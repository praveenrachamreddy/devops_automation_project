# Elasticsearch MCP Server

This is an updated MCP (Model Context Protocol) server that exposes Elasticsearch functionality as tools for use with the Google Agent Development Kit (ADK). It now uses the FastMCP framework for better performance and reliability.

## Features

The server provides the following tools for interacting with Elasticsearch:

1. **`test_connection`**: Test the connection to Elasticsearch
2. **`list_indices`**: List all available Elasticsearch indices
3. **`get_mappings`**: Get field mappings for a specific Elasticsearch index
4. **`search`**: Perform an Elasticsearch search with the provided query DSL
5. **`esql`**: Perform an ES|QL query
6. **`get_shards`**: Get shard information for all or specific indices

## Setup

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy the `.env.example` file to `.env` and configure your Elasticsearch connection settings:
   ```bash
   cp .env.example .env
   ```

3. Edit the `.env` file to match your Elasticsearch configuration.

## Usage

The server can be run as a standalone HTTP service:

```bash
python server.py
```

By default, it will start on port 8081. You can change the port by setting the `PORT` environment variable.

## Environment Variables

- `ELASTICSEARCH_URL`: Elasticsearch endpoint URL (default: "https://localhost:9200")
- `ELASTICSEARCH_USERNAME`: Elasticsearch username (default: "elastic")
- `ELASTICSEARCH_PASSWORD`: Elasticsearch password (default: "changeme")
- `ELASTICSEARCH_SSL_SKIP_VERIFY`: Skip SSL verification (default: "false")
- `PORT`: Port to run the server on (default: 8081)

## Tools API

### test_connection
Test the connection to Elasticsearch.

Parameters:
- None

Returns:
```json
{
  "success": true,
  "message": "Successfully connected to Elasticsearch",
  "cluster_info": {
    "cluster_name": "elasticsearch",
    "version": "8.11.0",
    "node_count": 1
  }
}
```

### list_indices
Lists all available Elasticsearch indices.

Parameters:
- `pattern` (optional): Pattern to filter indices (e.g., "logs-*")

Returns:
```json
{
  "success": true,
  "message": "Found X indices",
  "indices": ["index1", "index2", ...]
}
```

### get_mappings
Gets field mappings for a specific Elasticsearch index.

Parameters:
- `index_name`: Name of the index to get mappings for

Returns:
```json
{
  "success": true,
  "message": "Retrieved mappings for index 'index_name'",
  "index": "index_name",
  "mappings": {...}
}
```

### search
Performs an Elasticsearch search with the provided query DSL.

Parameters:
- `index_name`: Name of the index to search
- `query`: Elasticsearch query DSL as a dictionary

Returns:
```json
{
  "success": true,
  "message": "Search completed successfully. Found X documents.",
  "total": X,
  "hits": [...]
}
```

### esql
Performs an ES|QL query.

Parameters:
- `query`: ES|QL query string

Returns:
```json
{
  "success": true,
  "message": "ES|QL query completed successfully.",
  "results": {...}
}
```

### get_shards
Gets shard information for all or specific indices.

Parameters:
- `indices` (optional): List of indices to get shard information for

Returns:
```json
{
  "success": true,
  "message": "Retrieved shard information",
  "shards": [...]
}
```

## Testing Connectivity

To test if the server can connect to your Elasticsearch instance, you can run the provided test script:

```bash
python test_elasticsearch.py
```

This script will:
1. Load your environment variables from the `.env` file
2. Try to connect to your Elasticsearch instance
3. Show cluster information if successful
4. List all indices
5. Provide troubleshooting tips if there's an error

## Troubleshooting

### Common Issues

1. **Connection timed out**: 
   - Check if the Elasticsearch server is running and accessible
   - Verify the IP address and port are correct
   - Check firewall settings

2. **SSL certificate errors**:
   - Set `ELASTICSEARCH_SSL_SKIP_VERIFY=true` in your `.env` file
   - Or ensure you have the correct SSL certificates

3. **Authentication failed**:
   - Verify username and password in the `.env` file
   - Check if the user has the necessary permissions

4. **Version compatibility issues**:
   - Ensure the Elasticsearch client version matches your server version
   - Current requirements support Elasticsearch 7.x and 8.x

### Version Compatibility

The current implementation supports Elasticsearch versions 7.x and 8.x. If you're using a different version, you may need to adjust the `elasticsearch` package version in `requirements.txt`.