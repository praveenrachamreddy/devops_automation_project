# Thanos MCP Server Architecture

This document describes the architecture of the Thanos MCP Server, which provides monitoring and metrics querying capabilities for Thanos/Prometheus monitoring systems through the Model Context Protocol (MCP).

## System Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│                 │    │                  │    │                 │
│  MCP Client     │    │   Thanos MCP     │    │    Thanos       │
│  (ADK Agent)    │◄──►│    Server        │◄──►│   Components    │
│                 │    │                  │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │ Natural     │ │    │ │ Query        │ │    │ │ Query       │ │
│ │ Language    │ │    │ │ Execution    │ │    │ │ Frontend    │ │
│ │ Interface   │ │    │ │              │ │    │ │             │ │
│ └─────────────┘ │    │ │ ┌──────────┐ │ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ │ │ PromQL   │ │ │    │ ┌─────────────┐ │
│ │ Analysis    │ │    │ │ │ Query    │ │ │    │ │ Store API   │ │
│ │ Engine      │ │    │ │ │ Builder  │ │ │    │ │             │ │
│ └─────────────┘ │    │ │ └──────────┘ │ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ │ ┌──────────┐ │ │    │ ┌─────────────┐ │
│ │ Alerting    │ │    │ │ │ Metric   │ │ │    │ │ Sidecar     │ │
│ │ System      │ │    │ │ │ Metadata │ │ │    │ │             │ │
│ └─────────────┘ │    │ │ │ Handler  │ │ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ │ └──────────┘ │ │    │ ┌─────────────┐ │
│ │ Reporting   │ │    │ │ ┌──────────┐ │ │    │ │ Receive     │ │
│ │ Generator   │ │    │ │ │ Response │ │ │    │ │             │ │
│ └─────────────┘ │    │ │ │ Formatter│ │ │    │ └─────────────┘ │
│                 │    │ │ └──────────┘ │ │    │                 │
│                 │    │ └──────────────┘ │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Core Components

### 1. FastMCP Framework
The server is built on the FastMCP framework, which provides:
- HTTP-based MCP transport
- Tool registration and management
- JSON-RPC 2.0 protocol handling
- Asynchronous request processing

### 2. Thanos Connection Manager
Manages connections to Thanos/Prometheus systems:
- **HTTP Client**: Async HTTP client for API communication
- **Authentication**: Bearer token and basic auth support
- **Connection Pooling**: Efficient connection reuse
- **Error Handling**: Robust error handling and retries

### 3. Query Execution Engine
Handles different types of metric queries:
- **Instant Queries**: Single point-in-time metric values
- **Range Queries**: Time-series data over specified periods
- **Series Discovery**: Metric and label discovery
- **Metadata Retrieval**: Metric type and help information

### 4. Tool Implementations
Each MCP tool provides specific functionality:

#### query_metric
- Executes PromQL queries for instant results
- Handles time parameter for evaluation timestamp
- Returns structured metric data

#### query_range
- Executes PromQL queries over time ranges
- Supports start, end, and step parameters
- Returns time-series matrix data

#### list_metrics
- Discovers available metrics in the system
- Supports optional matching filters
- Returns sorted list of metric names

#### get_metric_metadata
- Retrieves detailed information about metrics
- Provides type, help text, and unit information
- Supports querying specific metrics

#### explore_labels
- Explores label names and values
- Supports label-specific value queries
- Returns structured label information

#### analyze_trends
- Provides framework for metric analysis
- Supports trend, anomaly, and correlation analysis
- Returns analysis results and recommendations

#### test_connection
- Verifies connectivity to Thanos
- Tests health endpoints
- Returns connection status

## Data Flow

```
1. MCP Client Request
        │
        ▼
2. FastMCP Router
        │
        ▼
3. Tool Handler (query_metric, etc.)
        │
        ▼
4. Thanos Connection Manager
        │
        ▼
5. Thanos Query API
        │
        ▼
6. Thanos Components (Querier, Store, etc.)
        │
        ▼
7. Response Processing
        │
        ▼
8. MCP Client Response
```

## Security Architecture

### Authentication
- **Bearer Token**: Primary authentication method
- **Environment Variables**: Secure token storage
- **Config File**: Alternative configuration method

### Transport Security
- **HTTPS**: Encrypted communication by default
- **Certificate Validation**: SSL certificate verification
- **Timeouts**: Request timeout protection

### Access Control
- **Query Limitations**: Prevents dangerous query patterns
- **Rate Limiting**: Future enhancement for abuse prevention
- **Input Validation**: Sanitizes all input parameters

## Configuration Management

### Sources
1. **config.yaml**: Primary configuration file
2. **Environment Variables**: Runtime overrides
3. **Defaults**: Safe fallback values

### Settings
- **Thanos URL**: Query frontend endpoint
- **Authentication**: Token and credentials
- **SSL Settings**: Certificate verification
- **Timeouts**: Request and connection timeouts

## Error Handling

### Categories
- **Network Errors**: Connection and timeout issues
- **HTTP Errors**: API response errors
- **Query Errors**: Invalid PromQL or parameters
- **Authentication Errors**: Token or credential issues

### Strategies
- **Retry Logic**: For transient failures
- **Graceful Degradation**: Partial results when possible
- **Detailed Logging**: Comprehensive error tracking
- **User Feedback**: Clear error messages

## Performance Considerations

### Optimization Techniques
- **Connection Pooling**: Reuse HTTP connections
- **Async Processing**: Non-blocking operations
- **Response Caching**: Future enhancement for frequent queries
- **Query Optimization**: Efficient PromQL patterns

### Scalability
- **Horizontal Scaling**: Multiple server instances
- **Load Distribution**: Even distribution of requests
- **Resource Management**: Efficient memory and CPU usage

## Monitoring and Observability

### Built-in Metrics
- **Request Counters**: Track tool usage
- **Response Times**: Monitor performance
- **Error Rates**: Track failure patterns
- **Connection Health**: Monitor connectivity

### Logging
- **Access Logs**: Request and response tracking
- **Error Logs**: Detailed error information
- **Debug Logs**: Development and troubleshooting

## Extensibility

### Plugin Architecture
- **New Tools**: Easy addition of MCP tools
- **Custom Handlers**: Specialized query processors
- **Middleware**: Request/response processing layers

### Future Enhancements
- **Advanced Analytics**: ML-based anomaly detection
- **Alerting Integration**: Direct alert management
- **Dashboard Generation**: Automated visualization creation
- **Report Export**: Various format exports

## Integration Patterns

### With ADK Agents
- **MCP Toolset**: Standard ADK integration
- **Streamable HTTP**: Efficient transport protocol
- **Context Sharing**: Shared configuration and state

### With Thanos Ecosystem
- **Query Frontend**: Primary integration point
- **Store API**: Direct store access when needed
- **Rule Evaluation**: Future alerting integration

This architecture provides a robust, scalable, and secure foundation for monitoring and metrics analysis through the MCP protocol.