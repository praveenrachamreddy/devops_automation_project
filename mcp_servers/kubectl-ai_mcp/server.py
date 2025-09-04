import asyncio
import logging
import os
import subprocess
import json
from typing import Dict, Any, Optional
from fastmcp import FastMCP
import yaml
from pathlib import Path

# Import our Kubernetes manager
from kubernetes_manager import initialize_kubernetes_connection, get_kubernetes_env

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

# Initialize FastMCP server
mcp = FastMCP("Kubectl-AI MCP Server 🚀")

def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml in the project root."""
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "config.yaml"
    
    try:
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            logger.warning(f"Config file not found at {config_path}")
            return {}
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}

# Load configuration and initialize Kubernetes connection
config = load_config()
kube_manager = initialize_kubernetes_connection(config)

@mcp.tool()
async def oc(
    command: str,
    modifies_resource: str = "unknown"
) -> Dict[str, Any]:
    """Executes an OpenShift CLI (oc) command against the user's OpenShift cluster.
    
    Use this tool only when you need to query or modify the state of the user's OpenShift cluster.
    
    IMPORTANT: Interactive commands are not supported in this environment. This includes:
    - oc exec with -it flag (use non-interactive exec instead)
    - oc edit (use oc get -o yaml, oc patch, or oc apply instead)
    - oc port-forward (use alternative methods like NodePort or LoadBalancer)
    
    For interactive operations, please use these non-interactive alternatives:
    - Instead of 'oc edit', use 'oc get -o yaml' to view, 'oc patch' for targeted changes, or 'oc apply' to apply full changes
    - Instead of 'oc exec -it', use 'oc exec' with a specific command
    - Instead of 'oc port-forward', use service types like NodePort or LoadBalancer
    
    Args:
        command: The complete oc command to execute. Prefer to use heredoc syntax for multi-line commands. Please include the oc prefix as well.
        modifies_resource: Whether the command modifies an OpenShift resource.
                          Possible values: "yes", "no", "unknown"
    
    Returns:
        A dictionary containing the command execution results.
    """
    logger.info(f"--- 🛠️ Tool: oc called with command: {command} ---")
    
    # Validate inputs
    if not command:
        return {"error": "oc command not provided"}
    
    # Check for interactive commands (not supported)
    if any(interactive_cmd in command for interactive_cmd in [" exec -it", " port-forward", " edit"]):
        return {
            "error": "interactive mode not supported for oc, please use non-interactive commands"
        }
    
    try:
        # Get environment with Kubernetes configuration
        env = get_kubernetes_env()
        
        # Execute the command
        logger.info(f"Executing oc command: {command}")
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        
        stdout, stderr = await process.communicate()
        
        result = {
            "success": process.returncode == 0,
            "command": command,
            "stdout": stdout.decode().strip() if stdout else "",
            "stderr": stderr.decode().strip() if stderr else "",
            "exit_code": process.returncode
        }
        
        if process.returncode == 0:
            logger.info(f"✅ oc command executed successfully")
        else:
            logger.warning(f"⚠️ oc command failed with exit code {process.returncode}")
            if stderr:
                logger.warning(f"Error output: {stderr.decode().strip()}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error executing oc command: {e}")
        return {
            "success": False,
            "error": f"Error executing oc command: {str(e)}",
            "command": command
        }

@mcp.tool()
async def bash(
    command: str,
    modifies_resource: str = "no"
) -> Dict[str, Any]:
    """Executes a bash command.
    
    Use this tool only when you need to execute a shell command.
    
    Args:
        command: The bash command to execute.
        modifies_resource: Whether the command modifies an OpenShift resource.
                          Possible values: "yes", "no", "unknown"
    
    Returns:
        A dictionary containing the command execution results.
    """
    logger.info(f"--- 🛠️ Tool: bash called with command: {command} ---")
    
    # Validate inputs
    if not command:
        return {"error": "bash command not provided"}
    
    # Check for forbidden commands
    if "oc edit" in command:
        return {
            "error": "interactive mode not supported for oc, please use non-interactive commands"
        }
    
    if "oc port-forward" in command:
        return {
            "error": "port-forwarding is not allowed because assistant is running in an unattended mode, please try some other alternative"
        }
    
    try:
        # Get environment with Kubernetes configuration
        env = get_kubernetes_env()
        
        # Execute the command
        logger.info(f"Executing bash command: {command}")
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        
        stdout, stderr = await process.communicate()
        
        result = {
            "success": process.returncode == 0,
            "command": command,
            "stdout": stdout.decode().strip() if stdout else "",
            "stderr": stderr.decode().strip() if stderr else "",
            "exit_code": process.returncode
        }
        
        if process.returncode == 0:
            logger.info(f"✅ bash command executed successfully")
        else:
            logger.warning(f"⚠️ bash command failed with exit code {process.returncode}")
            if stderr:
                logger.warning(f"Error output: {stderr.decode().strip()}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error executing bash command: {e}")
        return {
            "success": False,
            "error": f"Error executing bash command: {str(e)}",
            "command": command
        }

if __name__ == "__main__":
    # Get port from environment or default to 8082
    port = int(os.getenv('PORT', 8082))
    
    logger.info(f"🚀 Kubectl-AI MCP Server starting on port {port}")
    logger.info("Available tools: oc, bash")
    logger.info(f"Server URL will be: http://localhost:{port}/mcp")
    
    # Log Kubernetes configuration
    kubeconfig_path = kube_manager.setup_kubeconfig()
    if kubeconfig_path:
        logger.info(f"Using kubeconfig: {kubeconfig_path}")
    else:
        logger.warning("No kubeconfig available - oc commands may fail")
    
    try:
        # Run the server
        asyncio.run(
            mcp.run_async(
                transport="streamable-http",
                host="0.0.0.0",
                port=port,
            )
        )
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server failed to start: {e}")
    finally:
        # Clean up
        if kube_manager:
            kube_manager.cleanup()