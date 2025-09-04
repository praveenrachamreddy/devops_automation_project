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

"""Search Agent - Specialized for using the Google Search tool."""

import sys
import os

# Add the parent directory to the path so we can import base_agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.adk.agents import LlmAgent
from google.adk.tools import google_search

# Import the base agent
from agents.base_agent import BaseAgent


class SearchAgent(BaseAgent):
    """Agent specialized in using the Google Search tool.
    
    This agent is designed to handle web search queries and provide information
    retrieved from the internet. It uses the Google Search tool provided by
    the Google ADK.
    """

    def __init__(self):
        """Initialize the search agent with its specific name and description."""
        super().__init__(
            name="SearchAgent",
            description="A search specialist. Use this for simple questions that require web search."
        )

    def create_agent(self) -> LlmAgent:
        """Create and return the configured search agent.
        
        This method creates an LlmAgent with the Google Search tool and
        appropriate instructions for search-based queries.
        
        Returns:
            LlmAgent: Configured agent for handling search queries
        """
        return LlmAgent(
            model=self.get_default_model(),
            name=self.name,
            instruction=self.get_system_prompt(),
            tools=[google_search],
        )


# Create an instance of the search agent
search_agent = SearchAgent()