# DevOps Automation Assistant

A comprehensive DevOps assistant built with the Google Agent Development Kit (ADK), featuring modular architecture, custom tools, and Model Context Protocol (MCP) integration.

## Project Overview

This repository contains a complete, production-ready agentic system built with the Google Agent Development Kit (ADK) for DevOps automation tasks. It demonstrates best practices for creating modular, extensible agents with custom tools and external system integration.

### Key Features

1. **Modular Architecture**: Clean separation of concerns with a base agent class and specialized sub-agents
2. **Custom Tools**: Implementation of custom tools with the FunctionTool wrapper
3. **MCP Integration**: Integration with the Model Context Protocol for external system interaction
4. **Sub-Agent Transfer**: Intelligent delegation to specialized agents for complex tasks
5. **Extensibility**: Clear patterns for adding new agents and tools
6. **Testing**: Comprehensive test suite for verifying functionality
7. **Documentation**: Detailed documentation for understanding and extending the system

## Project Structure

```
devops_automation_project/
├── devops_agent_system/        # Main agent system code
│   ├── __init__.py           # Package initialization
│   ├── agent.py              # Main orchestrator and agent switching
│   ├── agents/               # Agent implementations
│   │   ├── base_agent.py     # Base agent abstract class
│   │   └── sub_agents/       # Specialized agents
│   │       ├── search_agent.py    # Search agent
│   │       ├── coding_agent.py    # Coding agent
│   │       ├── elasticsearch_agent.py  # Elasticsearch log analysis agent
│   │       ├── simple_mcp_agent.py    # Simple MCP currency conversion agent
│   │       ├── kubectl_ai_agent.py    # Kubernetes/OpenShift operations agent
│   │       ├── cicd_agent.py      # CI/CD agent (TODO)
│   │       ├── infrastructure_agent.py  # Infrastructure agent (TODO)
│   │       ├── monitoring_agent.py      # Monitoring agent (TODO)
│   │       └── deployment_agent.py      # Deployment agent (TODO)
│   ├── tools/                # Custom tools
│   └── shared/               # Shared utilities
├── mcp_servers/              # MCP server implementations
│   ├── elasticsearch_mcp/    # Elasticsearch MCP server
│   │   ├── server.py         # Elasticsearch MCP server implementation
│   │   ├── requirements.txt  # Server dependencies
│   │   ├── .env.example      # Example environment configuration
│   │   ├── README.md         # Server documentation
│   │   └── __init__.py       # Package initialization
│   ├── simple_mcp/           # Simple currency conversion MCP server
│   │   ├── server.py         # Simple MCP server implementation
│   │   ├── requirements.txt  # Server dependencies
│   │   └── README.md         # Server documentation
│   ├── kubectl-ai_mcp/       # Kubernetes/OpenShift MCP server
│   │   ├── server.py         # Kubernetes/OpenShift MCP server implementation
│   │   ├── kubernetes_manager.py  # Kubernetes connection manager
│   │   ├── requirements.txt  # Server dependencies
│   │   ├── README.md         # Server documentation
│   │   └── __init__.py       # Package initialization
│   └── thanos_mcp/           # Thanos monitoring MCP server
│       ├── server.py         # Thanos MCP server implementation
│       ├── thanos_manager.py # Thanos connection manager
│       ├── requirements.txt  # Server dependencies
│       ├── README.md         # Server documentation
│       └── __init__.py       # Package initialization
├── frontend/                 # React frontend application
├── scripts/                  # Utility scripts
├── testing/                  # Test scripts and verification tools
├── deployment/               # Deployment configurations
├── docs/                     # Documentation
├── tests/                    # Unit tests
├── eval/                     # Evaluation scripts
├── .env.example             # Environment variables template
├── config.yaml              # System configuration
├── pyproject.toml           # Project dependencies (Poetry)
├── requirements.txt         # Project dependencies (pip)
├── README.md                # Project documentation
├── architecture.md          # System architecture
└── run_agent.py             # Example runner script

## Getting Started

### Prerequisites

1. Python 3.10 or higher
2. pip package manager
3. Google Cloud account or Google Gemini API key
4. Docker (for Elasticsearch MCP server)
5. OpenShift CLI (oc) installed and available in PATH

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/praveenrachamreddy/devops_automation_project.git
   cd devops_automation_project
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and configure your environment variables:
   ```bash
   cp .env.example .env
   ```
   
   Edit the `.env` file with a text editor and add your credentials:
   - For Vertex AI: Set `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION`
   - For Gemini API: Set `GOOGLE_API_KEY` and `GOOGLE_GENAI_USE_VERTEXAI=false`

## Using the System

### Method 1: ADK Web Interface (Recommended)
1. Ensure the MCP servers are running (see MCP Servers section below)

2. Start the ADK web interface:
   ```bash
   adk web
   ```

3. Open your browser to the provided URL
4. Select the DevOpsOrchestratorAgent from the dropdown menu

### Method 2: ADK CLI
Run the agent directly from command line:
```bash
adk run devops_agent_system
```

### Method 3: Programmatic Access
Run the example script:
```bash
python run_agent.py
```

## MCP Servers

The DevOps Automation Assistant includes three MCP (Model Context Protocol) servers that provide external tool integration:

### 1. Simple MCP Server (Currency Conversion)
A simple MCP server that provides currency conversion tools using the Frankfurter API.

**Features:**
- `get_exchange_rate`: Get current exchange rates
- `list_currencies`: List all available currencies
- `convert_amount`: Convert a specific amount between currencies

**To run:**
```bash
cd mcp_servers/simple_mcp
pip install -r requirements.txt
python server.py
```

**Default URL:** http://localhost:8080/mcp

### 2. Elasticsearch MCP Server (Log Analysis)
An MCP server that provides tools for interacting with Elasticsearch for log analysis.

**Features:**
- `test_connection`: Test the connection to Elasticsearch
- `list_indices`: List all available Elasticsearch indices
- `get_mappings`: Get field mappings for a specific Elasticsearch index
- `search`: Perform an Elasticsearch search with the provided query DSL
- `esql`: Perform an ES|QL query
- `get_shards`: Get shard information for all or specific indices

**To run:**
```bash
cd mcp_servers/elasticsearch_mcp
pip install -r requirements.txt
# Copy and configure .env file:
cp .env.example .env
# Edit .env with your Elasticsearch settings
python server.py
```

**Default URL:** http://localhost:8081/mcp

### 3. Kubernetes/OpenShift MCP Server (Cluster Operations)
An MCP server that provides tools for interacting with Kubernetes/OpenShift clusters using the `oc` CLI.

**Features:**
- `oc`: Execute OpenShift CLI (oc) commands to manage OpenShift clusters
- `bash`: Execute bash commands for system operations

**To run:**
```bash
cd mcp_servers/kubectl-ai_mcp
pip install -r requirements.txt
python server.py
```

**Default URL:** http://localhost:8082/mcp

### 4. Thanos Monitoring MCP Server (Metrics Analysis)
An MCP server that provides tools for querying and analyzing metrics from Thanos/Prometheus monitoring systems.

**Features:**
- `query_metric`: Execute PromQL queries against Thanos
- `query_range`: Execute range queries for time-series data
- `list_metrics`: List available metrics in the Thanos instance
- `get_metric_metadata`: Get metadata and help text for specific metrics
- `explore_labels`: Explore label names and values for metrics
- `analyze_trends`: Analyze trends and patterns in metric data

**To run:**
```bash
cd mcp_servers/thanos_mcp
pip install -r requirements.txt
python server.py
```

**Default URL:** http://localhost:8083/mcp

## Agent Architecture

### DevOpsOrchestratorAgent (Main Orchestrator)
A master orchestrator that intelligently delegates tasks using two different patterns:

1. **Tool Pattern**: For simple, quick tasks
   - SearchAgent (web searches)
   - CodingAgent (math, logic, code execution)

2. **Sub-Agent Transfer Pattern**: For specialized, complex tasks
   - ElasticsearchAgent (log analysis) - transferred when user asks about Elasticsearch
   - SimpleMCPAgent (currency conversion) - transferred when user asks about currency
   - KubectlAIAgent (Kubernetes/OpenShift operations) - transferred when user asks about cluster operations
   - MonitoringAgent (metrics analysis) - transferred when user asks about monitoring or metrics
   - CI/CD, Infrastructure, Deployment agents (TODO) - for future expansion

**Example prompts:**
- "Search for best practices for Kubernetes deployments"
- "Calculate the number of servers needed for 1000 concurrent users"
- "List all Elasticsearch indices"
- "What is the exchange rate from USD to EUR?"
- "Show me all pods in my OpenShift cluster"
- "Deploy a new application to my cluster"
- "Show CPU usage trends for the past 24 hours"
- "Are there any memory leaks in my application?"
- "What's the current request rate for my API?"

### SearchAgent (Search Specialist)
Specialized agent for web searches, available as a tool.

**Example prompts:**
- "Search for CI/CD tools comparison"
- "Find documentation for Terraform AWS provider"

### CodingAgent (Coding Specialist)
Specialized agent for executing code, math calculations, and logic operations, available as a tool.

**Example prompts:**
- "Calculate 2 to the power of 16"
- "Write a Python script to parse JSON data"

### ElasticsearchAgent (Log Analysis Specialist)
Specialized agent for analyzing logs stored in Elasticsearch, available as a sub-agent for transfer.

**Example prompts:**
- "List all Elasticsearch indices"
- "Show me error logs from the application index"
- "Find the most common error messages in the logs"
- "Analyze the response time patterns in the web server logs"

### SimpleMCPAgent (Currency Conversion Specialist)
Specialized agent for currency conversions using the Simple MCP server, available as a sub-agent for transfer.

**Example prompts:**
- "What is the exchange rate from USD to EUR?"
- "Convert 100 USD to GBP"
- "How much is 50 EUR in USD?"

### KubectlAIAgent (Kubernetes/OpenShift Operations Specialist)
Specialized agent for managing Kubernetes/OpenShift clusters using the kubectl-ai MCP server, available as a sub-agent for transfer.

**Features:**
- Execute `oc` commands to manage OpenShift resources
- Execute bash commands for system operations
- Understand OpenShift-specific concepts like projects, DeploymentConfigs, Routes, etc.
- Follow best practices for resource creation and management

**Example prompts:**
- "Show me all pods in my cluster"
- "Describe the nginx deployment"
- "Get logs from the database pod"
- "Scale the frontend deployment to 3 replicas"
- "Create a new project called 'development'"
- "Expose the web service as a route"

### MonitoringAgent (Metrics Analysis Specialist)
Specialized agent for monitoring and analyzing system metrics using the Thanos MCP server, available as a sub-agent for transfer.

**Features:**
- Query metrics from Thanos using PromQL
- Analyze performance trends and patterns
- Identify anomalies and performance issues
- Provide capacity planning recommendations
- Help with alerting and monitoring setup

**Example prompts:**
- "Show CPU usage for all pods in the production namespace"
- "What's the memory consumption trend for the database service?"
- "Are there any network issues affecting the web frontend?"
- "How many requests per second is the API handling?"
- "Are there any pods crashing or restarting frequently?"
- "What's the disk usage pattern for persistent volumes?"
- "Analyze the response time trends for the past week"
- "Identify any anomalies in system metrics"

## Architecture Details

The system follows a modular architecture as detailed in [architecture.md](architecture.md). The key architectural decisions are:

1. **Hybrid Orchestration**: Uses both tool delegation and sub-agent transfer
2. **MCP Integration**: Connects to external systems via MCP servers
3. **Modular Design**: Each agent has a single, well-defined responsibility
4. **Extensible Framework**: Easy to add new agents and tools

## Extending the System

### Adding New Agents
1. Create a new file in `devops_agent_system/agents/sub_agents/`
2. Inherit from `BaseAgent`
3. Implement required methods:
   - `__init__`: Initialize with name and description
   - `get_system_prompt`: Return agent instructions
   - `create_agent`: Return configured ADK Agent
4. Register in the main orchestrator

### Adding New Tools
1. Add functions to `devops_agent_system/tools/`
2. Register them in an agent's `get_tools()` method
3. Use `FunctionTool` wrapper for ADK compatibility

## Elasticsearch Integration

The DevOps Automation Assistant includes an ElasticsearchAgent that connects to an Elasticsearch MCP server for log analysis. The MCP server is implemented as part of this project and runs as a separate HTTP service.

### Prerequisites
1. Running Elasticsearch instance (version 7.x or 8.x)
2. Python dependencies installed (elasticsearch library)

### Setup
1. Install the required dependencies:
   ```bash
   pip install -r mcp_servers/elasticsearch_mcp/requirements.txt
   ```

2. Copy the `.env.example` file to `.env` and configure your Elasticsearch connection settings:
   ```bash
   cd mcp_servers/elasticsearch_mcp
   cp .env.example .env
   ```
   
3. Edit the `.env` file in `mcp_servers/elasticsearch_mcp/` to match your Elasticsearch configuration.

4. The Elasticsearch settings in `config.yaml` are used by the MCP server for connection details.

### Usage
The ElasticsearchAgent provides access to these tools:
- `test_connection`: Test the connection to Elasticsearch
- `list_indices`: List all available Elasticsearch indices
- `get_mappings`: Get field mappings for a specific Elasticsearch index
- `search`: Perform an Elasticsearch search with the provided query DSL
- `esql`: Perform an ES|QL query
- `get_shards`: Get shard information for all or specific indices

The Elasticsearch MCP server is implemented as part of this project and runs as a separate HTTP service when started.

## Kubernetes/OpenShift Integration

The DevOps Automation Assistant includes a KubectlAIAgent that connects to a Kubernetes/OpenShift MCP server for cluster operations. The MCP server is implemented as part of this project and runs as a separate HTTP service.

### Prerequisites
1. OpenShift CLI (`oc`) installed and available in PATH
2. Access to an OpenShift cluster with valid credentials
3. Python dependencies installed

### Setup
1. Install the required dependencies:
   ```bash
   pip install -r mcp_servers/kubectl-ai_mcp/requirements.txt
   ```

2. Configure your OpenShift connection settings in `config.yaml`:
   ```yaml
   devops_settings:
     kubernetes:
       # Cluster connection settings
       api_url: "https://api.ocp4.imss.work:6443"
       username: "ocpadmin"
       password: "oShift@123"
       token: "sha256~F4ixBQBun-4atLkIdNlTsp-4NOpTe_SPftvasIuuN8Q"
       kubeconfig_path: "~/.kube/config"
   ```

3. The Kubernetes/OpenShift settings in `config.yaml` are used by the MCP server for connection details.

### Usage
The KubectlAIAgent provides access to these tools:
- `oc`: Execute OpenShift CLI (oc) commands to manage cluster resources
- `bash`: Execute bash commands for system operations

The Kubernetes/OpenShift MCP server is implemented as part of this project and runs as a separate HTTP service when started.

**Example commands the agent can execute:**
- `oc get pods --all-namespaces`
- `oc describe deployment my-app`
- `oc logs pod/my-pod -c container-name`
- `oc get projects`
- `oc create project new-project`
- `oc scale deployment/my-app --replicas=3`

## Thanos Monitoring Integration

The DevOps Automation Assistant includes a MonitoringAgent that connects to a Thanos MCP server for metrics querying and analysis. The MCP server is implemented as part of this project and runs as a separate HTTP service.

### Prerequisites
1. Access to a Thanos Query Frontend or Prometheus-compatible API
2. Valid authentication credentials (token or basic auth)
3. Python dependencies installed

### Setup
1. Install the required dependencies:
   ```bash
   pip install -r mcp_servers/thanos_mcp/requirements.txt
   ```

2. Configure your Thanos connection settings in `config.yaml`:
   ```yaml
   devops_settings:
     monitoring:
       # Thanos connection settings
       thanos_url: "http://thanos-query-frontend.monitoring.svc:9090"
       thanos_token: "sha256~your-thanos-token-here"
       ssl_verify: true
       timeout: 30
   ```

3. The monitoring settings in `config.yaml` are used by the MCP server for connection details.

### Usage
The MonitoringAgent provides access to these tools:
- `query_metric`: Execute instant PromQL queries for current metric values
- `query_range`: Execute range queries for historical metric data
- `list_metrics`: Discover available metrics in the system
- `get_metric_metadata`: Get detailed information about specific metrics
- `explore_labels`: Explore label names and values for metrics
- `analyze_trends`: Analyze trends and patterns in metric data

The Thanos MCP server is implemented as part of this project and runs as a separate HTTP service when started.

**Example queries the agent can execute:**
- `rate(container_cpu_usage_seconds_total[5m])`
- `container_memory_usage_bytes{namespace="production"}`
- `sum(rate(http_requests_total[5m])) by (job)`
- `up == 0` (find down targets)
- Historical analysis of resource usage patterns

## Testing

Run tests from the project root:
```bash
cd testing
python test_imports.py
```

## Troubleshooting

### Common Issues
1. **Async event loop errors**: This is a known ADK compatibility issue on Windows
2. **Missing environment variables**: Ensure `.env` is properly configured in the `mcp_servers/elasticsearch_mcp/` directory
3. **Agent not appearing in UI**: Check that `root_agent` is properly exported
4. **MCP server connection issues**: Verify Elasticsearch is running and accessible, and check the MCP server logs
5. **Python dependency issues**: Ensure all required dependencies are installed
6. **Version compatibility issues**: Ensure Elasticsearch client version matches server version
7. **Kubernetes/OpenShift connection issues**: Verify `oc` CLI is installed and cluster credentials are valid
8. **Thanos connection issues**: Verify Thanos Query Frontend is accessible and authentication is correct

### Solutions
1. Use ADK web interface instead of programmatic access for better compatibility
2. Verify all required environment variables are set in `mcp_servers/elasticsearch_mcp/.env`
3. Ensure only one agent is exported as `root_agent` in `agent.py`
4. Check that Elasticsearch is running and accessible with the provided credentials
5. Check the MCP server logs for detailed error information
6. Ensure Elasticsearch client version is compatible with server version (7.x or 8.x)
7. Verify `oc` CLI is in PATH and `config.yaml` contains valid cluster connection details
8. Verify Thanos URL and authentication token in `config.yaml` and check network connectivity

## Next Steps

The system is ready for immediate use and extension:
1. Implement the specialized DevOps agents (CI/CD, Infrastructure, Monitoring, Deployment)
2. Add custom tools for specific DevOps tasks
3. Deploy agents to Vertex AI Agent Engine using scripts in `deployment/`