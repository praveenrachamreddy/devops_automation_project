#!/bin/bash
# Script to start the Elasticsearch MCP server using podman

echo "Starting Elasticsearch MCP server..."

# Stop any existing container
podman stop elasticsearch-mcp 2>/dev/null
podman rm elasticsearch-mcp 2>/dev/null

# Start the Elasticsearch MCP server container
podman run -d \
  --name elasticsearch-mcp \
  -e ES_URL=https://praveen.elkserver.imss.com:9200 \
  -e ES_USERNAME=elastic \
  -e ES_PASSWORD=hlLWmR*tnDVMKkvR80ws \
  -e ES_SSL_SKIP_VERIFY=true \
  docker.elastic.co/mcp/elasticsearch:0.4.0

if [ $? -eq 0 ]; then
    echo "✅ Elasticsearch MCP server container started successfully"
    echo "Container is running in background"
    echo "Use 'podman logs -f elasticsearch-mcp' to view logs"
else
    echo "❌ Failed to start Elasticsearch MCP server container"
    exit 1
fi