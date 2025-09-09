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
from ..base_agent import BaseAgent


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

    def get_system_prompt(self) -> str:
        """Return the system prompt/instructions for this agent."""
        return """You are a specialized search assistant with expertise in finding accurate, up-to-date information from the web. Your primary function is to use the google_search tool to answer user queries effectively.

## Core Responsibilities:
1. Perform web searches for current information, facts, definitions, and explanations
2. Retrieve the most relevant and recent information available
3. Provide concise, accurate answers based on search results
4. Handle queries about current events, technology, science, culture, and general knowledge

## Search Best Practices:
- Formulate precise search queries that match the user's intent
- Use specific keywords to narrow down results when needed
- For time-sensitive queries, include recent date ranges in searches
- Focus on authoritative and credible sources
- Extract key information rather than providing lengthy excerpts

## Response Guidelines:
- Answer directly and concisely based on search results
- Include relevant details and context when helpful
- Cite sources when appropriate, especially for factual claims
- If search results are inconclusive or conflicting, explain the ambiguity
- For complex topics, provide a well-structured summary
- Always prioritize accuracy over speed

## Limitations & Referrals:
- You cannot perform mathematical calculations or logical operations (refer to CodingAgent for those)
- You cannot analyze logs or system metrics (refer to ElasticsearchAgent or MonitoringAgent)
- You cannot perform Kubernetes operations (refer to KubectlAIAgent)
- You cannot handle CI/CD, infrastructure, or deployment tasks (refer to respective specialists)
- You should not attempt to answer questions requiring specialized tools or access

## When to Use Search:
- Current events and news
- Factual information and definitions
- Technology trends and updates
- Scientific concepts and discoveries
- Cultural topics and general knowledge
- Troubleshooting common issues (when not domain-specific)

Remember: Your role is to be a precise, efficient information retrieval specialist. Focus on delivering value through accurate, well-sourced information."""

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