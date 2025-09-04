#!/bin/bash

# Prerequisites checker and installer for DevOps Automation Assistant

echo "🔧 DevOps Automation Assistant - Prerequisites Checker"
echo "======================================================"

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Check Python dependencies
echo "🔍 Checking Python dependencies..."
pip install -r requirements.txt

# Check for kubectl
echo "🔍 Checking for kubectl..."
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found"
    echo "💡 Please install kubectl:"
    echo "   - On Linux: curl -LO 'https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl'"
    echo "   - On macOS: brew install kubectl"
    echo "   - On Windows: choco install kubernetes-cli"
else
    echo "✅ kubectl is installed"
    kubectl version --client
fi

# Check for kubectl-ai
echo "🔍 Checking for kubectl-ai..."
if ! command -v kubectl-ai &> /dev/null; then
    echo "❌ kubectl-ai not found"
    
    # Check if kubectl-ai source is available
    if [ -d "kubectl-ai" ] && [ -f "kubectl-ai/cmd/main.go" ]; then
        echo "🔨 Building kubectl-ai from source..."
        cd kubectl-ai
        if command -v go &> /dev/null; then
            go build -o kubectl-ai cmd/main.go
            if [ -f "kubectl-ai" ]; then
                echo "✅ kubectl-ai built successfully"
                echo "💡 Please move kubectl-ai to a directory in your PATH:"
                echo "   sudo mv kubectl-ai /usr/local/bin/"
            else
                echo "❌ Failed to build kubectl-ai"
            fi
        else
            echo "❌ Go not found. Please install Go to build kubectl-ai"
        fi
        cd ..
    else
        echo "💡 Please install kubectl-ai manually:"
        echo "   git clone https://github.com/GoogleCloudPlatform/kubectl-ai.git"
        echo "   cd kubectl-ai && go build -o kubectl-ai cmd/main.go"
    fi
else
    echo "✅ kubectl-ai is installed"
    kubectl-ai --version
fi

# Check MCP servers
echo "🔍 Checking MCP servers..."

# Check Elasticsearch MCP server
if [ -d "mcp_servers/elasticsearch_mcp" ]; then
    echo "🔧 Elasticsearch MCP server found"
    cd mcp_servers/elasticsearch_mcp
    if [ ! -d "venv" ]; then
        echo "📦 Setting up Elasticsearch MCP virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        deactivate
    fi
    cd ../..
else
    echo "❌ Elasticsearch MCP server not found"
fi

# Check Simple MCP server
if [ -d "mcp_servers/simple_mcp" ]; then
    echo "🔧 Simple MCP server found"
    cd mcp_servers/simple_mcp
    if [ ! -d "venv" ]; then
        echo "📦 Setting up Simple MCP virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        deactivate
    fi
    cd ../..
else
    echo "❌ Simple MCP server not found"
fi

echo ""
echo "📋 Summary:"
echo "   - Python dependencies: Installed"
echo "   - kubectl: Checked"
echo "   - kubectl-ai: Checked"
echo "   - MCP servers: Configured"
echo ""
echo "💡 Next steps:"
echo "   1. Start MCP servers manually if needed:"
echo "      cd mcp_servers/elasticsearch_mcp && python server.py"
echo "      cd mcp_servers/simple_mcp && python server.py"
echo "   2. Configure your Kubernetes cluster connection in config.yaml"
echo "   3. Run the DevOps Assistant with: adk web"