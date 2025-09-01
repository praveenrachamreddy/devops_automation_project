# DevOps Automation Assistant Architecture

## 1. High-Level Architecture Overview

```
DevOps Automation Assistant
├── Orchestrator Agent (Root)
│   ├── Simple Task Agents (as Tools)
│   │   ├── Search Agent
│   │   ├── Coding Agent
│   │   └── Elasticsearch Agent
│   └── Complex Workflow Agents (as Sub-agents)
│       ├── CI/CD Pipeline Agent
│       ├── Infrastructure Agent
│       ├── Monitoring Agent
│       └── Deployment Agent
├── Custom Tools
│   ├── CI/CD Tools
│   ├── Infrastructure Tools
│   ├── Monitoring Tools
│   └── Deployment Tools
├── MCP Integration
│   └── External DevOps Systems
└── Configuration
    └── config.yaml
```

## 2. Component Details

### 2.1 Orchestrator Agent (Root Agent)
- **Role**: Central decision maker that routes tasks to appropriate specialized agents
- **Implementation**: Uses hybrid orchestration model:
  - Simple tasks delegated via `AgentTool` pattern
  - Complex workflows transferred via ADK's built-in transfer mechanism
- **Routing Logic**:
  - Search queries → Search Agent
  - Coding/math tasks → Coding Agent
  - Log analysis → Elasticsearch Agent
  - CI/CD operations → CI/CD Pipeline Agent
  - Infrastructure provisioning → Infrastructure Agent
  - Monitoring tasks → Monitoring Agent
  - Deployment operations → Deployment Agent

### 2.2 Specialized Agents

#### 2.2.1 Simple Task Agents (as Tools)
- **Search Agent**:
  - Purpose: Handle simple web search queries
  - Tools: Google Search built-in tool
  - Implementation: Similar to your existing search agent

- **Coding Agent**:
  - Purpose: Execute code for calculations, transformations, etc.
  - Tools: BuiltInCodeExecutor
  - Implementation: Similar to your existing coding agent

- **Elasticsearch Agent**:
  - Purpose: Analyze logs stored in Elasticsearch
  - Tools: Elasticsearch MCP server tools
  - Implementation: Connects to Elasticsearch MCP server via Docker

#### 2.2.2 Complex Workflow Agents (as Sub-agents)

- **CI/CD Pipeline Agent**:
  - Purpose: Manage CI/CD pipeline operations
  - Capabilities:
    - Trigger builds
    - Monitor pipeline status
    - Retrieve pipeline logs
    - Handle pipeline failures

- **Infrastructure Agent**:
  - Purpose: Manage infrastructure provisioning and configuration
  - Capabilities:
    - Provision resources (VMs, containers, networks)
    - Configure infrastructure components
    - Manage infrastructure state

- **Monitoring Agent**:
  - Purpose: Monitor system health and performance
  - Capabilities:
    - Retrieve metrics from monitoring systems
    - Analyze system performance
    - Generate alerts based on thresholds

- **Deployment Agent**:
  - Purpose: Handle application deployments
  - Capabilities:
    - Deploy applications to various environments
    - Rollback deployments
    - Verify deployment status

### 2.3 Custom Tools

- **CI/CD Tools**:
  - Integration with Jenkins, GitHub Actions, GitLab CI
  - Trigger pipeline execution
  - Retrieve pipeline status and logs

- **Infrastructure Tools**:
  - Integration with Terraform, AWS, GCP, Azure
  - Provision and manage infrastructure resources
  - Retrieve infrastructure state

- **Monitoring Tools**:
  - Integration with Prometheus, Grafana, Datadog
  - Retrieve system metrics
  - Set up alerts and notifications

- **Deployment Tools**:
  - Integration with Kubernetes, Docker, Helm
  - Deploy and manage applications
  - Perform rolling updates and rollbacks

### 2.4 MCP Integration

- **Purpose**: Connect to external DevOps systems that expose MCP-compatible interfaces
- **Implementation**:
  - Use `MCPToolset` to connect to MCP servers
  - Expose DevOps tools as MCP tools for external consumption
  - Support for stdio, HTTP, and other MCP transport mechanisms
- **Elasticsearch MCP Server**:
  - Connects to Elasticsearch for log analysis
  - Provides tools: `list_indices`, `get_mappings`, `search`, `esql`, `get_shards`

### 2.5 Configuration

- **File**: `config.yaml`
- **Contents**:
  - Model settings (LLM selection)
  - DevOps tool configurations (API keys, endpoints)
  - Agent behavior settings
  - MCP connection parameters
  - Elasticsearch connection settings

## 3. Data Flow

1. **User Request**: User submits a DevOps task to the assistant
2. **Orchestration**: Root agent analyzes the request and determines the appropriate agent
3. **Task Execution**:
   - For simple tasks: Direct execution by tool agents
   - For complex workflows: Transfer to specialized sub-agents
4. **Tool Usage**: Agents use custom tools or MCP tools to interact with DevOps systems
5. **Response Generation**: Agents process results and generate responses
6. **User Response**: Final response is returned to the user

## 4. Key Design Principles

1. **Modularity**: Each agent has a single, well-defined responsibility
2. **Extensibility**: Easy to add new agents and tools
3. **Reusability**: Simple agents can be reused across different workflows
4. **Configuration-Driven**: Behavior controlled through config files
5. **Observability**: Comprehensive logging and monitoring
6. **Security**: Secure handling of credentials and API keys

## 5. Implementation Approach

1. **Base Agent Class**: Extend your existing `BaseAgent` class for common functionality
2. **Configuration Management**: Use YAML config similar to your existing setup
3. **Tool Development**: Implement custom tools using `FunctionTool` wrapper
4. **MCP Integration**: Use `MCPToolset` for connecting to external systems
5. **Testing**: Develop unit tests for each agent and tool
6. **Documentation**: Provide clear documentation for each component

## 6. Elasticsearch Integration Details

### 6.1 Elasticsearch MCP Server
The Elasticsearch agent connects to an Elasticsearch MCP server that provides the following tools:
- `list_indices`: List all available Elasticsearch indices
- `get_mappings`: Get field mappings for a specific Elasticsearch index
- `search`: Perform an Elasticsearch search with the provided query DSL
- `esql`: Perform an ES|QL query
- `get_shards`: Get shard information for all or specific indices

### 6.2 Connection Setup
The agent connects to the Elasticsearch MCP server via Docker stdio connection, passing:
- Elasticsearch URL
- Authentication credentials (username/password or API key)
- Optional SSL settings

### 6.3 Usage Patterns
1. **Index Discovery**: Use `list_indices` to find relevant log indices
2. **Schema Understanding**: Use `get_mappings` to understand log structure
3. **Data Querying**: Use `search` or `esql` to retrieve log data
4. **Analysis**: Interpret results and provide insights to the user