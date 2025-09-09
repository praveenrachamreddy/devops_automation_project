from google.adk.tools.tool_context import ToolContext

def log_agent_action(action: str, details: str, tool_context: ToolContext) -> dict:
    """Logs an agent action to the trace log in state.
    
    Args:
        action: The type of action being logged.
        details: Details about the action.
        
    Returns:
        dict: Status of the logging operation.
    """
    # Get existing log or initialize new one
    trace_log = tool_context.state.get("agent_trace_log", [])
    
    # Add new entry with timestamp
    import time
    trace_log.append({
        "timestamp": time.time(),
        "agent": tool_context.agent_name,
        "action": action,
        "details": details
    })
    
    # Update state with new log
    tool_context.state["agent_trace_log"] = trace_log
    
    return {
        "status": "success"
    }

# Add this tool to all agents in your system for comprehensive tracing


import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Set up session and runner
session_service = InMemorySessionService()
APP_NAME = "streaming_app"
USER_ID = "user_123"
SESSION_ID = "session_456"

session = session_service.create_session(
    app_name=APP_NAME, 
    user_id=USER_ID,
    session_id=SESSION_ID
)

runner = Runner(
    agent=streaming_agent,  # Assume this is defined
    app_name=APP_NAME,
    session_service=session_service
)

async def stream_response(query: str):
    """Streams the agent's response token by token."""
    content = types.Content(role='user', parts=[types.Part(text=query)])
    
    print(f"User: {query}")
    print("Agent: ", end="", flush=True)
    
    # Process events as they arrive
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content
    ):
        # For token-by-token streaming, look for ContentPartDelta events
        if hasattr(event, 'content_part_delta') and event.content_part_delta:
            delta = event.content_part_delta
            if delta.text:
                print(delta.text, end="", flush=True)
        
        # For final response
        if event.is_final_response():
            print()  # End line after response
            
    print("\n")  # Add space after complete response

# Run streaming interaction
async def main():
    queries = [
        "What's the weather in New York?",
        "How about London?",
        "Thanks for your help!"
    ]
    
    for query in queries:
        await stream_response(query)

# Run the async main function
asyncio.run(main())

