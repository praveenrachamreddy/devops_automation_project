import logging
import os
import sys
import os

# Add the parent directory to the path so we can import base_agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams

# Import the base agent
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

load_dotenv()

class SimpleMCPAgent(BaseAgent):
    """Agent specialized in currency conversions using MCP tools."""

    def __init__(self):
        """Initialize the simple MCP agent with its specific name and description."""
        super().__init__(
            name="SimpleMCPAgent",
            description="A currency conversion specialist that uses external MCP tools."
        )

    def get_system_prompt(self) -> str:
        """Return the system prompt/instructions for this agent."""
        return (
            "You are a specialized assistant for currency conversions. "
            "Your sole purpose is to use the 'get_exchange_rate' tool to answer questions about currency exchange rates. "
            "If the user asks about anything other than currency conversion or exchange rates, "
            "politely state that you cannot help with that topic and can only assist with currency-related queries. "
            "Do not attempt to answer unrelated questions or use tools for other purposes."
            "If the user asks for a calculation that doesn't require the exchange rate tool, you can do simple math directly."
        )

    def create_agent(self) -> LlmAgent:
        """Create and return the configured simple MCP agent.
        
        This method creates an LlmAgent with MCP tools for handling
        currency conversion tasks.
        
        Returns:
            LlmAgent: Configured agent for handling currency conversion tasks
        """
        mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8080/mcp")
        logger.info(f"--- 🔧 Loading MCP tools from MCP Server at {mcp_server_url}... ---")
        logger.info("--- 🤖 Creating ADK Currency Agent... ---")
        
        return LlmAgent(
            model=self.get_default_model(),
            name=self.name,
            instruction=self.get_system_prompt(),
            tools=[
                MCPToolset(
                    connection_params=StreamableHTTPConnectionParams(
                        url=mcp_server_url
                    )
                )
            ],
        )


# Create an instance of the simple MCP agent
simple_mcp_agent = SimpleMCPAgent()