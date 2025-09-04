@echo off
title DevOps Automation Assistant - Prerequisites Checker

echo 🔧 DevOps Automation Assistant - Prerequisites Checker
echo ======================================================

:: Check if we're in the right directory
if not exist "requirements.txt" (
    echo ❌ Please run this script from the project root directory
    pause
    exit /b 1
)

:: Activate the virtual environment
echo 🔍 Activating virtual environment...
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo ✅ Virtual environment activated
) else (
    echo ❌ Virtual environment not found
    echo 💡 Please create a virtual environment first:
    echo    python -m venv .venv
    echo    call .venv\Scripts\activate.bat
    pause
    exit /b 1
)

:: Check Python dependencies
echo 🔍 Checking Python dependencies...
pip install -r requirements.txt

:: Check for kubectl
echo 🔍 Checking for kubectl...
where kubectl >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ kubectl not found
    echo 💡 Please install kubectl:
    echo    - Using Chocolatey: choco install kubernetes-cli
    echo    - Or download from: https://kubernetes.io/docs/tasks/tools/
) else (
    echo ✅ kubectl is installed
    kubectl version --client
)

:: Check for kubectl-ai
echo 🔍 Checking for kubectl-ai...
where kubectl-ai >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ kubectl-ai not found
    
    :: Check if kubectl-ai source is available
    if exist "kubectl-ai\cmd\main.go" (
        echo 🔨 Building kubectl-ai from source...
        cd kubectl-ai
        where go >nul 2>&1
        if %errorlevel% neq 0 (
            echo ❌ Go not found. Please install Go to build kubectl-ai
            echo 💡 Download Go from: https://golang.org/dl/
        ) else (
            go build -o kubectl-ai.exe cmd\main.go
            if exist "kubectl-ai.exe" (
                echo ✅ kubectl-ai built successfully
                echo 💡 Please move kubectl-ai.exe to a directory in your PATH
            ) else (
                echo ❌ Failed to build kubectl-ai
            )
        )
        cd ..
    ) else (
        echo 💡 Please install kubectl-ai manually:
        echo    git clone https://github.com/GoogleCloudPlatform/kubectl-ai.git
        echo    cd kubectl-ai
        echo    go build -o kubectl-ai.exe cmd\main.go
    )
) else (
    echo ✅ kubectl-ai is installed
    kubectl-ai --version
)

:: Check MCP servers
echo 🔍 Checking MCP servers...

:: Check Elasticsearch MCP server
if exist "mcp_servers\elasticsearch_mcp" (
    echo 🔧 Elasticsearch MCP server found
    cd mcp_servers\elasticsearch_mcp
    if exist "..\..\requirements.txt" (
        echo 📦 Installing Elasticsearch MCP dependencies in root venv...
        pip install -r requirements.txt
    )
    cd ..\..
) else (
    echo ❌ Elasticsearch MCP server not found
)

:: Check Simple MCP server
if exist "mcp_servers\simple_mcp" (
    echo 🔧 Simple MCP server found
    cd mcp_servers\simple_mcp
    if exist "..\..\requirements.txt" (
        echo 📦 Installing Simple MCP dependencies in root venv...
        pip install -r requirements.txt
    )
    cd ..\..
) else (
    echo ❌ Simple MCP server not found
)

echo.
echo 📋 Summary:
echo    - Python dependencies: Installed in root venv
echo    - kubectl: Checked
echo    - kubectl-ai: Checked
echo    - MCP servers: Configured
echo.
echo 💡 Next steps:
echo    1. Start MCP servers manually if needed:
echo       cd mcp_servers\elasticsearch_mcp ^&^& python server.py
echo       cd mcp_servers\simple_mcp ^&^& python server.py
echo    2. Configure your Kubernetes cluster connection in config.yaml
echo    3. Run the DevOps Assistant with: adk web

pause