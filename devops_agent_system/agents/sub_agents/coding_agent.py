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

"""Coding Agent - Specialized for executing code."""

import sys
import os

# Add the parent directory to the path so we can import base_agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.adk.agents import LlmAgent
from google.adk.code_executors import BuiltInCodeExecutor

# Import the base agent
from agents.base_agent import BaseAgent


class CodingAgent(BaseAgent):
    """Agent specialized in executing code."""

    def __init__(self):
        """Initialize the coding agent."""
        super().__init__(
            name="CodingAgent",
            description="A coding specialist. Use this for math, logic, or coding tasks."
        )

    def create_agent(self) -> LlmAgent:
        """Create and return the coding agent."""
        # Use default model if config is empty
        model = "gemini-2.0-flash"
        if self.config and 'agent_settings' in self.config:
            model = self.config['agent_settings'].get('model', model)
            
        return LlmAgent(
            model=model,
            name=self.name,
            instruction=self.get_system_prompt(),
            code_executor=BuiltInCodeExecutor(),
        )


# Create an instance of the coding agent
coding_agent = CodingAgent()