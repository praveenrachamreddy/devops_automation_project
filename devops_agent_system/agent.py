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

"""Main Agent Orchestrator - Entry point for the ADK web interface."""

import yaml
import importlib
import os
import sys

from google.adk.agents import LlmAgent
from google.adk.tools import agent_tool

# =============================================================================
# CONFIGURATION LOADING
# =============================================================================

def load_config():
    """Loads the main configuration from config.yaml."""
    # Assume config.yaml is in the project root, which is the parent of this file's directory.
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(project_root, 'config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Warning: Config file not found at {config_path}. Using default model.")
        return {'agent_settings': {'model': 'gemini-2.0-flash'}}
    except Exception as e:
        print(f"Error loading config file: {e}. Using default configuration.")
        return {'agent_settings': {'model': 'gemini-2.0-flash'}}

config = load_config()
model_name = config.get('agent_settings', {}).get('model', 'gemini-2.0-flash')


# =============================================================================
# AGENT REGISTRY AND DYNAMIC LOADING
# =============================================================================

# The agent registry provides a centralized and extensible way to manage agents.
# Using relative imports (.) makes the loading more robust when this package is
# imported by other modules (like main.py).
AGENT_REGISTRY = {
    "search_agent": ".agents.sub_agents.search_agent",
    "coding_agent": ".agents.sub_agents.coding_agent",
    "elasticsearch_agent": ".agents.sub_agents.elasticsearch_agent",
    "simple_mcp_agent": ".agents.sub_agents.simple_mcp_agent",
    "kubectl_ai_agent": ".agents.sub_agents.kubectl_ai_agent",
    "monitoring_agent": ".agents.sub_agents.monitoring_agent",
    "cicd_agent": ".agents.sub_agents.cicd_agent",
    "infrastructure_agent": ".agents.sub_agents.infrastructure_agent",
    "deployment_agent": ".agents.sub_agents.deployment_agent",
}

# Define which agents are simple tools vs. complex, transferable sub-agents.
TOOL_AGENTS = ["search_agent", "coding_agent"]
TRANSFER_AGENTS = [
    "elasticsearch_agent",
    "simple_mcp_agent",
    "kubectl_ai_agent",
    "monitoring_agent",
    "cicd_agent",
    "infrastructure_agent",
    "deployment_agent",
]

def load_agent_from_registry(agent_name: str):
    """
    Dynamically imports and creates an agent instance from the registry.
    This allows for a plug-and-play architecture for agents.
    """
    try:
        module_path = AGENT_REGISTRY[agent_name]
        # The package argument is crucial for relative imports to work correctly.
        agent_module = importlib.import_module(module_path, package="devops_agent_system")
        # Assumes the module contains a factory object with the same name as the agent
        agent_factory = getattr(agent_module, agent_name)
        return agent_factory.create_agent()
    except (ImportError, KeyError, AttributeError) as e:
        print(f"Error loading agent '{agent_name}': {e}", file=sys.stderr)
        return None

# Eagerly load all registered agents.
print("Loading agents...")
all_agents = {name: load_agent_from_registry(name) for name in AGENT_REGISTRY}
all_agents = {name: agent for name, agent in all_agents.items() if agent} # Filter out failed loads
print("Agents loaded successfully.")

# Separate agents into tools and sub-agents for the orchestrator
tool_agent_instances = [
    agent_tool.AgentTool(agent=all_agents[name])
    for name in TOOL_AGENTS if name in all_agents
]
sub_agent_instances = [
    all_agents[name] for name in TRANSFER_AGENTS if name in all_agents
]


# =============================================================================
# ORCHESTRATOR (ROOT AGENT) DEFINITION
# =============================================================================

root_agent = LlmAgent(
    name="DevOpsOrchestratorAgent",
    model=model_name,
    instruction="""You are a master DevOps orchestrator and automation expert. Your primary responsibility is to analyze user requests and delegate them to the most appropriate specialized agent or tool.


    
You have access to the full conversation history through the session context, so you can understand follow-up questions and maintain context across turns.

## Core Principles:
1.  **Handle Greetings**: For simple, conversational greetings like "hi" or "hello", respond directly and politely. Do not use any tools or agents for this.
2.  **Maintain Context**: You have access to the full conversation history for each session. Use this history to understand follow-up questions and maintain context across turns.
3.  **Analyze Intent**: For any other request, analyze the user's intent to determine the correct course of action.
4.  **Delegate to Sub-Agents**: For complex, multi-step tasks that fall into a specific domain (like Kubernetes, monitoring, or CI/CD), transfer control to the appropriate specialized sub-agent.
5.  **Use Tools**: For simple, single-step tasks (like a web search or a calculation), use a direct tool call.
6.  **Clarify Ambiguity**: If the user's request is unclear, ask specific questions to understand their goal before proceeding.

## Agent Capabilities:
You have access to a set of tools for simple tasks and a team of specialized sub-agents for complex workflows.

-   **Tools**: For direct, immediate actions like web searches or code execution.
-   **Sub-Agents**: For domain-specific tasks like log analysis, cloud infrastructure management, Kubernetes operations, CI/CD pipelines, and monitoring. You will be shown the descriptions of these agents to make your decision.

## Critical Rules:
1.  **Transfer Priority**: If a request falls into the domain of a specialized sub-agent, you MUST use the `transfer_to_agent()` function. Do not try to answer it yourself.
2.  **Focus**: Your primary role is to route and delegate. Let the specialized agents and tools handle the details of the execution.""",
    tools=tool_agent_instances,
    sub_agents=sub_agent_instances,
)

# This is required for the ADK to find the root agent
agent = root_agent
