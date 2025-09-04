import asyncio
import logging
import os
import json
from typing import Dict, Any, Optional
from fastmcp import FastMCP
import yaml
from pathlib import Path

# Import our Thanos manager
from thanos_manager import initialize_thanos_connection, get_thanos_manager

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

# Initialize FastMCP server
mcp = FastMCP("Thanos MCP Server 📊")

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

# Load configuration and initialize Thanos connection
config = load_config()
thanos_manager = initialize_thanos_connection(config)

@mcp.tool()
async def query_metric(
    query: str,
    time: Optional[str] = None
) -> Dict[str, Any]:
    """Execute a PromQL query against Thanos for an instant result.
    
    Use this tool to query current values of metrics from Thanos.
    
    Args:
        query: The PromQL query to execute (e.g., "up", "rate(container_cpu_usage_seconds_total[5m])")
        time: Evaluation timestamp (RFC3339 format or Unix timestamp)
        
    Returns:
        Query result containing metric data
    """
    logger.info(f"--- 🛠️ Tool: query_metric called with query: {query} ---")
    
    # Validate inputs
    if not query:
        return {"error": "Query not provided"}
    
    if not thanos_manager:
        return {"error": "Thanos connection not initialized"}
    
    try:
        result = await thanos_manager.query(query, time)
        return result
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return {
            "success": False,
            "error": f"Query execution failed: {str(e)}",
            "query": query
        }

@mcp.tool()
async def query_range(
    query: str,
    start: str,
    end: str,
    step: str
) -> Dict[str, Any]:
    """Execute a PromQL range query against Thanos for time-series data.
    
    Use this tool to query historical values of metrics over a time range.
    
    Args:
        query: The PromQL query to execute
        start: Start time (RFC3339 format or Unix timestamp)
        end: End time (RFC3339 format or Unix timestamp)
        step: Query resolution step width in duration format or float number of seconds
        
    Returns:
        Query result containing time-series data
    """
    logger.info(f"--- 🛠️ Tool: query_range called with query: {query} ---")
    
    # Validate inputs
    if not query:
        return {"error": "Query not provided"}
    
    if not start or not end or not step:
        return {"error": "Start, end, and step parameters are required"}
    
    if not thanos_manager:
        return {"error": "Thanos connection not initialized"}
    
    try:
        result = await thanos_manager.query_range(query, start, end, step)
        return result
    except Exception as e:
        logger.error(f"Error executing range query: {e}")
        return {
            "success": False,
            "error": f"Range query execution failed: {str(e)}",
            "query": query
        }

@mcp.tool()
async def list_metrics(
    match: Optional[str] = None
) -> Dict[str, Any]:
    """List available metrics in the Thanos instance.
    
    Use this tool to discover what metrics are available in Thanos.
    
    Args:
        match: Optional metric name matcher (e.g., "{job=~\"kubernetes.*\"}")
        
    Returns:
        List of available metrics
    """
    logger.info("--- 🛠️ Tool: list_metrics called ---")
    
    if not thanos_manager:
        return {"error": "Thanos connection not initialized"}
    
    try:
        # Get series data
        series_result = await thanos_manager.list_series(match)
        if not series_result.get('success'):
            return series_result
        
        # Extract unique metric names
        metrics = set()
        for series in series_result['result']['data']:
            if '__name__' in series:
                metrics.add(series['__name__'])
        
        return {
            "success": True,
            "metrics": sorted(list(metrics))
        }
    except Exception as e:
        logger.error(f"Error listing metrics: {e}")
        return {
            "success": False,
            "error": f"Metrics listing failed: {str(e)}"
        }

@mcp.tool()
async def get_metric_metadata(
    metric: str
) -> Dict[str, Any]:
    """Get metadata and help text for specific metrics.
    
    Use this tool to get detailed information about a specific metric.
    
    Args:
        metric: The metric name to get metadata for
        
    Returns:
        Metadata for the specified metric
    """
    logger.info(f"--- 🛠️ Tool: get_metric_metadata called for metric: {metric} ---")
    
    # Validate inputs
    if not metric:
        return {"error": "Metric name not provided"}
    
    if not thanos_manager:
        return {"error": "Thanos connection not initialized"}
    
    try:
        result = await thanos_manager.get_metadata(metric)
        return result
    except Exception as e:
        logger.error(f"Error getting metric metadata: {e}")
        return {
            "success": False,
            "error": f"Metadata retrieval failed: {str(e)}",
            "metric": metric
        }

