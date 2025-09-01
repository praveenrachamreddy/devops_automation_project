# Scripts Directory

This directory contains utility scripts for setting up and running the DevOps Automation Assistant.

## Available Scripts

### ensure_elasticsearch_image.sh / ensure_elasticsearch_image.bat
Ensures that the Elasticsearch MCP Docker image is available locally before starting the ADK web interface.

**Usage (Linux/Mac):**
```bash
./scripts/ensure_elasticsearch_image.sh
```

**Usage (Windows):**
```cmd
scripts\ensure_elasticsearch_image.bat
```

### start_elasticsearch_mcp.sh / start_elasticsearch_mcp.bat
Starts the Elasticsearch MCP server in HTTP mode using podman.

**Usage (Linux/Mac):**
```bash
./scripts/start_elasticsearch_mcp.sh
```

**Usage (Windows):**
```cmd
scripts\start_elasticsearch_mcp.bat
```

This script will:
1. Stop any existing elasticsearch-mcp container
2. Start a new container with the Elasticsearch MCP server
3. Configure it to connect to your Elasticsearch instance
4. Expose the MCP server on port 8080

## Running the DevOps Automation Assistant

1. First, ensure the Elasticsearch MCP image is available:
   ```bash
   ./scripts/ensure_elasticsearch_image.sh
   ```

2. Start the Elasticsearch MCP server:
   ```bash
   ./scripts/start_elasticsearch_mcp.sh
   ```

3. Then start the ADK web interface:
   ```bash
   adk web
   ```