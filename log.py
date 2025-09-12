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


