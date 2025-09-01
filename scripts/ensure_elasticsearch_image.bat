@echo off
REM Script to ensure Elasticsearch MCP Docker image is available locally

set IMAGE_NAME=docker.elastic.co/mcp/elasticsearch:0.4.0

echo Checking if Elasticsearch MCP Docker image is available locally...

REM Check if image exists locally
docker images | findstr "docker.elastic.co/mcp/elasticsearch.*0.4.0" >nul

if %errorlevel% == 0 (
    echo ✅ Elasticsearch MCP Docker image is already available locally
) else (
    echo 🔄 Elasticsearch MCP Docker image not found locally, pulling...
    docker pull %IMAGE_NAME%
    
    if %errorlevel% == 0 (
        echo ✅ Successfully pulled Elasticsearch MCP Docker image
    ) else (
        echo ❌ Failed to pull Elasticsearch MCP Docker image
        exit /b 1
    )
)

echo Ready to start ADK web interface