@mcp.tool()
async def explore_labels(
    label_name: Optional[str] = None,
    match: Optional[str] = None
) -> Dict[str, Any]:
    """Explore label names and values for metrics.
    
    Use this tool to understand the structure of your metrics by exploring labels.
    
    Args:
        label_name: Optional label name to get values for
        match: Optional metric name matcher
        
    Returns:
        Label names and values information
    """
    logger.info("--- 🛠️ Tool: explore_labels called ---")
    
    if not thanos_manager:
        return {"error": "Thanos connection not initialized"}
    
    try:
        result = {}
        
        # Get all label names if no specific label requested
        if not label_name:
            labels_result = await thanos_manager.get_labels()
            if not labels_result.get('success'):
                return labels_result
            result['names'] = labels_result['result']['data']
        
        # Get values for a specific label
        if label_name:
            values_result = await thanos_manager.get_label_values(label_name)
            if not values_result.get('success'):
                return values_result
            result['values'] = {label_name: values_result['result']['data']}
        
        return {
            "success": True,
            "labels": result
        }
    except Exception as e:
        logger.error(f"Error exploring labels: {e}")
        return {
            "success": False,
            "error": f"Label exploration failed: {str(e)}"
        }

@mcp.tool()
async def analyze_trends(
    query: str,
    duration: str = "1h",
    analysis_type: str = "trend"
) -> Dict[str, Any]:
    """Analyze trends and patterns in metric data.
    
    Use this tool to analyze metric data for trends, anomalies, or correlations.
    
    Args:
        query: The PromQL query to analyze
        duration: Time duration to analyze (e.g., "1h", "24h", "7d")
        analysis_type: Type of analysis ("trend", "anomaly", "correlation")
        
    Returns:
        Analysis results and recommendations
    """
    logger.info(f"--- 🛠️ Tool: analyze_trends called with query: {query} ---")
    
    # Validate inputs
    if not query:
        return {"error": "Query not provided"}
    
    if not thanos_manager:
        return {"error": "Thanos connection not initialized"}
    
    try:
        import time
        import datetime
        
        # Calculate time range for analysis
        end_time = datetime.datetime.now()
        if duration.endswith('h'):
            hours = int(duration[:-1])
            start_time = end_time - datetime.timedelta(hours=hours)
        elif duration.endswith('d'):
            days = int(duration[:-1])
            start_time = end_time - datetime.timedelta(days=days)
        elif duration.endswith('m'):
            minutes = int(duration[:-1])
            start_time = end_time - datetime.timedelta(minutes=minutes)
        else:
            # Default to 1 hour
            start_time = end_time - datetime.timedelta(hours=1)
        
        # Convert to Unix timestamps
        start_timestamp = int(start_time.timestamp())
        end_timestamp = int(end_time.timestamp())
        
        # Execute range query to get time series data
        # For trend analysis, we typically want a reasonable step (e.g., 1 minute for 1h, 10 minutes for 24h)
        if duration.endswith('h') and int(duration[:-1]) <= 1:
            step = "30s"
        elif duration.endswith('h') and int(duration[:-1]) <= 6:
            step = "1m"
        elif duration.endswith('h'):
            step = "5m"
        else:
            step = "30m"
            
        logger.info(f"Executing range query: {query} from {start_timestamp} to {end_timestamp} with step {step}")
        query_result = await thanos_manager.query_range(query, str(start_timestamp), str(end_timestamp), step)
        
        if not query_result.get('success'):
            return query_result
            
        # Process the data for analysis
        data_series = query_result['result']['data']['result']
        
        if not data_series:
            return {
                "success": True,
                "analysis": {
                    "query": query,
                    "duration": duration,
                    "analysis_type": analysis_type,
                    "result": "No data found for the specified query and time range",
                    "recommendations": ["Try a different time range or query"]
                }
            }
        
        # Perform analysis based on type
        analysis_results = []
        
        for series in data_series:
            metric_labels = series.get('metric', {})
            values = series.get('values', [])
            
            if not values:
                continue
                
            # Convert values to numbers
            numeric_values = []
            timestamps = []
            for timestamp, value_str in values:
                try:
                    numeric_values.append(float(value_str))
                    timestamps.append(float(timestamp))
                except (ValueError, TypeError):
                    continue
            
            if not numeric_values:
                continue
                
            # Perform analysis based on type
            if analysis_type == "trend":
                # Simple trend analysis - calculate slope
                if len(numeric_values) > 1:
                    # Linear regression slope calculation
                    n = len(numeric_values)
                    sum_x = sum(range(n))
                    sum_y = sum(numeric_values)
                    sum_xy = sum(i * numeric_values[i] for i in range(n))
                    sum_xx = sum(i * i for i in range(n))
                    
                    if n * sum_xx - sum_x * sum_x != 0:
                        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
                        avg_value = sum_y / n
                        recent_value = numeric_values[-1]
                        
                        # Determine trend direction
                        if abs(slope) < avg_value * 0.01:  # Less than 1% change
                            trend = "stable"
                        elif slope > 0:
                            trend = "increasing"
                        else:
                            trend = "decreasing"
                            
                        # Calculate percentage change
                        if avg_value != 0:
                            pct_change = ((recent_value - avg_value) / avg_value) * 100
                        else:
                            pct_change = 0
                            
                        analysis_results.append({
                            "metric": metric_labels,
                            "trend": trend,
                            "slope": slope,
                            "average_value": avg_value,
                            "recent_value": recent_value,
                            "percentage_change": pct_change,
                            "data_points": len(numeric_values)
                        })
                    else:
                        analysis_results.append({
                            "metric": metric_labels,
                            "trend": "insufficient_data",
                            "data_points": len(numeric_values)
                        })
                else:
                    analysis_results.append({
                        "metric": metric_labels,
                        "trend": "insufficient_data",
                        "data_points": len(numeric_values)
                    })
                    
            elif analysis_type == "anomaly":
                # Simple anomaly detection - values outside 2 standard deviations
                if len(numeric_values) > 3:
                    avg_value = sum(numeric_values) / len(numeric_values)
                    variance = sum((x - avg_value) ** 2 for x in numeric_values) / len(numeric_values)
                    std_dev = variance ** 0.5
                    
                    anomalies = []
                    for i, (timestamp, value) in enumerate(zip(timestamps, numeric_values)):
                        if abs(value - avg_value) > 2 * std_dev:
                            anomalies.append({
                                "timestamp": timestamp,
                                "value": value,
                                "deviation": abs(value - avg_value),
                                "z_score": abs(value - avg_value) / std_dev if std_dev != 0 else 0
                            })
                    
                    analysis_results.append({
                        "metric": metric_labels,
                        "anomalies_found": len(anomalies) > 0,
                        "anomaly_count": len(anomalies),
                        "anomalies": anomalies[:10],  # Limit to first 10 anomalies
                        "average_value": avg_value,
                        "std_deviation": std_dev,
                        "data_points": len(numeric_values)
                    })
                else:
                    analysis_results.append({
                        "metric": metric_labels,
                        "anomalies_found": False,
                        "reason": "Insufficient data points for anomaly detection",
                        "data_points": len(numeric_values)
                    })
            
            else:  # Default analysis
                avg_value = sum(numeric_values) / len(numeric_values) if numeric_values else 0
                max_value = max(numeric_values) if numeric_values else 0
                min_value = min(numeric_values) if numeric_values else 0
                
                analysis_results.append({
                    "metric": metric_labels,
                    "average_value": avg_value,
                    "max_value": max_value,
                    "min_value": min_value,
                    "data_points": len(numeric_values)
                })
        
        # Generate recommendations based on analysis
        recommendations = []
        summary = ""
        
        if analysis_type == "trend" and analysis_results:
            increasing_metrics = [r for r in analysis_results if r.get('trend') == 'increasing']
            decreasing_metrics = [r for r in analysis_results if r.get('trend') == 'decreasing']
            
            if increasing_metrics:
                summary += f"Found {len(increasing_metrics)} metrics with increasing trends. "
                recommendations.append("Monitor increasing metrics for potential resource exhaustion")
            if decreasing_metrics:
                summary += f"Found {len(decreasing_metrics)} metrics with decreasing trends. "
                recommendations.append("Investigate decreasing metrics for potential issues")
                
        elif analysis_type == "anomaly" and analysis_results:
            metrics_with_anomalies = [r for r in analysis_results if r.get('anomalies_found', False)]
            
            if metrics_with_anomalies:
                total_anomalies = sum(r.get('anomaly_count', 0) for r in metrics_with_anomalies)
                summary += f"Detected {total_anomalies} anomalies across {len(metrics_with_anomalies)} metrics. "
                recommendations.append("Investigate anomalous metrics for potential issues")
                recommendations.append("Check system logs around anomaly timestamps")
            else:
                summary += "No significant anomalies detected. "
                
        else:
            summary = f"Analyzed {len(analysis_results)} metric series. "
        
        return {
            "success": True,
            "analysis": {
                "query": query,
                "duration": duration,
                "analysis_type": analysis_type,
                "summary": summary,
                "results": analysis_results,
                "recommendations": recommendations
            }
        }
        
    except Exception as e:
        logger.error(f"Error in trend analysis: {e}")
        return {
            "success": False,
            "error": f"Trend analysis failed: {str(e)}",
            "query": query
        }

