# DevOps Automation Project - FastAPI Server

This project provides a FastAPI-based web server for the Google ADK multi-agent system, enabling real-time communication with DevOps automation agents through WebSockets and streaming HTTP endpoints.

## Features

- FastAPI web server with WebSocket support
- Google ADK integration for multi-agent orchestration
- Real-time communication with agents
- Session management with SQLite database
- Built-in web interface for testing
- REST API endpoints for session management
- Streaming HTTP endpoint for real-time agent responses

## Prerequisites

1. Python 3.8 or higher
2. Google ADK installed
3. API keys for Google Generative AI and other services as needed

## Setup

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```bash
   export GOOGLE_API_KEY="your-google-api-key"
   ```

3. Ensure your `config.yaml` is properly configured with the necessary settings for your DevOps tools.

## Running the Server

To start the FastAPI server:

```bash
python main.py
```

The server will start on `http://localhost:8000` with the following endpoints:

- Web interface: http://localhost:8000
- WebSocket endpoint: ws://localhost:8000/ws/{session_id}
- Health check: http://localhost:8000/health
- Session management: http://localhost:8000/sessions/{user_id}
- Streaming chat: http://localhost:8000/chat/stream

## Project Structure

```
devops_automation_project/
├── main.py                 # FastAPI server implementation
├── config.yaml             # Configuration file
├── devops_agent_system/    # Agent implementations
│   ├── agent.py            # Main orchestrator agent
│   ├── agents/             # Individual agent implementations
│   │   ├── base_agent.py   # Base agent class
│   │   └── sub_agents/     # Specialized agents
│   └── tools/              # Custom tools
└── requirements.txt        # Python dependencies
```

## Architecture

The FastAPI server integrates with the Google ADK to provide a web interface for the DevOps automation agents. The main components are:

1. **ADKManager**: Handles initialization and management of ADK components
2. **ConnectionManager**: Manages WebSocket connections and sessions
3. **DatabaseSessionService**: Stores session data in SQLite
4. **Root Agent**: The main orchestrator that delegates tasks to specialized agents

## API Endpoints

### WebSocket Endpoint
- `GET /ws/{session_id}?user_id={user_id}`: Establishes a WebSocket connection for real-time communication

### REST Endpoints
- `GET /`: Returns the web interface
- `GET /health`: Health check endpoint
- `GET /sessions/{user_id}`: Lists all sessions for a user
- `GET /sessions/{user_id}/{session_id}/history`: Retrieves conversation history for a session
- `DELETE /sessions/{user_id}/{session_id}`: Deletes a specific session
- `POST /chat/stream`: Streaming HTTP endpoint for real-time agent responses

### Streaming Endpoint
The `/chat/stream` endpoint provides server-sent events (SSE) for real-time agent responses. It's particularly useful for:
- Tracking agent thoughts and decision-making process
- Monitoring tool calls and their outputs
- Observing agent handoffs in multi-agent scenarios

Example request:
```json
{
  "message": "Analyze logs for errors",
  "user_id": "user123",
  "session_id": "session456"
}
```

The response will be a stream of events in the following format:
```
data: {"type": "Thought", "agent": "ElasticsearchAgent", "thought": "I need to search for error logs..."}
data: {"type": "ToolCall", "agent": "ElasticsearchAgent", "tool_name": "search", "tool_input": {"query": "error"}}
data: {"type": "ToolOutput", "agent": "ElasticsearchAgent", "tool_name": "search", "tool_output": {"results": [...]}}
data: {"type": "TextOutput", "agent": "ElasticsearchAgent", "text": "I found several error logs..."}
```

## Web Interface

The web interface provides a simple chat interface for interacting with the DevOps agents. It includes:

- Real-time messaging with the agents
- Session management
- Connection status indicators
- Message history display

## Extending the System

To add new agents or modify existing ones:

1. Create a new agent in `devops_agent_system/agents/sub_agents/`
2. Register the agent in `devops_agent_system/agent.py` in the `AGENT_REGISTRY`
3. Update the configuration in `config.yaml` if needed
4. Restart the server

## Troubleshooting

If you encounter issues:

1. Check that all required environment variables are set
2. Verify that the `config.yaml` file is properly configured
3. Ensure all dependencies are installed
4. Check the server logs for error messages

## Testing Streaming

To test the streaming endpoint, you can use the provided test script:

```bash
python test_streaming.py
```

This script will demonstrate how to use the streaming API with both single requests and multi-turn conversations.