#!/usr/bin/env python3
"""
FastAPI server for Google ADK Multi-Agent System with SQLite session management.
This server provides WebSocket support for real-time communication with your DevOps orchestrator.
"""

import asyncio
import json
import sqlite3
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel
import google.genai.types as types
from google.genai.types import Content, FunctionCall


# ADK imports
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from google.adk.sessions.session import Session
from google.adk.sessions.session import Event


# Import your agent
from devops_agent_system.agent import agent as root_agent  # Your orchestrator agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class WebSocketResponse(BaseModel):
    type: str  # 'message', 'error', 'session_info', 'agent_thinking'
    content: str
    session_id: Optional[str] = None
    timestamp: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

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
        try:
            # Create database session service
            self.session_service = DatabaseSessionService(
                db_url=f"sqlite:///{DATABASE_PATH}"
            )
            
            # Create runner with your orchestrator agent
            # Based on the documentation, we might need to pass additional parameters
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
                    # "history": []  # Initialize empty history
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
                logger.info(f"Processing event: {type(event)} - {event}")
                
                if hasattr(event, 'content') and event.content:
                    if isinstance(event.content, Content):
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
    
    # Replace the get_session_history method with:
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
    try:
        await adk_manager.session_service.delete_session(
            app_name=adk_manager.app_name,
            user_id=user_id,
            session_id=session_id
        )
        return {"message": "Session deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")

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
    
    uvicorn.run(
        "main:app",  # Assumes this file is named main.py
        host="0.0.0.0",
        port=8000,
        reload=False,  # Set to False in production
        log_level="info"
    )