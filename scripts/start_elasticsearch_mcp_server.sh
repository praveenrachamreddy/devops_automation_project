#!/bin/bash
# Script to start Elasticsearch MCP server in HTTP mode

echo "Starting Elasticsearch MCP server in HTTP mode..."

# Run the Elasticsearch MCP server in HTTP mode
docker run -d --name elasticsearch-mcp-server \
  -e ES_URL=https://praveen.elkserver.imss.com:9200 \
  -e ES_USERNAME=elastic \
  -e ES_PASSWORD=hlLWmR*tnDVMKkvR80ws \
  -p 8080:8080 \
  docker.elastic.co/mcp/elasticsearch:0.4.0 http

echo "Elasticsearch MCP server started on http://localhost:8080"
echo "Use 'docker logs elasticsearch-mcp-server' to check the server logs"