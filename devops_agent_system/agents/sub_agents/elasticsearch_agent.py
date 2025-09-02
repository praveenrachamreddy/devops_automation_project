# Copyright 2025 Praveen Rachamreddy
# Licensed under the Apache License, Version 2.0

"""Elasticsearch Agent – connects to an *already running* MCP server."""

import os
import sys
import base64

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams

from agents.base_agent import BaseAgent


class ElasticsearchAgent(BaseAgent):
    """Agent that talks to an external MCP server over HTTP/SSE."""

    def __init__(self):
        super().__init__(
            name="ElasticsearchAgent",
            description="A log-analysis specialist that queries your running Elasticsearch cluster."
        )

    def create_agent(self) -> Agent:
        # choose model from config if provided
        model = "gemini-2.0-flash"
        if self.config and "agent_settings" in self.config:
            model = self.config["agent_settings"].get("model", model)

        # Get Elasticsearch credentials from config
        es_config = self.config.get('elasticsearch_settings', {})
        es_username = es_config.get('username', 'elastic')
        es_password = es_config.get('password', 'changeme')
        ssl_skip_verify = es_config.get('ssl_skip_verify', False)
        
        # Create basic auth header for the MCP server
        credentials = f"{es_username}:{es_password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        auth_header = f"Basic {encoded_credentials}"

        # Prepare environment variables for the MCP server
        env_vars = {
            "ES_URL": es_config.get('url', 'http://localhost:9200'),
            "ES_USERNAME": es_username,
            "ES_PASSWORD": es_password
        }
        
        # Add SSL skip verify if enabled
        if ssl_skip_verify:
            env_vars["ES_SSL_SKIP_VERIFY"] = "true"

        return Agent(
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
                    connection_params=SseConnectionParams(
                        url="http://localhost:8080/mcp",
                        headers={
                            "Authorization": auth_header
                        }
                    )
                )
            ],
        )


# Singleton ready to import elsewhere
elasticsearch_agent = ElasticsearchAgent()