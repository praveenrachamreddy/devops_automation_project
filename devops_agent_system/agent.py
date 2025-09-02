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

"""Main Agent Orchestrator - Entry point for the ADK web interface.

This module defines a root agent that acts as an orchestrator, using a hybrid
model of delegation: using simple agents as tools, and transferring to complex
sub-agents for sequential workflows.
"""

import sys
import os
import yaml

# Add the project root and subdirectories to the path
project_root = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.dirname(project_root)
sys.path.insert(0, parent_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'agents'))
sys.path.insert(0, os.path.join(project_root, 'agents', 'sub_agents'))

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import agent_tool
from google.adk.code_executors import BuiltInCodeExecutor


# =============================================================================
# LOAD CONFIGURATION
# =============================================================================

config_path = os.path.join(parent_dir, 'config.yaml')
try:
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
except FileNotFoundError:
    print(f"Config file not found at {config_path}. Using default configuration.")
    config = {
        'agent_settings': {
            'model': 'gemini-2.0-flash'
        }
    }
except Exception as e:
    print(f"Error loading config file: {e}. Using default configuration.")
    config = {
        'agent_settings': {
            'model': 'gemini-2.0-flash'
        }
    }

model_name = config['agent_settings']['model']


# =============================================================================
# 1. DEFINE SPECIALIZED AGENTS (THE "EXPERTS")
# =============================================================================

# Import the simple, single-purpose agents
from agents.sub_agents.search_agent import search_agent
from agents.sub_agents.elasticsearch_agent import elasticsearch_agent

# An agent that can only execute code.
coding_agent = LlmAgent(
    name="CodingAgent",
    model=model_name,
    description="A coding specialist. Use this for math, logic, or coding tasks.",
    code_executor=BuiltInCodeExecutor(),
)

# TODO: Import the complex workflow agents when they are implemented
# from agents.sub_agents.cicd_agent import cicd_agent
# from agents.sub_agents.infrastructure_agent import infrastructure_agent
# from agents.sub_agents.monitoring_agent import monitoring_agent
# from agents.sub_agents.deployment_agent import deployment_agent

# =============================================================================
# 2. DEFINE THE ORCHESTRATOR (ROOT AGENT)
# =============================================================================

# This root agent uses the hybrid model of orchestration.
root_agent = LlmAgent(
    name="DevOpsOrchestratorAgent",
    model=model_name,
    instruction="""You are a master DevOps orchestrator. Delegate tasks as follows:
- For quick searches (e.g., 'search for X'), use the SearchAgent tool.
- For math, logic, or coding tasks (e.g., 'calculate X' or 'write code for Y'), use the CodingAgent tool.
- For log analysis and Elasticsearch queries, use the ElasticsearchAgent tool.
- For CI/CD operations, transfer to CICDPipelineAgent.
- For infrastructure provisioning, transfer to InfrastructureAgent.
- For monitoring tasks, transfer to MonitoringAgent.
- For deployment operations, transfer to DeploymentAgent.

If unsure, ask the user for clarification.""",
    tools=[
        agent_tool.AgentTool(agent=search_agent.create_agent()),
        agent_tool.AgentTool(agent=coding_agent),
        agent_tool.AgentTool(agent=elasticsearch_agent.create_agent()),
    ],
    # TODO: Add sub_agents when they are implemented
    # sub_agents=[
    #     cicd_agent.create_agent(),
    #     infrastructure_agent.create_agent(),
    #     monitoring_agent.create_agent(),
    #     deployment_agent.create_agent(),
    # ],
)

# This is required for the ADK to find the root agent
agent = root_agent