@mcp.tool()
async def test_connection() -> Dict[str, Any]:
    """Test the connection to Thanos.
    
    Use this tool to verify that the connection to Thanos is working.
    
    Returns:
        Connection test result
    """
    logger.info("--- 🛠️ Tool: test_connection called ---")
    
    if not thanos_manager:
        return {"error": "Thanos connection not initialized"}
    
    try:
        result = await thanos_manager.test_connection()
        return result
    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        return {
            "success": False,
            "error": f"Connection test failed: {str(e)}"
        }

if __name__ == "__main__":
    # Get port from environment or default to 8083
    port = int(os.getenv('PORT', 8083))
    
    # Log Thanos configuration
    thanos_config = config.get('devops_settings', {}).get('monitoring', {})
    thanos_url = thanos_config.get('thanos_url', os.getenv('THANOS_URL', 'http://localhost:9090'))
    logger.info(f"🚀 Thanos MCP Server starting on port {port}")
    logger.info(f"Thanos URL: {thanos_url}")
    logger.info("Available tools: query_metric, query_range, list_metrics, get_metric_metadata, explore_labels, analyze_trends, test_connection")
    logger.info(f"Server URL will be: http://localhost:{port}/mcp")
    
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
        if thanos_manager:
            asyncio.run(thanos_manager.close())