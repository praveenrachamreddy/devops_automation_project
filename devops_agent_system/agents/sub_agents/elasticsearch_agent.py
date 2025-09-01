# Copyright 2025 Praveen Rachamreddy
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Elasticsearch Agent - Specialized for log analysis using Elasticsearch MCP server."""

import sys
import os

# Add the parent directory to the path so we can import base_agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

# Import the base agent
from agents.base_agent import BaseAgent


class ElasticsearchAgent(BaseAgent):
    """Agent specialized in Elasticsearch log analysis using MCP server."""

    def __init__(self):
        """Initialize the Elasticsearch agent."""
        super().__init__(
            name="ElasticsearchAgent",
            description="A log analysis specialist that uses Elasticsearch to search and analyze logs."
        )

    def create_agent(self) -> Agent:
        """Create and return the Elasticsearch agent with MCP toolset."""
        # Use default model if config is empty
        model = "gemini-2.0-flash"
        if self.config and 'agent_settings' in self.config:
            model = self.config['agent_settings'].get('model', model)
            
        # Get Elasticsearch configuration from config
        es_config = self.config.get('elasticsearch_settings', {})
        es_url = es_config.get('url', 'http://localhost:9200')
        es_username = es_config.get('username', 'elastic')
        es_password = es_config.get('password', 'changeme')
        
        return Agent(
            model=model,
            name=self.name,
            instruction=f"""You are {self.name}, {self.description}.
            
Your task is to help users analyze logs stored in Elasticsearch. You have access to an Elasticsearch MCP server 
that provides the following tools:

1. `list_indices` - List all available Elasticsearch indices
2. `get_mappings` - Get field mappings for a specific Elasticsearch index
3. `search` - Perform an Elasticsearch search with the provided query DSL
4. `esql` - Perform an ES|QL query
5. `get_shards` - Get shard information for all or specific indices

When helping users with log analysis:

1. First, identify the relevant indices using `list_indices` with an appropriate pattern
2. Understand the structure of the data using `get_mappings` on the relevant index
3. Formulate specific queries using either `search` (for complex Query DSL) or `esql` (for simpler queries)
4. Interpret the results and provide meaningful insights to the user

Always explain your approach and the insights you derive from the log data.
""",
            tools=[
                MCPToolset(
                    connection_params=StdioServerParameters(
                        command="docker",
                        args=[
                            "run", "-i", "--rm",
                            "-e", "ES_URL", "-e", "ES_USERNAME", "-e", "ES_PASSWORD",
                            "docker.elastic.co/mcp/elasticsearch:latest",
                            "stdio"
                        ],
                        env={
                            "ES_URL": es_url,
                            "ES_USERNAME": es_username,
                            "ES_PASSWORD": es_password
                        }
                    )
                )
            ],
        )


# Create an instance of the Elasticsearch agent
elasticsearch_agent = ElasticsearchAgent()