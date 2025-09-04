# DevOps Automation Assistant Architecture

## 1. High-Level Architecture Overview

```
DevOps Automation Assistant
├── Orchestrator Agent (Root)
│   ├── Simple Task Agents (as Tools)
│   │   ├── Search Agent
│   │   └── Coding Agent
│   └── Specialized Agents (as Sub-agents)
│       ├── Elasticsearch Agent
│       ├── Simple MCP Agent (Currency Conversion)
│       ├── CI/CD Pipeline Agent (TODO)
│       ├── Infrastructure Agent (TODO)
│       ├── Monitoring Agent (TODO)
│       └── Deployment Agent (TODO)
├── Custom Tools
│   ├── Search Tool
│   ├── Code Execution Tool
│   └── MCP Tools (Elasticsearch, Currency Conversion)
├── MCP Integration
│   ├── Elasticsearch MCP Server
│   └── Simple MCP Server (Currency Conversion)
└── Configuration
    └── config.yaml
```

## 2. Component Details

### 2.1 Orchestrator Agent (Root Agent)
- **Role**: Central decision maker that routes tasks to appropriate specialized agents
- **Implementation**: Uses hybrid orchestration model:
  - Simple tasks delegated via `AgentTool` pattern
  - Specialized tasks transferred via ADK's built-in transfer mechanism
- **Routing Logic**:
  - Search queries → Search Agent (tool)
  - Coding/math tasks → Coding Agent (tool)
  - Log analysis → Elasticsearch Agent (sub-agent transfer)
  - Currency conversion → Simple MCP Agent (sub-agent transfer)
  - CI/CD operations → CI/CD Pipeline Agent (sub-agent transfer)
  - Infrastructure provisioning → Infrastructure Agent (sub-agent transfer)
  - Monitoring tasks → Monitoring Agent (sub-agent transfer)
  - Deployment operations → Deployment Agent (sub-agent transfer)

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

#### 2.2.2 Specialized Agents (as Sub-agents)

- **Elasticsearch Agent**:
  - Purpose: Analyze logs stored in Elasticsearch
  - Tools: Elasticsearch MCP server tools
  - Implementation: Connects to Elasticsearch MCP server via HTTP
  - Transfer Pattern: When user asks about Elasticsearch logs, indices, or search queries

- **Simple MCP Agent (Currency Conversion)**:
  - Purpose: Handle currency conversion and exchange rate queries
  - Tools: Simple MCP server tools (Frankfurter API)
  - Implementation: Connects to Simple MCP server via HTTP
  - Transfer Pattern: When user asks about currency conversion or exchange rates

- **CI/CD Pipeline Agent** (TODO):
  - Purpose: Manage CI/CD pipeline operations
  - Capabilities:
    - Trigger builds
    - Monitor pipeline status
    - Retrieve pipeline logs
    - Handle pipeline failures

- **Infrastructure Agent** (TODO):
  - Purpose: Manage infrastructure provisioning and configuration
  - Capabilities:
    - Provision resources (VMs, containers, networks)
    - Configure infrastructure components
    - Manage infrastructure state

- **Monitoring Agent** (TODO):
  - Purpose: Monitor system health and performance
  - Capabilities:
    - Retrieve metrics from monitoring systems
    - Analyze system performance
    - Generate alerts based on thresholds

- **Deployment Agent** (TODO):
  - Purpose: Handle application deployments
  - Capabilities:
    - Deploy applications to various environments
    - Rollback deployments
    - Verify deployment status

### 2.3 Custom Tools

- **Search Tool**:
  - Integration with Google Search
  - Perform web searches
  - Retrieve search results

- **Code Execution Tool**:
  - Execute Python code snippets
  - Perform mathematical calculations
  - Handle logical operations

- **MCP Tools**:
  - **Elasticsearch MCP Tools**:
    - `test_connection`: Test connection to Elasticsearch
    - `list_indices`: List all available Elasticsearch indices
    - `get_mappings`: Get field mappings for a specific Elasticsearch index
    - `search`: Perform an Elasticsearch search with the provided query DSL
    - `esql`: Perform an ES|QL query
    - `get_shards`: Get shard information for all or specific indices
  - **Simple MCP Tools (Currency Conversion)**:
    - `get_exchange_rate`: Get current exchange rates
    - `list_currencies`: List all available currencies
    - `convert_amount`: Convert specific amounts between currencies

