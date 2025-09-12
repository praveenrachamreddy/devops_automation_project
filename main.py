#!/usr/bin/env python3
"""
FastAPI server for Google ADK Multi-Agent System with SQLite session management.
This server provides WebSocket support for real-time communication with your DevOps orchestrator.
"""

import asyncio
import base64
import json
import sqlite3
import uuid
import os
import sys
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List, AsyncGenerator
import logging
import collections.abc
from pathlib import Path

# Fix for Windows aiodns issue - set SelectorEventLoop before any other imports
if sys.platform == 'win32':
    # Set the event loop policy to use SelectorEventLoop on Windows
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    logger = logging.getLogger(__name__)
    if hasattr(logger, 'info'):  # Check if logger is initialized
        logger.info("Windows detected: Using SelectorEventLoop for aiodns compatibility")
    else:
        print("Windows detected: Using SelectorEventLoop for aiodns compatibility")

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger = logging.getLogger(__name__)
    logger.info("Environment variables loaded from .env file")
except ImportError:
    print("Warning: python-dotenv not installed. Install it with: pip install python-dotenv")
    print("Environment variables will only be loaded from system environment")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel
import google.genai.types as types
from google.genai.types import Content, Part

# ADK imports
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from google.adk.sessions.session import Session
from google.adk.sessions.session import Event

# =============================================================================
# STREAMING MODE ENUM
# =============================================================================

class StreamingMode(str, Enum):
    """Enumeration of supported streaming modes."""
    NONE = "none"
    SSE = "sse"  # Server-Sent Events
    BIDI = "bidi"  # Bidirectional streaming

# Import your agent
try:
    from devops_agent_system.agent import root_agent  # Your orchestrator agent
except ImportError:
    print("Warning: Could not import root agent. Please ensure devops_agent_system.agent exists.")
    root_agent = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# ENVIRONMENT VARIABLE SETUP
# =============================================================================

# Verify and set up Google API Key
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    logger.error("🔴 **Error: GOOGLE_API_KEY not found in environment variables.**")
    logger.error("Please check your .env file or set the environment variable directly.")
    logger.error("Current working directory: %s", os.getcwd())
    logger.error("Looking for .env file at: %s", os.path.join(os.getcwd(), '.env'))
else:
    # Ensure the API key is set in os.environ for ADK to use
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
    logger.info("✅ Google API Key loaded successfully (length: %d)", len(GOOGLE_API_KEY))

# Set VertexAI configuration
GOOGLE_GENAI_USE_VERTEXAI = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "False")
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = GOOGLE_GENAI_USE_VERTEXAI
logger.info("🔧 GOOGLE_GENAI_USE_VERTEXAI set to: %s", GOOGLE_GENAI_USE_VERTEXAI)

# =============================================================================
# DATABASE SETUP
# =============================================================================

DATABASE_PATH = "adk_sessions.db"

