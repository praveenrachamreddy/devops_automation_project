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

class ElasticsearchAgent(BaseAgent):
    """Agent specialized in analyzing logs stored in Elasticsearch."""

    def __init__(self):
        """Initialize the Elasticsearch agent with its specific name and description."""
        super().__init__(
            name="ElasticsearchAgent",
            description="A log analysis specialist that can analyze logs stored in Elasticsearch"
        )

    def get_system_prompt(self) -> str:
        """Return the system prompt/instructions for this agent."""
        return """
You are a specialist in analyzing logs stored in Elasticsearch. You have access to the following tools:

1. `test_connection`: Test the connection to Elasticsearch
2. `list_indices`: List all available Elasticsearch indices. Use this to discover what log data is available.
3. `get_mappings`: Get field mappings for a specific Elasticsearch index. Use this to understand the structure of log data.
4. `search`: Perform an Elasticsearch search with the provided query DSL. Use this to retrieve specific log entries.
5. `esql`: Perform an ES|QL query
6. `get_shards`: Get shard information for all or specific indices

When analyzing logs, follow these principles:
- First, use `test_connection` to verify Elasticsearch is accessible
- Then use `list_indices` to discover available log indices
- Use `get_mappings` to understand the structure of relevant indices
- Finally, use `search` or `esql` to retrieve and analyze the actual log data
- Always provide clear, actionable insights based on the log data
- Format your findings in an easy-to-read manner with clear explanations
- If you encounter errors, explain what might be causing them and suggest solutions
"""

    def create_agent(self) -> LlmAgent:
        """Create and return the configured Elasticsearch agent.
        
        This method creates an LlmAgent with MCP tools for handling
        Elasticsearch log analysis tasks.
        
        Returns:
            LlmAgent: Configured agent for handling Elasticsearch tasks
        """
        mcp_server_url = os.getenv("ELASTICSEARCH_MCP_SERVER_URL", "http://localhost:8081/mcp")
        logger.info(f"--- 🔧 Loading Elasticsearch MCP tools from MCP Server at {mcp_server_url}... ---")
        logger.info("--- 🤖 Creating ADK Elasticsearch Agent... ---")
        
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


# Create an instance of the Elasticsearch agent
elasticsearch_agent = ElasticsearchAgent()
