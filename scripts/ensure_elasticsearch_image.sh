#!/bin/bash
# Script to ensure Elasticsearch MCP Docker image is available locally

IMAGE_NAME="docker.elastic.co/mcp/elasticsearch:0.4.0"

echo "Checking if Elasticsearch MCP Docker image is available locally..."

# Check if image exists locally
if docker images | grep -q "docker.elastic.co/mcp/elasticsearch.*0.4.0"; then
    echo "✅ Elasticsearch MCP Docker image is already available locally"
else
    echo "🔄 Elasticsearch MCP Docker image not found locally, pulling..."
    docker pull $IMAGE_NAME
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully pulled Elasticsearch MCP Docker image"
    else
        echo "❌ Failed to pull Elasticsearch MCP Docker image"
        exit 1
    fi
fi

echo "Ready to start ADK web interface"