def init_database():
    """Initialize SQLite database with custom tables (ADK will create its own tables)."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create active connections table for WebSocket management (custom table)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS active_connections (
            session_id TEXT PRIMARY KEY,
            connection_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create session resumption tokens table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_resumption_tokens (
            token TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info("Custom database tables initialized successfully")

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: str = "default_user"

class SessionInfo(BaseModel):
    session_id: str
    user_id: str
    app_name: str
    created_at: str
    last_update_time: float

class ChatRequest(BaseModel):
    query: str
    user_id: Optional[str] = "default_user" 
    session_id: Optional[str] = None  # If None, a new one will be created/retrieved

class StreamingConfig(BaseModel):
    """Configuration for streaming behavior."""
    mode: StreamingMode = StreamingMode.BIDI
    buffer_size: int = 4096
    timeout: int = 30
    enable_partial_responses: bool = True

class WebSocketResponse(BaseModel):
    type: str  # 'message', 'error', 'session_info', 'agent_thinking', 'audio'
    content: str
    session_id: Optional[str] = None
    timestamp: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    mime_type: Optional[str] = None  # For audio data, e.g., 'audio/pcm'
    data: Optional[str] = None  # Base64 encoded audio data

# =============================================================================
# PRODUCTION CONFIGURATION
# HELPERS (Serializer and Parser)
# =============================================================================

# Instance identification for multiple instances
INSTANCE_ID = os.environ.get("INSTANCE_ID", str(uuid.uuid4()))
HOSTNAME = os.environ.get("HOSTNAME", "localhost")

def json_default_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, collections.abc.Set):
        return list(obj)
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def serialize_adk_event_for_streaming(event):
    """Serialize ADK events into proper streaming format similar to google-adk-demos"""
    event_data = {
        "event_type": event.__class__.__name__,
        "author": getattr(event, 'author', None),
        "is_final_response": event.is_final_response() if hasattr(event, 'is_final_response') else False,
        "content_text": None,
        "tool_calls": None,
        "tool_responses": None,
        "error_message": getattr(event, 'error_message', None),
        "timestamp": datetime.now().timestamp(),
        "audio_data": None,
        "mime_type": None
    }
    
    if hasattr(event, 'content') and event.content and hasattr(event.content, 'parts'):
        # Extract text parts
        text_parts = []
        tool_call_parts = []
        tool_response_parts = []
        audio_parts = []
        
        for part in event.content.parts:
            if hasattr(part, 'text') and part.text is not None:
                text_parts.append(part.text)
            elif hasattr(part, 'function_call') and part.function_call is not None:
                tool_call_parts.append({
                    "name": part.function_call.name,
                    "args": dict(part.function_call.args) if hasattr(part.function_call, 'args') else {}
                })
            elif hasattr(part, 'function_response') and part.function_response is not None:
                tool_response_parts.append({
                    "name": part.function_response.name,
                    "response": part.function_response.response
                })
            elif hasattr(part, 'inline_data') and part.inline_data is not None:
                # Handle audio data
                if hasattr(part.inline_data, 'mime_type') and part.inline_data.mime_type.startswith('audio/'):
                    if hasattr(part.inline_data, 'data'):
                        # Convert audio data to Base64 for JSON serialization
                        audio_data = part.inline_data.data
                        base64_audio = array_buffer_to_base64(audio_data)
                        audio_parts.append({
                            "mime_type": part.inline_data.mime_type,
                            "data": base64_audio,
                            "size": len(audio_data)
                        })
                        event_data["mime_type"] = part.inline_data.mime_type
                        event_data["audio_data"] = base64_audio
        
        if text_parts:
            event_data["content_text"] = " ".join(filter(None, text_parts))
        if tool_call_parts:
            event_data["tool_calls"] = tool_call_parts
        if tool_response_parts:
            event_data["tool_responses"] = tool_response_parts
        if audio_parts:
            event_data["audio_parts"] = audio_parts
    
    return event_data

def parse_adk_event(event):
    """Parse ADK events into structured format (legacy function for backward compatibility)"""
    parsed_details = []
    if not hasattr(event, "content") or not event.content or not hasattr(event.content, "parts"):
        return parsed_details
    for part in event.content.parts:
        detail = None
        if hasattr(part, "thought") and part.thought:
            detail = {"type": "Thought", "agent": event.author, "thought": part.thought}
        elif hasattr(part, "function_call") and part.function_call:
            detail = {"type": "ToolCall", "agent": event.author, "tool_name": part.function_call.name, "tool_input": dict(part.function_call.args)}
        elif hasattr(part, "function_response") and part.function_response:
            detail = {"type": "ToolOutput", "agent": event.author, "tool_name": part.function_response.name, "tool_output": part.function_response.response}
        elif hasattr(part, "text") and part.text:
            detail = {"type": "TextOutput", "agent": event.author, "text": part.text}
        if detail:
            parsed_details.append(detail)
    return parsed_details


def array_buffer_to_base64(buffer):
    """Convert an array buffer to Base64 string."""
    if isinstance(buffer, bytes):
        return base64.b64encode(buffer).decode("ascii")
    elif isinstance(buffer, bytearray):
        return base64.b64encode(bytes(buffer)).decode("ascii")
    else:
        raise TypeError("Buffer must be bytes or bytearray")

def base64_to_array_buffer(base64_string):
    """Convert a Base64 string to bytes."""
    return base64.b64decode(base64_string)

def extract_agent_and_tool_info(event):
    """Extract detailed agent and tool information from ADK events for better visualization"""
    info = {
        "event_type": None,
        "agent_name": None,
        "tool_name": None,
        "content": None,
        "is_transfer": False
    }
    
    # Check for agent transfer (sub-agent activation)
    if hasattr(event, 'author') and event.author:
        info["agent_name"] = event.author
    
    # Check for tool calls
    if hasattr(event, "content") and event.content and hasattr(event.content, "parts"):
        for part in event.content.parts:
            if hasattr(part, "function_call") and part.function_call:
                info["event_type"] = "tool_call"
                info["tool_name"] = part.function_call.name
                info["content"] = dict(part.function_call.args) if hasattr(part.function_call, 'args') else {}
                break
            elif hasattr(part, "function_response") and part.function_response:
                info["event_type"] = "tool_response"
                info["tool_name"] = part.function_response.name
                info["content"] = part.function_response.response
                break
            elif hasattr(part, "text") and part.text:
                # Check if this is an agent transfer message
                text_content = part.text.lower()
                if "transferring to" in text_content or "transfer to" in text_content:
                    info["event_type"] = "agent_transfer"
                    info["is_transfer"] = True
                    # Try to extract agent name from text
                    if ":" in part.text:
                        info["agent_name"] = part.text.split(":")[-1].strip()
                else:
                    info["event_type"] = "agent_response"
                    info["content"] = part.text
                break
    
    # If we haven't identified a specific event type, check for agent transfer in other ways
    if not info["event_type"] and hasattr(event, 'author') and event.author:
        if hasattr(event, 'content') and event.content:
            # This is likely an agent response
            info["event_type"] = "agent_response"
    
    return info

# =============================================================================
# BASE64 CONVERSION HELPERS
# =============================================================================

def array_buffer_to_base64(buffer):
    """Convert an array buffer to Base64 string."""
    if isinstance(buffer, bytes):
        return base64.b64encode(buffer).decode("ascii")
    elif isinstance(buffer, bytearray):
        return base64.b64encode(bytes(buffer)).decode("ascii")
    else:
        raise TypeError("Buffer must be bytes or bytearray")

def base64_to_array_buffer(base64_string):
    """Convert a Base64 string to bytes."""
    return base64.b64decode(base64_string)

# =============================================================================
# CONNECTION MANAGER
# =============================================================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_connections: Dict[str, str] = {}  # session_id -> connection_id
    
    async def connect(self, websocket: WebSocket, session_id: str, user_id: str):
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        self.session_connections[session_id] = connection_id
        
        # Store in database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO active_connections 
            (session_id, connection_id, user_id, connected_at, last_activity)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (session_id, connection_id, user_id))
        conn.commit()
        conn.close()
        
        logger.info(f"WebSocket connected: {connection_id} for session {session_id}")
        return connection_id
    
    def disconnect(self, connection_id: str, session_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        if session_id in self.session_connections:
            del self.session_connections[session_id]
            
        # Remove from database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM active_connections WHERE session_id = ?", (session_id,))
        conn.commit()
        conn.close()
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_message(self, session_id: str, response: WebSocketResponse):
        if session_id in self.session_connections:
            connection_id = self.session_connections[session_id]
            if connection_id in self.active_connections:
                websocket = self.active_connections[connection_id]
                try:
                    # Handle audio data differently if present
                    if response.mime_type == "audio/pcm" and response.data:
                        # For audio data, we can send it as binary or keep it as Base64 in JSON
                        # Let's send as JSON with Base64 data for compatibility
                        await websocket.send_text(response.model_dump_json())
                    else:
                        await websocket.send_text(response.model_dump_json())
                    
                    # Update last activity
                    conn = sqlite3.connect(DATABASE_PATH)
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE active_connections 
                        SET last_activity = CURRENT_TIMESTAMP 
                        WHERE session_id = ?
                    """, (session_id,))
                    conn.commit()
                    conn.close()
                    
                except Exception as e:
                    logger.error(f"Error sending message to {session_id}: {e}")
                    # Clean up dead connection
                    self.disconnect(connection_id, session_id)

