#!/usr/bin/env python3
"""
Prerequisites checker and installer for the DevOps Automation Assistant.

This script checks for and installs all required components:
1. kubectl-ai tool
2. MCP servers (Elasticsearch, Simple MCP)
3. Kubernetes CLI (kubectl)
4. Other dependencies
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_command(command, description):
    """Check if a command is available."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error checking {description}: {e}")
        return False

def install_kubectl_ai():
    """Install kubectl-ai tool."""
    print("🔍 Checking for kubectl-ai...")
    
    # Check if kubectl-ai is already installed
    if check_command("kubectl-ai --version", "kubectl-ai"):
        print("✅ kubectl-ai is already installed")
        return True
    
    # Try to build from source
    kubectl_ai_path = os.path.join(os.getcwd(), "kubectl-ai")
    if os.path.exists(kubectl_ai_path):
        print("🔨 Building kubectl-ai from source...")
        try:
            # Change to kubectl-ai directory
            original_dir = os.getcwd()
            os.chdir(kubectl_ai_path)
            
            # Build kubectl-ai
            result = subprocess.run(
                ["go", "build", "-o", "kubectl-ai", "cmd/main.go"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                # Move to a directory in PATH
                kubectl_ai_binary = os.path.join(kubectl_ai_path, "kubectl-ai")
                if os.path.exists(kubectl_ai_binary):
                    # Try to move to /usr/local/bin or similar
                    try:
                        shutil.move(kubectl_ai_binary, "/usr/local/bin/kubectl-ai")
                        print("✅ kubectl-ai installed successfully")
                        os.chdir(original_dir)
                        return True
                    except:
                        # If we can't move to system directory, add to PATH
                        print(f"⚠️  kubectl-ai built but not installed to system PATH")
                        print(f"   Please add {kubectl_ai_path} to your PATH")
                        os.chdir(original_dir)
                        return True
                else:
                    print("❌ kubectl-ai binary not found after build")
            else:
                print(f"❌ Failed to build kubectl-ai: {result.stderr}")
            
            os.chdir(original_dir)
        except Exception as e:
            print(f"❌ Error building kubectl-ai: {e}")
    
    print("❌ kubectl-ai not found and could not be built")
    print("💡 Please install kubectl-ai manually or ensure Go is installed")
    return False

def install_kubectl():
    """Install kubectl if not available."""
    print("🔍 Checking for kubectl...")
    
    if check_command("kubectl version --client", "kubectl"):
        print("✅ kubectl is already installed")
        return True
    
    print("❌ kubectl not found")
    print("💡 Please install kubectl manually:")
    print("   - On Linux: curl -LO 'https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl'")
    print("   - On macOS: brew install kubectl")
    print("   - On Windows: choco install kubernetes-cli")
    return False

def start_mcp_servers():
    """Start MCP servers."""
    print("🚀 Starting MCP servers...")
    
    # Start Elasticsearch MCP server
    elasticsearch_mcp_path = os.path.join(os.getcwd(), "mcp_servers", "elasticsearch_mcp")
    if os.path.exists(elasticsearch_mcp_path):
        print("🔧 Starting Elasticsearch MCP server...")
        try:
            # Change to Elasticsearch MCP directory
            original_dir = os.getcwd()
            os.chdir(elasticsearch_mcp_path)
            
            # Install dependencies if needed
            if not os.path.exists("venv"):
                print("📦 Installing Elasticsearch MCP dependencies...")
                subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
                subprocess.run([os.path.join("venv", "bin", "pip"), "install", "-r", "requirements.txt"], check=True)
            
            # Start server in background (this is a simplified approach)
            print("✅ Elasticsearch MCP server ready (start manually with: python server.py)")
            os.chdir(original_dir)
        except Exception as e:
            print(f"❌ Error setting up Elasticsearch MCP server: {e}")
    
    # Start Simple MCP server
    simple_mcp_path = os.path.join(os.getcwd(), "mcp_servers", "simple_mcp")
    if os.path.exists(simple_mcp_path):
        print("🔧 Starting Simple MCP server...")
        try:
            # Change to Simple MCP directory
            original_dir = os.getcwd()
            os.chdir(simple_mcp_path)
            
            # Install dependencies if needed
            if not os.path.exists("venv"):
                print("📦 Installing Simple MCP dependencies...")
                subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
                subprocess.run([os.path.join("venv", "bin", "pip"), "install", "-r", "requirements.txt"], check=True)
            
            # Start server in background (this is a simplified approach)
            print("✅ Simple MCP server ready (start manually with: python server.py)")
            os.chdir(original_dir)
        except Exception as e:
            print(f"❌ Error setting up Simple MCP server: {e}")

def check_python_dependencies():
    """Check and install Python dependencies."""
    print("🔍 Checking Python dependencies...")
    
    required_packages = [
        "google-adk",
        "pyyaml",
        "elasticsearch",
        "fastmcp",
        "httpx",
        "uvicorn",
        "aiohttp",
        "python-dotenv"
    ]
    
    try:
        import google
        import yaml
        import elasticsearch
        import fastmcp
        import httpx
        import uvicorn
        import aiohttp
        import dotenv
        print("✅ All Python dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing Python dependencies: {e}")
        print("💡 Please install dependencies with: pip install -r requirements.txt")
        return False

def main():
    """Main function to check and install prerequisites."""
    print("🔧 DevOps Automation Assistant - Prerequisites Checker")
    print("=" * 50)
    
    # Check Python dependencies
    check_python_dependencies()
    
    # Install kubectl
    install_kubectl()
    
    # Install kubectl-ai
    install_kubectl_ai()
    
    # Start MCP servers
    start_mcp_servers()
    
    print("\n📋 Summary:")
    print("   - Python dependencies: Checked")
    print("   - kubectl: Checked")
    print("   - kubectl-ai: Checked")
    print("   - MCP servers: Configured")
    print("\n💡 Next steps:")
    print("   1. Start MCP servers manually if needed")
    print("   2. Configure your Kubernetes cluster connection in config.yaml")
    print("   3. Run the DevOps Assistant with: adk web")

if __name__ == "__main__":
    main()