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

"""Base Agent Class - Provides common functionality for all agents."""

import sys
import os
import yaml
import logging

from google.adk.agents import Agent
from google.adk.tools import google_search

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root and subdirectories to the path
project_root = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.dirname(project_root)
sys.path.insert(0, parent_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'agents'))
sys.path.insert(0, os.path.join(project_root, 'agents', 'sub_agents'))
sys.path.insert(0, os.path.join(project_root, 'tools'))


class BaseAgent:
    """Base class for all agents in the DevOps Automation Assistant."""

    def __init__(self, name: str, description: str):
        """Initialize the base agent.
        
        Args:
            name: The name of the agent
            description: A brief description of the agent's purpose
        """
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"{__name__}.{name}")
        
        # Load configuration
        config_path = os.path.join(parent_dir, 'config.yaml')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.warning(f"Config file not found at {config_path}. Using empty config.")
            self.config = {}
        except Exception as e:
            self.logger.error(f"Error loading config file: {e}. Using empty config.")
            self.config = {}

    def get_system_prompt(self) -> str:
        """Get the system prompt for the agent.
        
        Returns:
            The system prompt string
        """
        return f"You are {self.name}, {self.description}."

    def get_input_schema(self):
        """Get the input schema for the agent (if any).
        
        Returns:
            None by default (no input schema)
        """
        return None

    def get_output_schema(self):
        """Get the output schema for the agent (if any).
        
        Returns:
            None by default (no output schema)
        """
        return None

    def get_tools(self):
        """Get the base tools available to all agents.
        
        Returns:
            List of base tools
        """
        # All agents get the google_search tool by default
        # We'll add save_note in the actual agent implementations to avoid circular imports
        return [google_search]

    def create_agent(self) -> Agent:
        """Create and return the ADK agent.
        
        Returns:
            Configured ADK Agent instance
        """
        raise NotImplementedError("Subclasses must implement create_agent method")