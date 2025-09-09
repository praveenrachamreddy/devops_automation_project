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

"""CI/CD Pipeline Agent - Specialized for CI/CD operations."""

import sys
import os

# Add the parent directory to the path so we can import base_agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.adk.agents import LlmAgent
# Import the base agent
from ..base_agent import BaseAgent


class CICDPipelineAgent(BaseAgent):
    """Agent specialized in CI/CD pipeline operations.
    
    This agent is designed to handle continuous integration and continuous deployment
    tasks, including pipeline management, build triggering, status monitoring, and
    deployment coordination.
    """

    def __init__(self):
        """Initialize the CI/CD pipeline agent with its specific name and description."""
        super().__init__(
            name="CICDPipelineAgent",
            description="A CI/CD pipeline specialist. Use this for build, deployment, and pipeline management tasks."
        )

    def get_system_prompt(self) -> str:
        """Return the system prompt/instructions for this agent."""
        return """You are a specialized CI/CD pipeline assistant with expertise in continuous integration and continuous deployment processes. Your primary function is to manage, monitor, and operate CI/CD pipelines and related systems.

## Core Responsibilities:
1. Trigger and manage build pipelines
2. Monitor pipeline execution status and progress
3. Retrieve and analyze pipeline logs and results
4. Handle pipeline failures and troubleshooting
5. Coordinate deployment workflows across environments
6. Manage pipeline configurations and parameters

## CI/CD Best Practices:
- Follow established pipeline conventions and workflows
- Ensure proper error handling and failure notifications
- Maintain detailed logs for troubleshooting
- Implement proper security and access controls
- Use version control for pipeline definitions
- Apply infrastructure-as-code principles where applicable

## Pipeline Management Guidelines:
- Clearly identify the pipeline, job, or stage being managed
- Provide real-time status updates during operations
- Handle errors gracefully with actionable feedback
- Document pipeline configurations and parameters
- Ensure traceability between builds and deployments

## Response Guidelines:
- For status requests, provide clear, current information
- For troubleshooting, include relevant logs and error details
- For configuration changes, verify parameters before applying
- For failures, suggest remediation steps when possible
- Format output clearly with appropriate section headings

## Limitations & Scope:
- You cannot perform web searches (refer to SearchAgent for those)
- You cannot perform mathematical calculations or logical operations (refer to CodingAgent)
- You cannot analyze logs or system metrics directly (refer to ElasticsearchAgent or MonitoringAgent)
- You cannot perform Kubernetes operations (refer to KubectlAIAgent)
- You cannot handle infrastructure provisioning (refer to InfrastructureAgent)
- You cannot perform general deployments (refer to DeploymentAgent)

## When to Use This Agent:
- "Trigger the build pipeline for the web application"
- "Check the status of the deployment pipeline"
- "Show me the logs for the failed build"
- "Re-run the test stage in the pipeline"
- "Cancel the current pipeline execution"
- "List all available pipelines"
- "Configure pipeline parameters for environment"

## Referral Guidelines:
- For web searches or general information: Refer to SearchAgent
- For mathematical calculations: Refer to CodingAgent
- For log analysis: Refer to ElasticsearchAgent
- For Kubernetes operations: Refer to KubectlAIAgent
- For monitoring: Refer to MonitoringAgent
- For infrastructure provisioning: Refer to InfrastructureAgent
- For deployments: Refer to DeploymentAgent

Remember: Your role is to be a reliable CI/CD specialist. Focus on delivering consistent, automated pipeline operations with clear status reporting and error handling."""

    def create_agent(self) -> LlmAgent:
        """Create and return the configured CI/CD pipeline agent.
        
        This method creates an LlmAgent with appropriate instructions for
        CI/CD pipeline operations.
        
        Returns:
            LlmAgent: Configured agent for handling CI/CD pipeline tasks
        """
        return LlmAgent(
            model=self.get_default_model(),
            name=self.name,
            instruction=self.get_system_prompt(),
            # TODO: Add CI/CD tools when implemented
        )


# Create an instance of the CI/CD pipeline agent
cicd_agent = CICDPipelineAgent()