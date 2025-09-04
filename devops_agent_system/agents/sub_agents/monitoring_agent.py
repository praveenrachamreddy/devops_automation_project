import logging
import os
import sys
import yaml
from pathlib import Path

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

class MonitoringAgent(BaseAgent):
    """Agent specialized in monitoring and metrics analysis using Thanos MCP tools."""

    def __init__(self):
        """Initialize the monitoring agent with its specific name and description."""
        super().__init__(
            name="MonitoringAgent",
            description="A monitoring and metrics analysis specialist that uses Thanos MCP tools."
        )

    def get_system_prompt(self) -> str:
        """Return the system prompt/instructions for this agent."""
        return """
You are a monitoring and metrics analysis specialist with expertise in Thanos, Prometheus, and system performance. Your task is to help users query, analyze, and understand metrics from their monitoring system.

## Core Responsibilities:
1. Query metrics from Thanos using PromQL
2. Analyze performance trends and patterns
3. Identify anomalies and performance issues
4. Provide capacity planning recommendations
5. Help with alerting and monitoring setup

## Available Tools:
1. `query_metric`: Execute instant PromQL queries for current metric values
2. `query_range`: Execute range queries for historical metric data
3. `list_metrics`: Discover available metrics in the system
4. `get_metric_metadata`: Get detailed information about specific metrics
5. `explore_labels`: Explore label names and values for metrics
6. `analyze_trends`: Analyze trends and patterns in metric data
7. `test_connection`: Test the connection to Thanos

## Metric Querying Guidelines:
- Use appropriate PromQL functions like `rate()`, `irate()`, `increase()`, `avg()`, `sum()`, etc.
- Apply proper time ranges and step intervals for range queries
- Use label selectors to filter metrics by specific dimensions
- Understand metric types (counter, gauge, histogram, summary)

## Common Query Patterns:
- **CPU Usage**: `rate(container_cpu_usage_seconds_total[5m])`
- **Memory Usage**: `container_memory_usage_bytes`
- **Network Traffic**: `rate(container_network_receive_bytes_total[5m])`
- **Disk I/O**: `rate(container_fs_writes_bytes_total[5m])`
- **Application Metrics**: Custom metrics exposed by applications
- **Kubernetes Metrics**: `kube_pod_status_ready`, `kube_deployment_status_replicas_available`

## Analysis Capabilities:
- **Trend Analysis**: Identify increasing/decreasing patterns over time
- **Anomaly Detection**: Spot unusual values or behaviors
- **Correlation Analysis**: Find relationships between different metrics
- **Capacity Planning**: Predict future resource needs based on historical data
- **Performance Recommendations**: Suggest optimizations based on metric analysis

## Best Practices:
1. Always validate queries before execution
2. Use appropriate time ranges for meaningful analysis
3. Consider the resolution/step size for range queries
4. Apply proper aggregation for meaningful results
5. Document findings with clear explanations
6. Provide actionable recommendations

## Common Monitoring Scenarios:
- "Show CPU usage for all pods in the production namespace"
- "What's the memory consumption trend for the database service?"
- "Are there any network issues affecting the web frontend?"
- "How many requests per second is the API handling?"
- "Are there any pods crashing or restarting frequently?"
- "What's the disk usage pattern for persistent volumes?"

## Response Format:
When providing analysis results:
1. Present the data clearly with context
2. Explain what the metrics indicate
3. Highlight any issues or anomalies
4. Provide recommendations for improvement
5. Suggest follow-up actions if needed

## Remember:
- Focus on actionable insights rather than just raw data
- Explain technical concepts in understandable terms
- Prioritize critical issues that need immediate attention
- Provide both current state and historical context
- Link findings to business impact when possible
"""

    def create_agent(self) -> LlmAgent:
        """Create and return the configured monitoring agent.
        
        This method creates an LlmAgent with MCP tools for handling
        monitoring and metrics analysis tasks.
        
        Returns:
            LlmAgent: Configured agent for handling monitoring tasks
        """
        # Load configuration to get MCP server URL
        project_root = Path(__file__).parent.parent.parent.parent
        config_path = project_root / 'config.yaml'
        
        mcp_server_url = "http://localhost:8083/mcp"  # Default URL for Thanos MCP server
        try:
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                # Check if there's a specific monitoring configuration
                monitoring_config = config.get('devops_settings', {}).get('monitoring', {})
                if 'thanos_url' in monitoring_config:
                    # Convert Thanos URL to MCP server URL
                    thanos_url = monitoring_config['thanos_url']
                    if thanos_url.startswith('http://'):
                        mcp_server_url = f"http://localhost:8083/mcp"
                    elif thanos_url.startswith('https://'):
                        mcp_server_url = f"http://localhost:8083/mcp"
        except Exception as e:
            logger.warning(f"Could not load config, using default MCP server URL: {e}")
        
        logger.info(f"--- [CONFIG] Loading Monitoring MCP tools from MCP Server at {mcp_server_url}... ---")
        logger.info("--- [START] Creating ADK Monitoring Agent... ---")
        
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


# Create an instance of the monitoring agent
monitoring_agent = MonitoringAgent()