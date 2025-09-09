@echo off
title MCP Server Starter

echo =================================================================
echo  Starting all Model Context Protocol (MCP) Servers in parallel...
echo =================================================================
echo.
echo Each server will open in a new terminal window.
echo Please keep these windows open.
echo.

REM Get the directory of the batch script so this can be run from anywhere
set SCRIPT_DIR=%~dp0

REM --- Start Simple MCP Server (Currency) ---
echo Starting Simple MCP Server on port 8080...
start "Simple MCP (Port 8080)" cmd /c "cd /d %SCRIPT_DIR%..\mcp_servers\simple_mcp && python server.py"

REM --- Start Elasticsearch MCP Server ---
echo Starting Elasticsearch MCP Server on port 8081...
start "Elasticsearch MCP (Port 8081)" cmd /c "cd /d %SCRIPT_DIR%..\mcp_servers\elasticsearch_mcp && python server.py"

REM --- Start Kubectl-AI MCP Server ---
echo Starting Kubectl-AI MCP Server on port 8082...
start "Kubectl-AI MCP (Port 8082)" cmd /c "cd /d %SCRIPT_DIR%..\mcp_servers\kubectl-ai_mcp && python server.py"

REM --- Start Thanos MCP Server ---
echo Starting Thanos MCP Server on port 8083...
start "Thanos MCP (Port 8083)" cmd /c "cd /d %SCRIPT_DIR%..\mcp_servers\thanos_mcp && python server.py"

echo.
echo =================================================================
echo  All MCP servers have been launched.
echo =================================================================
echo.
pause
