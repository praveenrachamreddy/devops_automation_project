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

"""Base Agent Class - Provides common functionality for all agents following Google ADK patterns."""

import sys
import os
import yaml
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from google.adk.agents import Agent

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


class BaseAgent(ABC):
    """Base class for all agents in the DevOps Automation Assistant following Google ADK patterns.
    
    This class provides common functionality and structure for all specialized agents.
    It handles configuration loading, logging, and defines the interface that all
    agents must implement.
    """

    def __init__(self, name: str, description: str):
        """Initialize the base agent with common functionality.
        
        Args:
            name: The name of the agent
            description: A brief description of the agent's purpose
        """
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"{__name__}.{name}")
        
        # Load configuration
        # The config.yaml file is in the project root, not in the devops_agent_system directory
        project_root = os.path.dirname(parent_dir)
        config_path = os.path.join(project_root, 'config.yaml')
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
            The system prompt string that defines the agent's behavior
        """
        return f"You are {self.name}, {self.description}."

    def get_input_schema(self) -> Optional[Dict[str, Any]]:
        """Get the input schema for the agent (if any).
        
        Returns:
            Dictionary defining the expected input structure, or None if no schema
        """
        return None

    def get_output_schema(self) -> Optional[Dict[str, Any]]:
        """Get the output schema for the agent (if any).
        
        Returns:
            Dictionary defining the output structure, or None if no schema
        """
        return None

    def get_default_model(self) -> str:
        """Get the default model name from configuration.
        
        Returns:
            Model name string
        """
        model = "gemini-2.0-flash"
        if self.config and 'agent_settings' in self.config:
            model = self.config['agent_settings'].get('model', model)
        return model

    @abstractmethod
    def create_agent(self) -> Agent:
        """Create and return the Google ADK agent.
        
        This method must be implemented by all subclasses to create and configure
        the specific agent with its tools, instructions, and other properties.
        
        Returns:
            Configured Google ADK Agent instance
        """
        pass