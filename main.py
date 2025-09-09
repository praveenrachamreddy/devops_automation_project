#!/usr/bin/env python3
"""
FastAPI server for Google ADK Multi-Agent System with SQLite session management.
This server provides WebSocket support for real-time communication with your DevOps orchestrator.
"""

import asyncio
import json
import sqlite3
import uuid
import os
from datetime import datetime
from typing import Optional, Dict, Any, List, AsyncGenerator
import logging
import collections.abc
from pathlib import Path

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
from fastapi.responses import HTMLResponse, StreamingResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel
import google.genai.types as types
from google.genai.types import Content, Part

# ADK imports
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from google.adk.sessions.session import Session
from google.adk.sessions.session import Event

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

class WebSocketResponse(BaseModel):
    type: str  # 'message', 'error', 'session_info', 'agent_thinking'
    content: str
    session_id: Optional[str] = None
    timestamp: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

# =============================================================================
# HELPERS (Serializer and Parser)
# =============================================================================

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
        "timestamp": datetime.now().timestamp()
    }
    
    if hasattr(event, 'content') and event.content and hasattr(event.content, 'parts'):
        # Extract text parts
        text_parts = []
        tool_call_parts = []
        tool_response_parts = []
        
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
        
        if text_parts:
            event_data["content_text"] = " ".join(filter(None, text_parts))
        if tool_call_parts:
            event_data["tool_calls"] = tool_call_parts
        if tool_response_parts:
            event_data["tool_responses"] = tool_response_parts
    
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
    def __init__(self):
        self.session_service = None
        self.runner = None
        self.app_name = "devops_orchestrator"
    
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
                    # Serialize event using the new serialization function
                    event_data = serialize_adk_event_for_streaming(event)
                    
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

