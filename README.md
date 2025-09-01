# DevOps Automation Assistant

A comprehensive DevOps assistant built with the Google Agent Development Kit (ADK), featuring modular architecture, custom tools, and Model Context Protocol (MCP) integration.

## Project Overview

This repository contains a complete, production-ready agentic system built with the Google Agent Development Kit (ADK) for DevOps automation tasks. It demonstrates best practices for creating modular, extensible agents with custom tools and external system integration.

### Key Features

1. **Modular Architecture**: Clean separation of concerns with a base agent class and specialized sub-agents
2. **Custom Tools**: Implementation of custom tools with the FunctionTool wrapper
3. **MCP Integration**: Integration with the Model Context Protocol for external system interaction
4. **Extensibility**: Clear patterns for adding new agents and tools
5. **Testing**: Comprehensive test suite for verifying functionality
6. **Documentation**: Detailed documentation for understanding and extending the system

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
│   │       ├── cicd_agent.py      # CI/CD agent (TODO)
│   │       ├── infrastructure_agent.py  # Infrastructure agent (TODO)
│   │       ├── monitoring_agent.py      # Monitoring agent (TODO)
│   │       └── deployment_agent.py      # Deployment agent (TODO)
│   ├── tools/                # Custom tools
│   │   └── session_tools.py  # Session management tools
│   └── shared/               # Shared utilities
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
1. Ensure Docker is installed and running:
   ```bash
   systemctl status docker
   # If not running:
   sudo systemctl start docker
   ```

2. Ensure the Elasticsearch MCP Docker image is available (see scripts/README.md):
   ```bash
   # On Linux/Mac:
   ./scripts/ensure_elasticsearch_image.sh
   
   # On Windows:
   scripts\ensure_elasticsearch_image.bat
   ```

3. Start the ADK web interface:
   ```bash
   adk web
   ```

4. Open your browser to the provided URL
5. Select the DevOpsOrchestratorAgent from the dropdown menu

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

## Agent Descriptions

### DevOpsOrchestratorAgent (Main Orchestrator)
A master orchestrator that intelligently delegates tasks. It uses SearchAgent, CodingAgent, and ElasticsearchAgent as direct tools for simple tasks.

**Example prompts:**
- "Search for best practices for Kubernetes deployments"
- "Calculate the number of servers needed for 1000 concurrent users"
- "Analyze the error logs from the last 24 hours"

### SearchAgent (Search Specialist)
Specialized agent for web searches.

**Example prompts:**
- "Search for CI/CD tools comparison"
- "Find documentation for Terraform AWS provider"

### CodingAgent (Coding Specialist)
Specialized agent for executing code, math calculations, and logic operations.

**Example prompts:**
- "Calculate 2 to the power of 16"
- "Write a Python script to parse JSON data"

### ElasticsearchAgent (Log Analysis Specialist)
Specialized agent for analyzing logs stored in Elasticsearch using the Elasticsearch MCP server.

**Example prompts:**
- "Show me error logs from the application index"
- "Find the most common error messages in the logs"
- "Analyze the response time patterns in the web server logs"

## Architecture Details

The system follows a modular architecture as detailed in [architecture.md](architecture.md).

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

The DevOps Automation Assistant includes an ElasticsearchAgent that connects to an Elasticsearch MCP server for log analysis.

### Prerequisites
1. Running Elasticsearch instance (version 8.x or 9.x)
2. Docker (to run the Elasticsearch MCP server)

### Setup
1. Ensure Docker is running:
   ```bash
   systemctl status docker
   # If not running:
   sudo systemctl start docker
   ```

2. Run the utility script to ensure the Elasticsearch MCP image is available:
   ```bash
   # On Linux/Mac:
   ./scripts/ensure_elasticsearch_image.sh
   
   # On Windows:
   scripts\ensure_elasticsearch_image.bat
   ```

3. Update the Elasticsearch settings in `config.yaml` with your Elasticsearch connection details.

### Usage
The ElasticsearchAgent provides access to these tools:
- `list_indices`: List all available Elasticsearch indices
- `get_mappings`: Get field mappings for a specific Elasticsearch index
- `search`: Perform an Elasticsearch search with the provided query DSL
- `esql`: Perform an ES|QL query
- `get_shards`: Get shard information for all or specific indices

The Elasticsearch MCP server Docker image will be automatically downloaded when the agent is first used.

## Testing

Run tests from the project root:
```bash
cd testing
python test_imports.py
```

## Troubleshooting

### Common Issues
1. **Async event loop errors**: This is a known ADK compatibility issue on Windows
2. **Missing environment variables**: Ensure `.env` is properly configured
3. **Agent not appearing in UI**: Check that `root_agent` is properly exported
4. **MCP server connection issues**: Verify Elasticsearch MCP server is running and accessible
5. **Docker image pull timeouts**: Run the utility scripts to ensure images are available locally

### Solutions
1. Use ADK web interface instead of programmatic access for better compatibility
2. Verify all required environment variables are set
3. Ensure only one agent is exported as `root_agent` in `agent.py`
4. Check that Docker is running and accessible
5. Run the utility scripts in the `scripts/` directory to ensure Docker images are available locally

## Next Steps

The system is ready for immediate use and extension:
1. Implement the specialized DevOps agents (CI/CD, Infrastructure, Monitoring, Deployment)
2. Add custom tools for specific DevOps tasks
3. Deploy agents to Vertex AI Agent Engine using scripts in `deployment/`