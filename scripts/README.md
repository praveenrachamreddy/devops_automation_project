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

This script will:
1. Check if the `docker.elastic.co/mcp/elasticsearch:0.4.0` image is available locally
2. If not found, it will pull the image from Docker Hub
3. Confirm when the image is ready for use

## Running the DevOps Automation Assistant

1. First, ensure the Elasticsearch MCP image is available:
   ```bash
   ./scripts/ensure_elasticsearch_image.sh
   ```

2. Then start the ADK web interface:
   ```bash
   adk web
   ```