#!/usr/bin/env python3
"""
Test script for kubectl-ai MCP server.
"""

import subprocess
import sys
import os

def test_kubectl_ai_available():
    """Test if kubectl-ai is available."""
    print("Checking if kubectl-ai is available...")
    try:
        result = subprocess.run(
            ["kubectl-ai", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("SUCCESS: kubectl-ai is available")
            return True
        else:
            print("ERROR: kubectl-ai is not available")
            print(f"   Error: {result.stderr}")
            return False
    except FileNotFoundError:
        print("ERROR: kubectl-ai not found in PATH")
        return False
    except Exception as e:
        print(f"ERROR: Error checking kubectl-ai: {e}")
        return False

def test_kubectl_available():
    """Test if kubectl is available."""
    print("Checking if kubectl is available...")
    try:
        result = subprocess.run(
            ["kubectl", "version", "--client"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("SUCCESS: kubectl is available")
            return True
        else:
            print("ERROR: kubectl is not available")
            print(f"   Error: {result.stderr}")
            return False
    except FileNotFoundError:
        print("ERROR: kubectl not found in PATH")
        return False
    except Exception as e:
        print(f"ERROR: Error checking kubectl: {e}")
        return False

def test_env_file():
    """Test if .env file exists and has required variables."""
    print("Checking .env file...")
    # Look for .env in project root (current directory)
    project_root = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(project_root, '.env')
    
    if os.path.exists(env_path):
        print(f"SUCCESS: .env file found at {env_path}")
        # Check for GEMINI_API_KEY
        with open(env_path, 'r') as f:
            content = f.read()
            if 'GEMINI_API_KEY' in content:
                print("SUCCESS: GEMINI_API_KEY found in .env")
                return True
            else:
                print("WARNING: GEMINI_API_KEY not found in .env")
                return False
    else:
        # Try looking in parent directory
        parent_root = os.path.dirname(project_root)
        env_path = os.path.join(parent_root, '.env')
        if os.path.exists(env_path):
            print(f"SUCCESS: .env file found at {env_path}")
            # Check for GEMINI_API_KEY
            with open(env_path, 'r') as f:
                content = f.read()
                if 'GEMINI_API_KEY' in content:
                    print("SUCCESS: GEMINI_API_KEY found in .env")
                    return True
                else:
                    print("WARNING: GEMINI_API_KEY not found in .env")
                    return False
        else:
            print(f"ERROR: .env file not found at {env_path}")
            return False

def main():
    """Main test function."""
    print("Kubectl-AI MCP Server - Test Script")
    print("=" * 40)
    
    # Test prerequisites
    kubectl_available = test_kubectl_available()
    kubectl_ai_available = test_kubectl_ai_available()
    env_file_ok = test_env_file()
    
    print("\nSummary:")
    print(f"   kubectl available: {'SUCCESS' if kubectl_available else 'ERROR'}")
    print(f"   kubectl-ai available: {'SUCCESS' if kubectl_ai_available else 'ERROR'}")
    print(f"   .env file configured: {'SUCCESS' if env_file_ok else 'ERROR'}")
    
    if kubectl_available and kubectl_ai_available and env_file_ok:
        print("\nAll prerequisites met! You can now start the MCP server:")
        print("   cd mcp_servers/kubectl_ai_mcp")
        print("   python server.py")
    else:
        print("\nSome prerequisites are missing.")
        if not kubectl_available:
            print("   Please install kubectl and ensure it's in your PATH")
        if not kubectl_ai_available:
            print("   Please install kubectl-ai and ensure it's in your PATH")
        if not env_file_ok:
            print("   Please create a .env file in the project root with GEMINI_API_KEY")

if __name__ == "__main__":
    main()