### 2.4 MCP Integration

- **Purpose**: Connect to external systems that expose MCP-compatible interfaces
- **Implementation**:
  - Use `MCPToolset` with `StreamableHTTPConnectionParams` to connect to MCP servers
  - Expose DevOps tools as MCP tools for external consumption
  - Support for HTTP transport mechanism
- **Elasticsearch MCP Server**:
  - Connects to Elasticsearch for log analysis
  - Provides tools: `test_connection`, `list_indices`, `get_mappings`, `search`, `esql`, `get_shards`
  - Runs as a separate HTTP service on port 8081
- **Simple MCP Server (Currency Conversion)**:
  - Connects to Frankfurter API for currency conversion
  - Provides tools: `get_exchange_rate`, `list_currencies`, `convert_amount`
  - Runs as a separate HTTP service on port 8080

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
3. **Routing Decision**:
   - For simple tasks: Direct execution by tool agents
   - For specialized tasks: Transfer to sub-agents
4. **Task Execution**:
   - Tool agents execute tasks directly
   - Sub-agents handle complex specialized workflows
5. **Tool Usage**: Agents use custom tools or MCP tools to interact with external systems
6. **Response Generation**: Agents process results and generate responses
7. **User Response**: Final response is returned to the user

## 4. Key Design Principles

1. **Modularity**: Each agent has a single, well-defined responsibility
2. **Extensibility**: Easy to add new agents and tools
3. **Reusability**: Simple agents can be reused across different workflows
4. **Configuration-Driven**: Behavior controlled through config files
5. **Observability**: Comprehensive logging and monitoring
6. **Security**: Secure handling of credentials and API keys

## 5. Implementation Approach

1. **Base Agent Class**: Extend the `BaseAgent` class for common functionality
2. **Configuration Management**: Use YAML config for settings
3. **Tool Development**: Implement custom tools using `FunctionTool` wrapper
4. **MCP Integration**: Use `MCPToolset` with `StreamableHTTPConnectionParams` for connecting to external systems
5. **Agent Transfer**: Use ADK's sub-agent transfer mechanism for specialized agents
6. **Testing**: Develop unit tests for each agent and tool
7. **Documentation**: Provide clear documentation for each component

## 6. Elasticsearch Integration Details

### 6.1 Elasticsearch MCP Server
The Elasticsearch agent connects to an Elasticsearch MCP server that provides the following tools:
- `test_connection`: Test the connection to Elasticsearch
- `list_indices`: List all available Elasticsearch indices
- `get_mappings`: Get field mappings for a specific Elasticsearch index
- `search`: Perform an Elasticsearch search with the provided query DSL
- `esql`: Perform an ES|QL query
- `get_shards`: Get shard information for all or specific indices

The MCP server is implemented as part of this project and runs as a separate HTTP service.

### 6.2 Connection Setup
The agent connects to the Elasticsearch MCP server via HTTP connection, using:
- Elasticsearch URL from environment variables
- Authentication credentials from environment variables
- Optional SSL settings from environment variables

### 6.3 Usage Patterns
1. **Connection Testing**: Use `test_connection` to verify Elasticsearch accessibility
2. **Index Discovery**: Use `list_indices` to find relevant log indices
3. **Schema Understanding**: Use `get_mappings` to understand log structure
4. **Data Querying**: Use `search` or `esql` to retrieve log data
5. **Analysis**: Interpret results and provide insights to the user

## 7. Simple MCP Integration Details

### 7.1 Simple MCP Server (Currency Conversion)
The Simple MCP agent connects to a Simple MCP server that provides the following tools:
- `get_exchange_rate`: Get current exchange rates between two currencies
- `list_currencies`: List all available currencies supported by the API
- `convert_amount`: Convert a specific amount from one currency to another

### 7.2 Connection Setup
The agent connects to the Simple MCP server via HTTP connection, using:
- Server URL from environment variables (default: http://localhost:8080/mcp)

### 7.3 Usage Patterns
1. **Exchange Rate Queries**: Use `get_exchange_rate` to get current rates
2. **Currency Discovery**: Use `list_currencies` to see available currencies
3. **Amount Conversion**: Use `convert_amount` to convert specific amounts