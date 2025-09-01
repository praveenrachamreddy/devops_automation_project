#!/bin/bash
# Script to start the Elasticsearch MCP server using podman

echo "Starting Elasticsearch MCP server..."

# Stop any existing container
podman stop elasticsearch-mcp 2>/dev/null
podman rm elasticsearch-mcp 2>/dev/null

# Start the Elasticsearch MCP server
podman run -d \
  --name elasticsearch-mcp \
  -e ES_URL=https://praveen.elkserver.imss.com:9200 \
  -e ES_USERNAME=elastic \
  -e ES_PASSWORD=hlLWmR*tnDVMKkvR80ws \
  -e ES_SSL_SKIP_VERIFY=true \
  -p 8080:8080 \
  docker.elastic.co/mcp/elasticsearch:0.4.0 http

if [ $? -eq 0 ]; then
    echo "✅ Elasticsearch MCP server started successfully"
    echo "Server is running on http://localhost:8080"
    echo "Use 'podman logs -f elasticsearch-mcp' to view logs"
else
    echo "❌ Failed to start Elasticsearch MCP server"
    exit 1
fi