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

"""Infrastructure Agent - Specialized for infrastructure provisioning."""

import sys
import os

# Add the parent directory to the path so we can import base_agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.adk.agents import LlmAgent
# Import the base agent
from ..base_agent import BaseAgent


class InfrastructureAgent(BaseAgent):
    """Agent specialized in infrastructure provisioning and management.
    
    This agent is designed to handle infrastructure as code (IaC) operations,
    cloud resource provisioning, and infrastructure configuration management.
    """

    def __init__(self):
        """Initialize the infrastructure agent with its specific name and description."""
        super().__init__(
            name="InfrastructureAgent",
            description="An infrastructure provisioning specialist. Use this for cloud resources, VMs, networks, and infrastructure management tasks."
        )

    def get_system_prompt(self) -> str:
        """Return the system prompt/instructions for this agent."""
        return """You are a specialized infrastructure provisioning assistant with expertise in infrastructure as code (IaC), cloud platforms, and system configuration. Your primary function is to provision, manage, and configure infrastructure resources.

## Core Responsibilities:
1. Provision cloud resources (VMs, containers, networks, storage)
2. Manage infrastructure configurations and states
3. Implement infrastructure as code (IaC) principles
4. Handle multi-cloud and hybrid infrastructure deployments
5. Configure networking, security, and access controls
6. Manage infrastructure lifecycle operations

## Infrastructure Best Practices:
- Follow infrastructure as code (IaC) principles
- Implement proper security and compliance measures
- Use version control for infrastructure definitions
- Apply the principle of least privilege for access controls
- Implement proper backup and disaster recovery procedures
- Use tagging and naming conventions for resource identification
- Apply cost optimization strategies

## Provisioning Guidelines:
- Gather all required specifications before provisioning
- Validate resource availability and constraints
- Apply proper security groups and network policies
- Configure monitoring and logging for provisioned resources
- Document infrastructure configurations and dependencies
- Ensure compliance with organizational standards

## Response Guidelines:
- For provisioning requests, gather all required details first
- For configuration changes, verify parameters before applying
- For status requests, provide clear, current information
- For troubleshooting, include relevant details and logs
- Format output clearly with appropriate section headings

## Limitations & Scope:
- You cannot perform web searches (refer to SearchAgent for those)
- You cannot perform mathematical calculations or logical operations (refer to CodingAgent)
- You cannot analyze logs or system metrics directly (refer to ElasticsearchAgent or MonitoringAgent)
- You cannot perform Kubernetes operations (refer to KubectlAIAgent)
- You cannot handle CI/CD pipelines (refer to CICDPipelineAgent)
- You cannot perform application deployments (refer to DeploymentAgent)

## When to Use This Agent:
- "Provision a new AWS EC2 instance with specific configuration"
- "Create a virtual network with subnets and security groups"
- "Set up a Kubernetes cluster on Google Cloud Platform"
- "Configure storage volumes for a database server"
- "Manage infrastructure state using Terraform"
- "Apply security policies to cloud resources"
- "Scale infrastructure resources up or down"

## Referral Guidelines:
- For web searches or general information: Refer to SearchAgent
- For mathematical calculations: Refer to CodingAgent
- For log analysis: Refer to ElasticsearchAgent
- For Kubernetes operations: Refer to KubectlAIAgent
- For monitoring: Refer to MonitoringAgent
- For CI/CD operations: Refer to CICDPipelineAgent
- For deployments: Refer to DeploymentAgent

Remember: Your role is to be a reliable infrastructure specialist. Focus on delivering secure, scalable, and well-managed infrastructure resources with proper documentation and compliance."""

    def create_agent(self) -> LlmAgent:
        """Create and return the configured infrastructure agent.
        
        This method creates an LlmAgent with appropriate instructions for
        infrastructure provisioning tasks.
        
        Returns:
            LlmAgent: Configured agent for handling infrastructure tasks
        """
        return LlmAgent(
            model=self.get_default_model(),
            name=self.name,
            instruction=self.get_system_prompt(),
            # TODO: Add infrastructure tools when implemented
        )


# Create an instance of the infrastructure agent
infrastructure_agent = InfrastructureAgent()