# =============================================================================
# FASTAPI APP SETUP
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_database()
    app.state.adk_manager = ADKManager()
    await app.state.adk_manager.initialize()
    app.state.connection_manager = ConnectionManager()
    logger.info("FastAPI server started with ADK integration")
    yield
    # Shutdown
    logger.info("FastAPI server shutting down")

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
    """Serve a simple chat interface."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ADK Multi-Agent Chat</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .chat-container { border: 1px solid #ddd; height: 400px; overflow-y: scroll; padding: 10px; margin: 20px 0; background: #fafafa; border-radius: 4px; }
            .message { margin: 10px 0; padding: 8px 12px; border-radius: 6px; }
            .user-message { background: #007bff; color: white; margin-left: 20%; }
            .agent-message { background: #e9ecef; margin-right: 20%; }
            .system-message { background: #fff3cd; color: #856404; font-style: italic; }
            .input-container { display: flex; gap: 10px; }
            .input-container input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
            .input-container button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
            .input-container button:hover { background: #0056b3; }
            .status { padding: 10px; margin: 10px 0; border-radius: 4px; background: #d1ecf1; border-left: 4px solid #bee5eb; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 ADK Multi-Agent DevOps Orchestrator</h1>
            <div class="status" id="status">Connecting...</div>
            <div class="chat-container" id="chatContainer"></div>
            <div class="input-container">
                <input type="text" id="messageInput" placeholder="Type your DevOps question or command..." maxlength="1000">
                <button onclick="sendMessage()">Send</button>
            </div>
            <p><small>Session ID: <span id="sessionId">Generating...</span></small></p>
        </div>

        <script>
            let ws = null;
            let sessionId = generateSessionId();
            const userId = 'web_user_' + Math.random().toString(36).substr(2, 9);
            
            document.getElementById('sessionId').textContent = sessionId;
            
            function generateSessionId() {
                return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            }
            
            function connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws/${sessionId}?user_id=${userId}`;
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function() {
                    document.getElementById('status').textContent = '✅ Connected to ADK Multi-Agent System';
                    document.getElementById('status').style.background = '#d4edda';
                    document.getElementById('status').style.borderColor = '#c3e6cb';
                };
                
                ws.onmessage = function(event) {
                    const response = JSON.parse(event.data);
                    handleMessage(response);
                };
                
                ws.onclose = function() {
                    document.getElementById('status').textContent = '❌ Connection lost. Refresh to reconnect.';
                    document.getElementById('status').style.background = '#f8d7da';
                    document.getElementById('status').style.borderColor = '#f5c6cb';
                };
                
                ws.onerror = function(error) {
                    console.error('WebSocket error:', error);
                    document.getElementById('status').textContent = '❌ Connection error';
                };
            }
            
            function handleMessage(response) {
                const chatContainer = document.getElementById('chatContainer');
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message';
                
                if (response.type === 'message') {
                    messageDiv.className += ' agent-message';
                    messageDiv.innerHTML = `<strong>🤖 DevOps Agent:</strong><br>${response.content.replace(/\\n/g, '<br>')}`;
                } else if (response.type === 'agent_thinking') {
                    messageDiv.className += ' system-message';
                    messageDiv.innerHTML = `💭 ${response.content}`;
                    messageDiv.id = 'thinking-indicator';
                } else if (response.type === 'error') {
                    messageDiv.className += ' system-message';
                    messageDiv.style.background = '#f8d7da';
                    messageDiv.innerHTML = `❌ Error: ${response.content}`;
                }
                
                chatContainer.appendChild(messageDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
                
                // Remove thinking indicator when we get the actual response
                if (response.type === 'message') {
                    const thinkingIndicator = document.getElementById('thinking-indicator');
                    if (thinkingIndicator) {
                        thinkingIndicator.remove();
                    }
                }
            }
            
            function addUserMessage(message) {
                const chatContainer = document.getElementById('chatContainer');
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message user-message';
                messageDiv.innerHTML = `<strong>👤 You:</strong><br>${message.replace(/\\n/g, '<br>')}`;
                chatContainer.appendChild(messageDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
            
            function sendMessage() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                
                if (message && ws && ws.readyState === WebSocket.OPEN) {
                    addUserMessage(message);
                    ws.send(JSON.stringify({
                        message: message,
                        session_id: sessionId,
                        user_id: userId
                    }));
                    input.value = '';
                }
            }
            
            // Event listeners
            document.getElementById('messageInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
            
            // Connect on page load
            connectWebSocket();
            
            // Add welcome message
            setTimeout(() => {
                const chatContainer = document.getElementById('chatContainer');
                const welcomeDiv = document.createElement('div');
                welcomeDiv.className = 'message system-message';
                welcomeDiv.innerHTML = `🚀 Welcome to the ADK Multi-Agent DevOps Orchestrator!<br>
                I can help you with:<br>
                • Web searches and research<br>
                • Code analysis and development<br>
                • Elasticsearch operations<br>
                • Kubernetes management<br>
                • Infrastructure automation<br>
                • CI/CD pipelines<br>
                • System monitoring<br>
                • And much more!<br><br>
                Ask me anything about your DevOps needs!`;
                chatContainer.appendChild(welcomeDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }, 500);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

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
    adk_manager: ADKManager = Depends(get_adk_manager),
    connection_manager: ConnectionManager = Depends(get_connection_manager)
):
    """WebSocket endpoint for real-time chat with the ADK agent."""
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
            metadata={"user_id": user_id, "connection_id": connection_id}
        )
    )
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            user_message = message_data.get("message", "").strip()
            
            if user_message:
                logger.info(f"Processing message from {user_id} in session {actual_session_id}: {user_message[:50]}...")
                
                # Process through ADK
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
    
    print("🚀 Starting ADK Multi-Agent DevOps Orchestrator Server...")
    print(f"📁 Database: {DATABASE_PATH}")
    print(f"🌐 Web interface: http://localhost:8000")
    print(f"🔌 WebSocket endpoint: ws://localhost:8000/ws/{{session_id}}")
    print(f"📡 Streaming endpoint: http://localhost:8000/chat/stream")
    
    uvicorn.run(
        "main:app",  # Assumes this file is named main.py
        host="0.0.0.0",
        port=8000,
        reload=False,  # Set to False in production
        log_level="info"
    )