# =============================================================================
# ADK INTEGRATION
# =============================================================================

class ADKManager:
    def __init__(self, streaming_config: Optional[StreamingConfig] = None):
        self.session_service = None
        self.runner = None
        self.app_name = "devops_orchestrator"
        self.streaming_config = streaming_config or StreamingConfig()
    
    async def initialize(self):
        """Initialize ADK components with database session service."""
        if not root_agent:
            logger.error("Root agent not available. ADK Manager initialization failed.")
            return
            
        try:
            # Create database session service
            self.session_service = DatabaseSessionService(
                db_url=f"sqlite:///{DATABASE_PATH}"
            )
            
            # Create runner with your orchestrator agent
            self.runner = Runner(
                agent=root_agent,
                session_service=self.session_service,
                app_name=self.app_name
            )
            
            logger.info("ADK Manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ADK Manager: {e}")
            raise
    
    async def get_or_create_session(self, user_id: str, session_id: Optional[str] = None) -> Session:
        """Get existing session or create a new one."""
        try:
            if session_id:
                # Try to get existing session
                try:
                    session = await self.session_service.get_session(
                        app_name=self.app_name,
                        user_id=user_id,
                        session_id=session_id
                    )
                    if session:
                        logger.info(f"Retrieved existing session: {session.id} for user: {user_id}")
                        # Ensure history exists in existing sessions
                        if "history" not in session.state:
                            session.state["history"] = []
                        return session
                    else:
                        logger.warning(f"Session {session_id} not found, creating new one")
                except Exception as e:
                    logger.warning(f"Session {session_id} not found or error retrieving it: {e}, creating new one")
            
            # Create new session
            session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id=user_id,
                state={
                    "initialized": True,
                    "created_at": datetime.now().isoformat()
                }
            )
            if session:
                logger.info(f"Created new session: {session.id} for user: {user_id}")
                return session
            else:
                logger.error("Failed to create session - returned None")
                raise Exception("Session creation failed - returned None")
            
        except Exception as e:
            logger.error(f"Error managing session: {e}")
            raise
    
    async def process_message(self, session_id: str, user_id: str, message: str, connection_manager: ConnectionManager) -> str:
        """Process user message through the ADK orchestrator."""
        if not self.runner:
            error_msg = "ADK Manager not properly initialized"
            logger.error(error_msg)
            return f"I apologize, but I encountered an error: {error_msg}"
            
        try:
            # Get session
            session = await self.get_or_create_session(user_id, session_id)
            
            # Check if session was successfully created/retrieved
            if not session:
                error_msg = "Failed to create or retrieve session"
                logger.error(error_msg)
                return f"I apologize, but I encountered an error: {error_msg}"
            
            # Send "thinking" indicator
            await connection_manager.send_message(
                session.id,
                WebSocketResponse(
                    type="agent_thinking",
                    content="Agent is processing your request...",
                    session_id=session.id,
                    timestamp=datetime.now().timestamp()
                )
            )
            
            # Process message through ADK runner
            final_response = ""
            function_calls_made = []
            
            async for event in self.runner.run_async(
                session_id=session.id,
                user_id=user_id,
                new_message=types.Content(role='user', parts=[types.Part(text=message)])
            ):
                logger.info(f"Processing event: {type(event)}")
                
                # Extract detailed agent and tool information
                event_info = extract_agent_and_tool_info(event)
                
                # Check for audio content in the event
                audio_data = None
                if hasattr(event, 'content') and event.content and hasattr(event.content, 'parts'):
                    for part in event.content.parts:
                        # Check for inline audio data
                        if hasattr(part, 'inline_data') and part.inline_data:
                            if hasattr(part.inline_data, 'mime_type') and part.inline_data.mime_type.startswith('audio/'):
                                if hasattr(part.inline_data, 'data'):
                                    audio_data = part.inline_data.data
                
                # Send appropriate WebSocket messages based on event type
                if audio_data:
                    # Convert audio data to Base64 for transmission
                    base64_audio = array_buffer_to_base64(audio_data)
                    
                    # Send audio data to client
                    await connection_manager.send_message(
                        session.id,
                        WebSocketResponse(
                            type="audio",
                            content=f"Audio response: {len(audio_data)} bytes",
                            session_id=session.id,
                            timestamp=datetime.now().timestamp(),
                            mime_type="audio/pcm",
                            data=base64_audio,
                            metadata={
                                "event_type": "audio_response",
                                "audio_size": len(audio_data)
                            }
                        )
                    )
                elif event_info["event_type"] == "agent_transfer":
                    await connection_manager.send_message(
                        session.id,
                        WebSocketResponse(
                            type="agent_transfer",
                            content=f"🔄 Transferring to {event_info['agent_name']}",
                            session_id=session.id,
                            timestamp=datetime.now().timestamp(),
                            metadata={
                                "agent_name": event_info['agent_name'],
                                "event_type": "agent_transfer"
                            }
                        )
                    )
                elif event_info["event_type"] == "tool_call":
                    await connection_manager.send_message(
                        session.id,
                        WebSocketResponse(
                            type="tool_call",
                            content=f"🔧 Using tool: {event_info['tool_name']}",
                            session_id=session.id,
                            timestamp=datetime.now().timestamp(),
                            metadata={
                                "tool_name": event_info['tool_name'],
                                "tool_args": event_info['content'],
                                "event_type": "tool_call"
                            }
                        )
                    )
                elif event_info["event_type"] == "tool_response":
                    await connection_manager.send_message(
                        session.id,
                        WebSocketResponse(
                            type="tool_response",
                            content=f"✅ Tool response: {str(event_info['content'])[:200]}{'...' if len(str(event_info['content'])) > 200 else ''}",
                            session_id=session.id,
                            timestamp=datetime.now().timestamp(),
                            metadata={
                                "tool_name": event_info['tool_name'],
                                "tool_response": event_info['content'],
                                "event_type": "tool_response"
                            }
                        )
                    )
                elif event_info["event_type"] == "agent_response":
                    await connection_manager.send_message(
                        session.id,
                        WebSocketResponse(
                            type="agent_response",
                        content=f"🤖 {event_info['agent_name'] or 'Agent'}: {event_info['content']}" if event_info['agent_name'] else event_info['content'],
                            session_id=session.id,
                            timestamp=datetime.now().timestamp(),
                            metadata={
                                "agent_name": event_info['agent_name'],
                                "event_type": "agent_response"
                            }
                        )
                    )
                
                # Also collect the final response text
                if hasattr(event, 'content') and event.content:
                    if isinstance(event.content, types.Content):
                        # Extract text and function calls from Content object's parts
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text is not None:
                                final_response += part.text
                            elif hasattr(part, 'function_call') and part.function_call:
                                # Handle function calls
                                func_call = part.function_call
                                function_calls_made.append({
                                    "name": func_call.name,
                                    "args": dict(func_call.args) if hasattr(func_call, 'args') else {}
                                })
                                final_response += f"\n[Used tool: {func_call.name}]"
                    else:
                        # Handle other content types
                        content_str = str(event.content)
                        if content_str and content_str.strip() and content_str != "None":
                            final_response += content_str
                elif hasattr(event, 'text') and event.text is not None:
                    # Direct text content
                    final_response += event.text
                elif isinstance(event, str) and event.strip():
                    final_response += event
            
            # Clean up the response and provide fallback if empty
            final_response = final_response.strip()
            if not final_response and function_calls_made:
                final_response = f"I used {len(function_calls_made)} tool(s) to process your request: " + ", ".join([fc["name"] for fc in function_calls_made])
            elif not final_response:
                final_response = "I processed your request. Please let me know if you need anything else."
                
            return final_response
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"I apologize, but I encountered an error: {str(e)}"
    
    async def process_message_stream(self, session_id: str, user_id: str, message: str):
        """Process user message through the ADK orchestrator with streaming response using proper SSE format."""
        if not self.runner or not self.session_service:
            error_msg = "ADK Manager not properly initialized"
            logger.error(error_msg)
            error_event_data = {"event_type": "ErrorEvent", "error_message": error_msg}
            yield f"data: {json.dumps(error_event_data, default=json_default_serializer)}\n\n"
            return
            
        try:
            # Get or create session
            session = await self.get_or_create_session(user_id, session_id)
            if not session:
                error_msg = "Failed to create or retrieve session"
                logger.error(error_msg)
                error_event_data = {"event_type": "ErrorEvent", "error_message": error_msg}
                yield f"data: {json.dumps(error_event_data, default=json_default_serializer)}\n\n"
                return
                
            actual_session_id = session.id
            logger.info(f"Processing message for session: {actual_session_id}")
            
            # Create content for the user message
            content = types.Content(role='user', parts=[types.Part(text=message)])
            
            # Process message through ADK runner and stream events
            try:
                async for event in self.runner.run_async(
                    session_id=actual_session_id,
                    user_id=user_id,
                    new_message=content
                ):
                    # Extract detailed agent and tool information
                    event_info = extract_agent_and_tool_info(event)
                    
                    # Serialize event using the new serialization function
                    event_data = serialize_adk_event_for_streaming(event)
                    
                    # Add our enhanced information to the event data
                    event_data["enhanced_info"] = event_info
                    
                    # Yield in proper SSE format - ADK events should have a .json() method
                    if hasattr(event, 'json'):
                        yield f"data: {event.json()}\n\n"
                    else:
                        yield f"data: {json.dumps(event_data, default=json_default_serializer)}\n\n"
                    
                    # Small sleep to allow other tasks
                    await asyncio.sleep(0.01)
                    
            except Exception as e:
                logger.error(f"Error during agent execution or event streaming: {e}", exc_info=True)
                error_event_data = {"event_type": "ErrorEvent", "error_message": str(e)}
                yield f"data: {json.dumps(error_event_data, default=json_default_serializer)}\n\n"
                
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            error_event_data = {"event_type": "ErrorEvent", "error_message": str(e)}
            yield f"data: {json.dumps(error_event_data, default=json_default_serializer)}\n\n"
    
    async def get_session_history(self, session_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        try:
            session = await self.session_service.get_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_id
            )
            
            if not session:
                logger.warning(f"Session {session_id} not found for user {user_id}")
                return []
            
            # Convert ADK events to simple format
            history = []
            for event in session.events:
                if hasattr(event, 'content') and event.content:
                    history.append({
                        "author": event.author,
                        "content": str(event.content),
                        "timestamp": event.timestamp if hasattr(event, 'timestamp') else None
                    })
            
            return history
        except Exception as e:
            logger.error(f"Error getting session history: {e}")
            return []

    async def create_resumption_token(self, session_id: str, user_id: str) -> str:
        """Create a resumption token for a session."""
        try:
            # Generate a unique token
            token = str(uuid.uuid4())
            
            # Calculate expiration time (24 hours from now)
            expires_at = datetime.now().timestamp() + (24 * 60 * 60)
            
            # Store in database
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO session_resumption_tokens 
                (token, session_id, user_id, expires_at)
                VALUES (?, ?, ?, ?)
            """, (token, session_id, user_id, datetime.fromtimestamp(expires_at)))
            conn.commit()
            conn.close()
            
            logger.info(f"Created resumption token for session {session_id}")
            return token
        except Exception as e:
            logger.error(f"Error creating resumption token: {e}")
            raise

    async def validate_resumption_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate a resumption token and return session info if valid."""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT session_id, user_id, expires_at 
                FROM session_resumption_tokens 
                WHERE token = ?
            """, (token,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                session_id, user_id, expires_at = row
                # Check if token is expired
                if datetime.fromtimestamp(expires_at) > datetime.now():
                    return {
                        "session_id": session_id,
                        "user_id": user_id,
                        "valid": True
                    }
                else:
                    # Token expired, clean it up
                    await self.invalidate_resumption_token(token)
                    return {"valid": False, "reason": "expired"}
            
            return {"valid": False, "reason": "not found"}
        except Exception as e:
            logger.error(f"Error validating resumption token: {e}")
            return {"valid": False, "reason": str(e)}

    async def invalidate_resumption_token(self, token: str):
        """Invalidate a resumption token."""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM session_resumption_tokens 
                WHERE token = ?
            """, (token,))
            conn.commit()
            conn.close()
            
            logger.info(f"Invalidated resumption token: {token}")
        except Exception as e:
            logger.error(f"Error invalidating resumption token: {e}")

    async def handle_audio_streaming(self, session_id: str, user_id: str, audio_data: bytes, connection_manager: ConnectionManager):
        """Handle audio streaming from client to agent."""
        try:
            # Convert audio data to Base64 for transmission
            base64_audio = base64.b64encode(audio_data).decode("ascii")
            
            # Send audio data to client as acknowledgment
            await connection_manager.send_message(
                session_id,
                WebSocketResponse(
                    type="audio_received",
                    content=f"Received audio data: {len(audio_data)} bytes",
                    session_id=session_id,
                    timestamp=datetime.now().timestamp(),
                    mime_type="audio/pcm",
                    data=base64_audio
                )
            )
            
            # Here you would typically process the audio data with the agent
            # For now, we'll just acknowledge receipt
            return f"Processed audio data: {len(audio_data)} bytes"
        except Exception as e:
            logger.error(f"Error handling audio streaming: {e}")
            return f"Error handling audio streaming: {str(e)}"

