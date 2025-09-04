# Thanos MCP Server

This is an MCP (Model Context Protocol) server that provides monitoring and metrics querying capabilities for Thanos/Prometheus monitoring systems. It uses the FastMCP framework to expose tools for querying metrics, analyzing performance, and troubleshooting issues.

## Features

The server provides the following tools for monitoring:

1. **`query_metric`**: Execute PromQL queries against Thanos
2. **`query_range`**: Execute range queries for time-series data
3. **`list_metrics`**: List available metrics in the Thanos instance
4. **`get_metric_metadata`**: Get metadata and help text for specific metrics
5. **`explore_labels`**: Explore label names and values for metrics
6. **`analyze_trends`**: Analyze trends and patterns in metric data

## Setup

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure your Thanos connection in the project's `config.yaml`:
   ```yaml
   devops_settings:
     monitoring:
       thanos_url: "http://thanos-query:9090"
       thanos_token: "your-thanos-api-token"
       ssl_verify: true
   ```

## Usage

The server can be run as a standalone HTTP service:

```bash
python server.py
```

By default, it will start on port 8083. You can change the port by setting the `PORT` environment variable.

## Thanos Configuration

The server automatically detects Thanos configuration in the following order:

1. **From config.yaml**: Uses monitoring settings in `devops_settings.monitoring` section
2. **From THANOS_URL environment variable**: Uses the URL specified in the THANOS_URL environment variable
3. **Default URL**: Uses `http://localhost:9090` if no configuration is provided

### Configuration in config.yaml

The server looks for Thanos configuration in your project's `config.yaml` file:

```yaml
devops_settings:
  monitoring:
    # Thanos connection settings
    thanos_url: "http://thanos-query.monitoring.svc:9090"
    thanos_token: "sha256~your-thanos-token-here"
    ssl_verify: true
    timeout: 30
```

## Environment Variables

- `PORT`: Port to run the server on (default: 8083)
- `THANOS_URL`: Thanos Query frontend URL (overrides config.yaml setting)
- `THANOS_TOKEN`: Bearer token for Thanos authentication

## Tools API

### query_metric
Execute a PromQL query against Thanos for an instant result.

Parameters:
- `query`: The PromQL query to execute (e.g., "up", "rate(container_cpu_usage_seconds_total[5m])")
- `time`: Evaluation timestamp (RFC3339 format or Unix timestamp)

Returns:
```json
{
  "success": true,
  "result": {
    "status": "success",
    "data": {
      "resultType": "vector",
      "result": [
        {
          "metric": {
            "__name__": "up",
            "job": "kubernetes-nodes",
            "instance": "10.0.0.1:9100"
          },
          "value": [1634567890.123, "1"]
        }
      ]
    }
  }
}
```

### query_range
Execute a PromQL range query against Thanos for time-series data.

Parameters:
- `query`: The PromQL query to execute
- `start`: Start time (RFC3339 format or Unix timestamp)
- `end`: End time (RFC3339 format or Unix timestamp)
- `step`: Query resolution step width in duration format or float number of seconds

Returns:
```json
{
  "success": true,
  "result": {
    "status": "success",
    "data": {
      "resultType": "matrix",
      "result": [
        {
          "metric": {
            "__name__": "up",
            "job": "kubernetes-nodes"
          },
          "values": [
            [1634567890.123, "1"],
            [1634567950.123, "1"],
            [1634568010.123, "1"]
          ]
        }
      ]
    }
  }
}
```

### list_metrics
List available metrics in the Thanos instance.

Parameters:
- `match`: Optional metric name matcher (e.g., "{job=~\"kubernetes.*\"}")

Returns:
```json
{
  "success": true,
  "metrics": [
    "up",
    "container_cpu_usage_seconds_total",
    "container_memory_usage_bytes",
    "node_cpu_seconds_total"
  ]
}
```

### get_metric_metadata
Get metadata and help text for specific metrics.

Parameters:
- `metric`: The metric name to get metadata for

Returns:
```json
{
  "success": true,
  "metadata": {
    "up": {
      "type": "gauge",
      "help": "Metric indicating the health state of a target (1 = up, 0 = down)",
      "unit": ""
    }
  }
}
```

### explore_labels
Explore label names and values for metrics.

Parameters:
- `label_name`: Optional label name to get values for
- `match`: Optional metric name matcher

Returns:
```json
{
  "success": true,
  "labels": {
    "names": ["__name__", "job", "instance", "namespace"],
    "values": {
      "job": ["kubernetes-nodes", "kubernetes-pods", "thanos-query"]
    }
  }
}
```

### analyze_trends
Analyze trends and patterns in metric data.

Parameters:
- `query`: The PromQL query to analyze
- `duration`: Time duration to analyze (e.g., "1h", "24h", "7d")
- `analysis_type`: Type of analysis ("trend", "anomaly", "correlation")

Returns:
```json
{
  "success": true,
  "analysis": {
    "trend": "increasing",
    "rate_of_change": "2.5% per hour",
    "confidence": 0.85,
    "recommendations": [
      "Consider scaling up resources",
      "Monitor for potential bottlenecks"
    ]
  }
}
```

## Testing the Server

You can test if the server is running correctly by making a request to list the available tools:

```bash
curl http://localhost:8083/mcp
```

## Supported Thanos Versions

This server works with:
- Thanos v0.20+ (Query Frontend)
- Prometheus 2.20+ (compatible API)
- Any system exposing the Prometheus HTTP API

## Authentication

The server supports:
- Bearer token authentication
- Basic authentication (username/password)
- Certificate-based authentication (mTLS)
- No authentication (for development/testing)

Make sure your Thanos instance is properly configured and accessible with the provided credentials.