# OpenShift AI MCP Server

This is an MCP (Model Context Protocol) server that provides OpenShift management tools for use with the Google Agent Development Kit (ADK). It uses the FastMCP framework and connects to OpenShift clusters to execute `oc` commands and manage cluster resources.

## Features

The server provides the following tools for OpenShift management:

1. **`oc`**: Execute OpenShift CLI (oc) commands to manage OpenShift clusters
2. **`bash`**: Execute bash commands for system operations

## Setup

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

The server can be run as a standalone HTTP service:

```bash
python server.py
```

By default, it will start on port 8082. You can change the port by setting the `PORT` environment variable.

## OpenShift Configuration

The server automatically detects OpenShift configuration in the following order:

1. **From config.yaml**: Uses Kubernetes settings in `devops_settings.kubernetes` section
2. **From KUBECONFIG environment variable**: Uses the path specified in the KUBECONFIG environment variable
3. **From default location**: Uses `~/.kube/config` if it exists

### Configuration in config.yaml

The server looks for OpenShift configuration in your project's `config.yaml` file:

```yaml
devops_settings:
  kubernetes:
    # Cluster connection settings
    api_url: "https://api.ocp4.imss.work:6443"
    username: "ocpadmin"
    password: "oShift@123"
    token: "sha256~F4ixBQBun-4atLkIdNlTsp-4NOpTe_SPftvasIuuN8Q"
    kubeconfig_path: "~/.kube/config"
```

If a kubeconfig_path is specified and the file exists, it will be used directly. Otherwise, the server will create a temporary kubeconfig file from the provided API URL and authentication details.

## Environment Variables

- `PORT`: Port to run the server on (default: 8082)
- `KUBECONFIG`: Path to kubeconfig file (overrides config.yaml setting)

## Tools API

### oc
Execute OpenShift CLI (oc) commands to interact with the OpenShift cluster.

Parameters:
- `command`: The oc command to execute (e.g., "oc get pods", "oc describe deployment nginx")
- `modifies_resource`: Whether the command modifies an OpenShift resource. Possible values: "yes", "no", "unknown"

Returns:
```json
{
  "success": true,
  "command": "oc get pods",
  "stdout": "NAME READY STATUS RESTARTS AGE\nnginx-deployment-12345 1/1 Running 0 2d",
  "stderr": "",
  "exit_code": 0
}
```

### bash
Execute bash commands for system operations.

Parameters:
- `command`: The bash command to execute (e.g., "ls -la", "echo 'Hello World'")
- `modifies_resource`: Whether the command modifies an OpenShift resource. Possible values: "yes", "no", "unknown"

Returns:
```json
{
  "success": true,
  "command": "echo 'Hello World'",
  "stdout": "Hello World",
  "stderr": "",
  "exit_code": 0
}
```

## Testing the Server

You can test if the server is running correctly by making a request to list the available tools:

```bash
curl http://localhost:8082/mcp
```

## Supported OpenShift Clusters

This server works with any OpenShift cluster, including:
- Red Hat OpenShift Container Platform (OCP)
- Red Hat OpenShift Dedicated
- Red Hat OpenShift Online
- OKD (OpenShift Origin)
- Local development clusters (CodeReady Containers, minishift, etc.)

Make sure your kubeconfig is properly configured and has the necessary permissions to execute the commands you want to use.