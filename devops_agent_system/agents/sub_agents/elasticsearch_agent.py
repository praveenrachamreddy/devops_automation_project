# Copyright 2025 Praveen Rachamreddy
# Licensed under the Apache License, Version 2.0

"""Elasticsearch Agent - connects to Elasticsearch MCP server via npx."""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

from agents.base_agent import BaseAgent


class ElasticsearchAgent(BaseAgent):
    """Agent that connects to Elasticsearch MCP server via npx."""

    def __init__(self):
        super().__init__(
            name="ElasticsearchAgent",
            description="A log-analysis specialist that queries your Elasticsearch cluster."
        )

    def create_agent(self) -> LlmAgent:
        # choose model from config if provided
        model = "gemini-2.0-flash"
        if self.config and "agent_settings" in self.config:
            model = self.config["agent_settings"].get("model", model)

        # Get Elasticsearch credentials from config
        es_config = self.config.get('elasticsearch_settings', {})
        es_url = es_config.get('url', 'http://localhost:9200')
        es_username = es_config.get('username', 'elastic')
        es_password = es_config.get('password', 'changeme')
        ssl_skip_verify = es_config.get('ssl_skip_verify', False)

        # Prepare environment variables for the MCP server
        env_vars = {
            "ES_URL": es_url,
            "ES_USERNAME": es_username,
            "ES_PASSWORD": es_password
        }
        
        # Add SSL skip verify if enabled
        if ssl_skip_verify:
            env_vars["ES_SSL_SKIP_VERIFY"] = "true"

        return LlmAgent(
            model=model,
            name=self.name,
            instruction=f"""You are {self.name}, {self.description}.

You have access to the following MCP tools backed by Elasticsearch:
- list_indices
- get_mappings
- search (Query DSL)
- esql
- get_shards

Steps when answering user questions:
1. Use list_indices with a suitable pattern to find relevant indices.
2. Use get_mappings to understand the data structure.
3. Formulate precise queries with search or esql.
4. Summarise findings clearly.

Explain your reasoning along the way.
""",
            tools=[
                MCPToolset(
                    connection_params=StdioConnectionParams(
                        server_params=StdioServerParameters(
                            command='npx',
                            args=[
                                "-y",  # Argument for npx to auto-confirm install
                                "@elastic/mcp-server-elasticsearch@0.3.1"
                            ],
                            env=env_vars
                        ),
                        timeout=120.0  # Increase timeout to 120 seconds
                    ),
                    # Optional: Filter which tools from the MCP server are exposed
                    # tool_filter=['list_indices', 'search', 'esql']
                )
            ],
        )


# Singleton ready to import elsewhere
elasticsearch_agent = ElasticsearchAgent()