# =============================================================================
# FASTAPI APP SETUP
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_database()
    # Create streaming configuration
    streaming_config = StreamingConfig(
        mode=StreamingMode.BIDI,
        buffer_size=4096,
        timeout=30,
        enable_partial_responses=True
    )
    app.state.adk_manager = ADKManager(streaming_config=streaming_config)
    await app.state.adk_manager.initialize()
    app.state.connection_manager = ConnectionManager()
    logger.info("FastAPI server started with ADK integration")
    yield
    # Shutdown
    logger.info("FastAPI server shutting down")
    # Close all active connections
    if hasattr(app.state, 'connection_manager'):
        # Disconnect all active connections
        for connection_id in list(app.state.connection_manager.active_connections.keys()):
            # We don't have session_id here, so we'll just remove from active_connections
            if connection_id in app.state.connection_manager.active_connections:
                del app.state.connection_manager.active_connections[connection_id]
        logger.info("Closed all active WebSocket connections")

app = FastAPI(
    title="ADK Multi-Agent DevOps Orchestrator",
    description="FastAPI server with WebSocket support for Google ADK multi-agent system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# =============================================================================
# DEPENDENCY INJECTION
# =============================================================================

def get_adk_manager() -> ADKManager:
    return app.state.adk_manager

def get_connection_manager() -> ConnectionManager:
    return app.state.connection_manager

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def get_root():
    """Serve the chat interface from static file."""
    return FileResponse("static/index.html")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/health/detailed")
async def detailed_health_check(adk_manager: ADKManager = Depends(get_adk_manager)):
    """Detailed health check endpoint with component status."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "instance": {
            "id": INSTANCE_ID,
            "hostname": HOSTNAME,
            "port": os.environ.get("PORT", 8000)
        },
        "components": {
            "database": "unknown",
            "adk_manager": "unknown",
            "connection_manager": "unknown"
        }
    }
    
    # Check database connectivity
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        health_status["components"]["database"] = "healthy"
    except Exception as e:
        health_status["components"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check ADK manager
    if adk_manager.runner and adk_manager.session_service:
        health_status["components"]["adk_manager"] = "healthy"
    else:
        health_status["components"]["adk_manager"] = "unhealthy: not initialized"
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/health/liveness")
async def liveness_probe():
    """Liveness probe for Kubernetes."""
    return {"status": "alive", "timestamp": datetime.now().isoformat()}

@app.get("/health/readiness")
async def readiness_probe(adk_manager: ADKManager = Depends(get_adk_manager)):
    """Readiness probe for Kubernetes."""
    if adk_manager.runner and adk_manager.session_service:
        return {"status": "ready", "timestamp": datetime.now().isoformat()}
    else:
        raise HTTPException(status_code=503, detail="Service not ready")

@app.get("/health/loadbalancer")
async def load_balancer_health_check(connection_manager: ConnectionManager = Depends(get_connection_manager)):
    """Health check endpoint specifically for load balancers."""
    # Get active connections count
    active_connections = len(connection_manager.active_connections)
    
    # Check if we're at capacity (assuming a max of 1000 connections per instance)
    max_connections = int(os.environ.get("MAX_CONNECTIONS", 1000))
    capacity_percentage = (active_connections / max_connections) * 100 if max_connections > 0 else 0
    
    # Determine status based on capacity
    if capacity_percentage > 90:
        status = "unhealthy"  # Over 90% capacity
    elif capacity_percentage > 75:
        status = "degraded"   # 75-90% capacity
    else:
        status = "healthy"    # Under 75% capacity
    
    return {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "instance": {
            "id": INSTANCE_ID,
            "hostname": HOSTNAME
        },
        "load": {
            "active_connections": active_connections,
            "max_connections": max_connections,
            "capacity_percentage": round(capacity_percentage, 2)
        }
    }

@app.get("/metrics")
async def get_metrics(connection_manager: ConnectionManager = Depends(get_connection_manager)):
    """Get application metrics."""
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "instance": {
            "id": INSTANCE_ID,
            "hostname": HOSTNAME
        },
        "connections": {
            "active_connections": len(connection_manager.active_connections),
            "active_sessions": len(connection_manager.session_connections)
        },
        "system": {
            "platform": sys.platform,
            "python_version": sys.version
        },
        "load_balancing": {
            "max_connections": int(os.environ.get("MAX_CONNECTIONS", 1000)),
            "weight": int(os.environ.get("INSTANCE_WEIGHT", 100))  # For load balancer weighting
        }
    }
    
    # Calculate capacity percentage
    max_connections = metrics["load_balancing"]["max_connections"]
    active_connections = metrics["connections"]["active_connections"]
    capacity_percentage = (active_connections / max_connections) * 100 if max_connections > 0 else 0
    metrics["load_balancing"]["capacity_percentage"] = round(capacity_percentage, 2)
    
    # Add database metrics
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM active_connections")
        active_db_connections = cursor.fetchone()[0]
        metrics["database"] = {
            "active_connections": active_db_connections
        }
        conn.close()
    except Exception as e:
        metrics["database"] = {
            "error": str(e)
        }
    
    return metrics

@app.get("/sessions/{user_id}")
async def list_user_sessions(user_id: str, adk_manager: ADKManager = Depends(get_adk_manager)):
    """List all sessions for a user."""
    if not adk_manager.session_service:
        raise HTTPException(status_code=500, detail="Session service not initialized")
        
    try:
        # Use ADK session service to list sessions
        sessions = await adk_manager.session_service.list_sessions(
            app_name=adk_manager.app_name,
            user_id=user_id
        )
        
        session_list = []
        for session in sessions:
            session_list.append({
                "session_id": session.id,
                "app_name": session.app_name,
                "user_id": session.user_id,
                "state": session.state,
                "last_update_time": session.last_update_time.timestamp() if hasattr(session.last_update_time, 'timestamp') else session.last_update_time
            })
        
        return {"sessions": session_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")

@app.get("/sessions/{user_id}/{session_id}/history")
async def get_session_history(
    user_id: str, 
    session_id: str, 
    adk_manager: ADKManager = Depends(get_adk_manager)
):
    """Get conversation history for a specific session."""
    try:
        history = await adk_manager.get_session_history(session_id, user_id)
        return {"session_id": session_id, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting session history: {str(e)}")

@app.delete("/sessions/{user_id}/{session_id}")
async def delete_session(
    user_id: str, 
    session_id: str, 
    adk_manager: ADKManager = Depends(get_adk_manager)
):
    """Delete a specific session."""
    if not adk_manager.session_service:
        raise HTTPException(status_code=500, detail="Session service not initialized")
        
    try:
        await adk_manager.session_service.delete_session(
            app_name=adk_manager.app_name,
            user_id=user_id,
            session_id=session_id
        )
        return {"message": "Session deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")

@app.post("/sessions/{user_id}/{session_id}/resume")
async def create_session_resumption_token(
    user_id: str,
    session_id: str,
    adk_manager: ADKManager = Depends(get_adk_manager)
):
    """Create a resumption token for a session."""
    try:
        token = await adk_manager.create_resumption_token(session_id, user_id)
        return {
            "token": token,
            "session_id": session_id,
            "expires_in": 24 * 60 * 60  # 24 hours in seconds
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating resumption token: {str(e)}")

@app.post("/sessions/resume")
async def resume_session(
    token: str,
    adk_manager: ADKManager = Depends(get_adk_manager)
):
    """Resume a session using a resumption token."""
    try:
        validation_result = await adk_manager.validate_resumption_token(token)
        if validation_result.get("valid"):
            # Token is valid, return session info
            session_id = validation_result["session_id"]
            user_id = validation_result["user_id"]
            
            # Get session history
            history = await adk_manager.get_session_history(session_id, user_id)
            
            return {
                "session_id": session_id,
                "user_id": user_id,
                "history": history,
                "resumed": True
            }
        else:
            raise HTTPException(status_code=400, detail=f"Invalid resumption token: {validation_result.get('reason')}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resuming session: {str(e)}")

@app.post("/chat/stream")
async def chat_stream(
    request: ChatMessage,
    adk_manager: ADKManager = Depends(get_adk_manager)
):
    """Streaming chat endpoint for real-time agent responses."""
    return StreamingResponse(
        adk_manager.process_message_stream(
            session_id=request.session_id,
            user_id=request.user_id,
            message=request.message
        ),
        media_type="text/event-stream"
    )

@app.post("/chat_sse")
async def chat_with_agent_sse(
    chat_request: ChatRequest,
    adk_manager: ADKManager = Depends(get_adk_manager)
):
    """Server-Sent Events endpoint for streaming agent responses with proper ADK event handling."""
    user_id = chat_request.user_id
    session_id = chat_request.session_id if chat_request.session_id else str(uuid.uuid4())
    
    logger.info(f"Received request for /chat_sse: user_id='{user_id}', session_id='{session_id}'")
    
    async def event_stream_generator() -> AsyncGenerator[str, None]:
        """Generates Server-Sent Events from ADK runner."""
        try:
            # Get or create session
            session = await adk_manager.get_or_create_session(user_id, session_id)
            if not session:
                error_event_data = {"event_type": "ErrorEvent", "error_message": "Failed to create or retrieve session"}
                yield f"data: {json.dumps(error_event_data)}\n\n"
                return
                
            actual_session_id = session.id
            content = types.Content(role='user', parts=[types.Part(text=chat_request.query)])
            
            logger.info(f"Running agent for user_id='{user_id}', session_id='{actual_session_id}', query='{chat_request.query}'")
            
            async for event in adk_manager.runner.run_async(
                user_id=user_id, 
                session_id=actual_session_id, 
                new_message=content
            ):
                # Serialize the event using our improved serialization function
                event_data = serialize_adk_event_for_streaming(event)
                
                # Try to use ADK's native json() method if available, otherwise use our serialization
                if hasattr(event, 'json'):
                    yield f"data: {event.json()}\n\n"
                else:
                    yield f"data: {json.dumps(event_data, default=json_default_serializer)}\n\n"
                
                await asyncio.sleep(0.01)  # Small sleep to allow other tasks
                
        except Exception as e:
            logger.error(f"Error during agent execution or event streaming: {e}", exc_info=True)
            error_event_data = {"event_type": "ErrorEvent", "error_message": str(e)}
            yield f"data: {json.dumps(error_event_data)}\n\n"
    
    return StreamingResponse(
        event_stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

# =============================================================================
# WEBSOCKET ENDPOINT
# =============================================================================

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    session_id: str, 
    user_id: str = "default_user",
    is_audio: str = "false",  # Query parameter to indicate audio mode
    streaming_mode: str = "bidi",  # Query parameter for streaming mode
    resume_token: Optional[str] = None,  # Query parameter for session resumption
    adk_manager: ADKManager = Depends(get_adk_manager),
    connection_manager: ConnectionManager = Depends(get_connection_manager)
):
    """WebSocket endpoint for real-time chat with the ADK agent."""
    # Handle session resumption if token is provided
    if resume_token:
        try:
            validation_result = await adk_manager.validate_resumption_token(resume_token)
            if validation_result.get("valid"):
                # Use the session from the token
                session_id = validation_result["session_id"]
                user_id = validation_result["user_id"]
                # Invalidate the token as it's now used
                await adk_manager.invalidate_resumption_token(resume_token)
            else:
                await websocket.accept()
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": f"Invalid resumption token: {validation_result.get('reason')}",
                    "session_id": session_id,
                    "timestamp": datetime.now().timestamp()
                }))
                await websocket.close()
                return
        except Exception as e:
            await websocket.accept()
            await websocket.send_text(json.dumps({
                "type": "error",
                "content": f"Error validating resumption token: {str(e)}",
                "session_id": session_id,
                "timestamp": datetime.now().timestamp()
            }))
            await websocket.close()
            return
    
    # Get or create session to ensure we have a valid session ID
    try:
        session = await adk_manager.get_or_create_session(user_id, session_id)
        if not session:
            await websocket.accept()
            await websocket.send_text(json.dumps({
                "type": "error",
                "content": "Failed to create or retrieve session",
                "session_id": session_id,
                "timestamp": datetime.now().timestamp()
            }))
            await websocket.close()
            return
        # Use the actual session ID from the created/retrieved session
        actual_session_id = session.id
    except Exception as e:
        await websocket.accept()
        await websocket.send_text(json.dumps({
            "type": "error",
            "content": f"Session error: {str(e)}",
            "session_id": session_id,
            "timestamp": datetime.now().timestamp()
        }))
        await websocket.close()
        return
    
    connection_id = await connection_manager.connect(websocket, actual_session_id, user_id)
    
    # Send session info
    await connection_manager.send_message(
        actual_session_id,
        WebSocketResponse(
            type="session_info",
            content=f"Connected to session {actual_session_id}",
            session_id=actual_session_id,
            timestamp=datetime.now().timestamp(),
            metadata={"user_id": user_id, "connection_id": connection_id, "is_audio": is_audio, "streaming_mode": streaming_mode}
        )
    )
    
    # If this is a resumed session, send the history
    if resume_token:
        try:
            history = await adk_manager.get_session_history(actual_session_id, user_id)
            if history:
                await connection_manager.send_message(
                    actual_session_id,
                    WebSocketResponse(
                        type="session_history",
                        content=f"Session resumed with {len(history)} previous messages",
                        session_id=actual_session_id,
                        timestamp=datetime.now().timestamp(),
                        metadata={"history": history, "resumed": True}
                    )
                )
        except Exception as e:
            logger.error(f"Error sending session history: {e}")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive()
            
            # Handle both text and binary data
            if "text" in data:
                message_data = json.loads(data["text"])
                user_message = message_data.get("message", "").strip()
                mime_type = message_data.get("mime_type", "text/plain")
                
                # Handle audio data
                if mime_type == "audio/pcm" and "data" in message_data:
                    # Process audio data (Base64 encoded)
                    audio_data = message_data.get("data")
                    logger.info(f"Processing audio data from {user_id} in session {actual_session_id}: {len(audio_data)} bytes")
                    
                    # Send audio acknowledgment
                    await connection_manager.send_message(
                        actual_session_id,
                        WebSocketResponse(
                            type="audio_received",
                            content=f"Received audio data: {len(audio_data)} bytes",
                            session_id=actual_session_id,
                            timestamp=datetime.now().timestamp(),
                            mime_type="audio/pcm",
                            data=audio_data
                        )
                    )
                elif user_message:
                    logger.info(f"Processing message from {user_id} in session {actual_session_id}: {user_message[:50]}...")
                    
                    # Process through ADK based on streaming mode
                    if streaming_mode == "bidi":
                        # Use bidirectional streaming (existing implementation)
                        agent_response = await adk_manager.process_message(
                            actual_session_id, user_id, user_message, connection_manager
                        )
                        
                        # Send agent response
                        await connection_manager.send_message(
                            actual_session_id,
                            WebSocketResponse(
                                type="message",
                                content=agent_response,
                                session_id=actual_session_id,
                                timestamp=datetime.now().timestamp(),
                                metadata={"user_message": user_message}
                            )
                        )
                    elif streaming_mode == "sse":
                        # Use SSE-like streaming
                        # We'll stream the response as it comes in
                        pass  # Implementation would go here
                    else:
                        # No streaming (regular request-response)
                        agent_response = await adk_manager.process_message(
                            actual_session_id, user_id, user_message, connection_manager
                        )
                        
                        # Send agent response
                        await connection_manager.send_message(
                            actual_session_id,
                            WebSocketResponse(
                                type="message",
                                content=agent_response,
                                session_id=actual_session_id,
                                timestamp=datetime.now().timestamp(),
                                metadata={"user_message": user_message}
                            )
                        )
            elif "bytes" in data:
                # Handle binary data directly
                binary_data = data["bytes"]
                logger.info(f"Processing binary data from {user_id} in session {actual_session_id}: {len(binary_data)} bytes")
                
                # Convert binary data to Base64 for transmission
                base64_data = base64.b64encode(binary_data).decode("ascii")
                
                # Send audio data to agent
                await connection_manager.send_message(
                    actual_session_id,
                    WebSocketResponse(
                        type="audio_received",
                        content=f"Received binary audio data: {len(binary_data)} bytes",
                        session_id=actual_session_id,
                        timestamp=datetime.now().timestamp(),
                        mime_type="audio/pcm",
                        data=base64_data
                    )
                )
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {actual_session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {actual_session_id}: {e}")
        try:
            await connection_manager.send_message(
                actual_session_id,
                WebSocketResponse(
                    type="error",
                    content=f"An error occurred: {str(e)}",
                    session_id=actual_session_id,
                    timestamp=datetime.now().timestamp()
                )
            )
        except:
            pass
    finally:
        connection_manager.disconnect(connection_id, actual_session_id)

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Additional Windows-specific fixes for event loop
    if sys.platform == 'win32':
        # Ensure we're using the correct event loop policy
        if not isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsSelectorEventLoopPolicy):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            print("🔧 Windows: Set SelectorEventLoop policy for aiodns compatibility")
    
    # Get configuration from environment variables
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    reload = os.environ.get("RELOAD", "false").lower() == "true"
    log_level = os.environ.get("LOG_LEVEL", "info")
    max_connections = int(os.environ.get("MAX_CONNECTIONS", 1000))
    instance_weight = int(os.environ.get("INSTANCE_WEIGHT", 100))
    
    print("🚀 Starting ADK Multi-Agent DevOps Orchestrator Server...")
    print(f"📁 Database: {DATABASE_PATH}")
    print(f"🌐 Web interface: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
    print(f"🔌 WebSocket endpoint: ws://{host if host != '0.0.0.0' else 'localhost'}:{port}/ws/{{session_id}}")
    print(f"📡 Streaming endpoint: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/chat/stream")
    print(f"📡 New SSE endpoint: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/chat_sse")
    print(f"📊 Metrics endpoint: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/metrics")
    print(f"🏥 Health check endpoints:")
    print(f"   - Basic: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/health")
    print(f"   - Detailed: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/health/detailed")
    print(f"   - Liveness: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/health/liveness")
    print(f"   - Readiness: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/health/readiness")
    print(f"   - Load Balancer: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/health/loadbalancer")
    print(f"🔢 Instance ID: {INSTANCE_ID}")
    print(f"🏠 Hostname: {HOSTNAME}")
    print(f"⚖️  Instance weight: {instance_weight}")
    print(f"🔗 Max connections: {max_connections}")
    
    # Check environment variables before starting
    if not os.environ.get("GOOGLE_API_KEY"):
        print("⚠️  WARNING: GOOGLE_API_KEY not found in environment variables!")
        print("   Please check your .env file or set the environment variable directly.")
    
    try:
        uvicorn.run(
            "main:app",  # Assumes this file is named main.py
            host=host,
            port=port,
            reload=reload,  # Set to False in production
            log_level=log_level,
            loop="asyncio"  # Explicitly use asyncio loop
        )
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        if "aiodns" in str(e) and sys.platform == 'win32':
            print("🔧 Windows aiodns issue detected. Trying alternative approach...")
            # Try with different event loop configuration
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                uvicorn.run(
                    "main:app",
                    host=host,
                    port=port,
                    reload=reload,
                    log_level=log_level
                )
            except Exception as e2:
                print(f"❌ Alternative approach also failed: {e2}")
                print("Please try installing/updating aiodns: pip install --upgrade aiodns")
