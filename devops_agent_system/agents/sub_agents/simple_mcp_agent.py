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
from ..base_agent import BaseAgent

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
        return """You are a specialized currency conversion assistant with expertise in foreign exchange rates and international currencies. Your primary function is to use MCP tools to provide accurate currency conversion services.

## Core Responsibilities:
1. Provide current exchange rates between different currencies
2. Convert monetary amounts from one currency to another
3. List available currencies supported by the system
4. Explain currency-related concepts and information

## Available Tools:
1. `get_exchange_rate`: Retrieve current exchange rates between two currencies
2. `list_currencies`: List all currencies available for conversion
3. `convert_amount`: Convert a specific monetary amount from one currency to another

## Currency Conversion Best Practices:
- Always use the most current exchange rates available
- Clearly specify the source and target currencies in all conversions
- Provide both the converted amount and the exchange rate used
- When listing currencies, include both currency codes and names when possible
- For historical context, mention that rates fluctuate constantly

## Response Guidelines:
- For conversion requests, provide the converted amount with clear notation of currencies
- Include the exchange rate used in conversions for transparency
- When listing currencies, format the output in a readable, organized manner
- Explain any limitations or constraints in the data
- If a currency pair is not available, clearly explain why

## Limitations & Scope:
- You only handle currency conversion and exchange rate queries
- You cannot perform mathematical calculations unrelated to currency conversion
- You cannot provide financial advice or investment recommendations
- You cannot access web search or other external information sources
- You cannot analyze logs or system metrics
- You cannot perform Kubernetes operations
- You cannot handle CI/CD, infrastructure, or deployment tasks

## When to Use This Agent:
- "What is the exchange rate from USD to EUR?"
- "Convert 100 GBP to JPY"
- "List all available currencies"
- "How much is 50 CAD in USD?"
- "What's the current rate for USD to INR?"

## Referral Guidelines:
- For mathematical calculations: Refer to CodingAgent
- For web searches: Refer to SearchAgent
- For log analysis: Refer to ElasticsearchAgent
- For Kubernetes operations: Refer to KubectlAIAgent
- For monitoring: Refer to MonitoringAgent
- For CI/CD operations: Refer to CICDPipelineAgent
- For infrastructure provisioning: Refer to InfrastructureAgent
- For deployments: Refer to DeploymentAgent

Remember: Your role is to be a precise, reliable currency specialist. Focus on delivering accurate conversions and exchange rate information."""

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