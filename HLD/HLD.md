# High-Level Design (HLD) - DevOps Automation Assistant

## 1. Overview

The DevOps Automation Assistant is a comprehensive agentic system built with the Google Agent Development Kit (ADK) that provides intelligent automation for various DevOps tasks. It features a modular architecture with specialized agents for different domains, custom tools, and integration with external systems via the Model Context Protocol (MCP).

## 2. System Architecture

```
DevOps Automation Assistant
├── DevOpsOrchestratorAgent (Root)
│   ├── Simple Task Agents (as Tools)
│   │   ├── SearchAgent
│   │   └── CodingAgent
│   └── Specialized Agents (as Sub-agents)
│       ├── ElasticsearchAgent
│       ├── KubectlAIAgent
│       ├── MonitoringAgent
│       ├── CICDPipelineAgent (TODO)
│       ├── InfrastructureAgent (TODO)
│       └── DeploymentAgent (TODO)
├── Custom Tools
│   ├── SearchTool
│   ├── CodeExecutionTool
│   └── MCP Tools
├── MCP Integration
│   ├── Elasticsearch MCP Server
│   └── Kubectl-AI MCP Server
│   └── Thanos MCP Server
└── Configuration
    └── config.yaml
```

## 3. Core Components

### 3.1 DevOpsOrchestratorAgent (Root Agent)
The central orchestrator that routes tasks to appropriate specialized agents based on the task domain. It uses a hybrid model of delegation:
- Simple tasks are delegated via AgentTool pattern
- Complex tasks are transferred via ADK's built-in transfer mechanism

### 3.2 Specialized Agents

#### 3.2.1 Simple Task Agents (as Tools)
- **SearchAgent**: Handles simple web search queries using Google Search
- **CodingAgent**: Executes code for calculations, transformations, and logic operations

#### 3.2.2 Specialized Agents (as Sub-agents)
- **ElasticsearchAgent**: Analyzes logs stored in Elasticsearch
- **KubectlAIAgent**: Manages Kubernetes/OpenShift cluster operations
- **MonitoringAgent**: Handles system metrics and performance analysis
- **CICDPipelineAgent**: Manages CI/CD pipeline operations (TODO)
- **InfrastructureAgent**: Manages infrastructure provisioning (TODO)
- **DeploymentAgent**: Handles application deployments (TODO)

### 3.3 MCP Integration
The system connects to external systems that expose MCP-compatible interfaces:
- **Elasticsearch MCP Server**: Connects to Elasticsearch for log analysis
- **Kubectl-AI MCP Server**: Connects to Kubernetes/OpenShift clusters
- **Thanos MCP Server**: Connects to Thanos/Prometheus for metrics analysis

### 3.4 Configuration
The system uses `config.yaml` for:
- Model settings (LLM selection)
- DevOps tool configurations (API keys, endpoints)
- Agent behavior settings
- MCP connection parameters

## 4. Data Flow

1. **User Request**: User submits a DevOps task to the assistant
2. **Orchestration**: Root agent analyzes the request and determines the appropriate agent
3. **Routing Decision**:
   - Simple tasks: Direct execution by tool agents
   - Specialized tasks: Transfer to sub-agents
4. **Task Execution**:
   - Tool agents execute tasks directly
   - Sub-agents handle complex specialized workflows
5. **Tool Usage**: Agents use custom tools or MCP tools to interact with external systems
6. **Response Generation**: Agents process results and generate responses
7. **User Response**: Final response is returned to the user

## 5. Key Design Principles

1. **Modularity**: Each agent has a single, well-defined responsibility
2. **Extensibility**: Easy to add new agents and tools
3. **Reusability**: Simple agents can be reused across different workflows
4. **Configuration-Driven**: Behavior controlled through config files
5. **Observability**: Comprehensive logging and monitoring
6. **Security**: Secure handling of credentials and API keys

## 6. Implementation Approach

1. **Base Agent Class**: Extend the `BaseAgent` class for common functionality
2. **Configuration Management**: Use YAML config for settings
3. **Tool Development**: Implement custom tools using `FunctionTool` wrapper
4. **MCP Integration**: Use `MCPToolset` with `StreamableHTTPConnectionParams` for connecting to external systems
5. **Agent Transfer**: Use ADK's sub-agent transfer mechanism for specialized agents
6. **Testing**: Develop unit tests for each agent and tool
7. **Documentation**: Provide clear documentation for each component