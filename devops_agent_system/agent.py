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
from agents.sub_agents.coding_agent import coding_agent
from agents.sub_agents.simple_mcp_agent import simple_mcp_agent
from agents.sub_agents.kubectl_ai_agent import kubectl_ai_agent
from agents.sub_agents.monitoring_agent import monitoring_agent

# Create instances of the specialized agents
search_agent_instance = search_agent.create_agent()

coding_agent_instance = coding_agent.create_agent()

elasticsearch_agent_instance = elasticsearch_agent.create_agent()

simple_mcp_agent_instance = simple_mcp_agent.create_agent()

kubectl_ai_agent_instance = kubectl_ai_agent.create_agent()

monitoring_agent_instance = monitoring_agent.create_agent()

# =============================================================================
# 2. DEFINE THE ORCHESTRATOR (ROOT AGENT)
# =============================================================================

# This root agent uses the hybrid model of orchestration.
root_agent = LlmAgent(
    name="DevOpsOrchestratorAgent",
    model=model_name,
    instruction="""You are a master DevOps orchestrator. Your job is to delegate tasks to the most appropriate agent.

When a user asks a question, you should analyze it and determine which agent is best suited to handle it:

1. If the user asks about Elasticsearch logs, indices, or search queries, you MUST transfer to ElasticsearchAgent using the transfer_to_agent function.
2. If the user asks about currency conversion or exchange rates, you MUST transfer to SimpleMCPAgent using the transfer_to_agent function.
3. If the user asks about Kubernetes operations or cluster management, you MUST transfer to KubectlAIAgent using the transfer_to_agent function.
4. For quick web searches, use the SearchAgent tool.
5. For math, logic, or coding tasks, use the CodingAgent tool.
6. For CI/CD operations, transfer to CICDPipelineAgent.
7. For infrastructure provisioning, transfer to InfrastructureAgent.
8. For monitoring tasks, transfer to MonitoringAgent.
9. For deployment operations, transfer to DeploymentAgent.

Examples of when to transfer:
- User asks: "List all Elasticsearch indices" -> Transfer to ElasticsearchAgent
- User asks: "What is the exchange rate from USD to EUR?" -> Transfer to SimpleMCPAgent
- User asks: "Show me all pods in my cluster" -> Transfer to KubectlAIAgent
- User asks: "Deploy a nginx server" -> Transfer to KubectlAIAgent

To transfer to an agent, you MUST call the transfer_to_agent function with the agent name as a parameter.
Do NOT respond with text suggesting to transfer - you must actually call the function.

If you're unsure which agent to use, ask the user for clarification.""",
    tools=[
        agent_tool.AgentTool(agent=search_agent_instance),
        agent_tool.AgentTool(agent=coding_agent_instance),
    ],
    sub_agents=[
        elasticsearch_agent_instance,
        simple_mcp_agent_instance,
        kubectl_ai_agent_instance,
        monitoring_agent_instance,
    ],
    # TODO: Add sub_agents when they are implemented
    # sub_agents=[
    #     cicd_agent.create_agent(),
    #     infrastructure_agent.create_agent(),
    #     deployment_agent.create_agent(),
    # ],
)

# This is required for the ADK to find the root agent
agent = root_agent