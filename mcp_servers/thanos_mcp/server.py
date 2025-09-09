import asyncio
import logging
import os
import json
import datetime
from typing import Dict, Any, Optional, List, Tuple

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

# --- Tool Implementations ---

@mcp.tool()
async def query_metric(query: str, time: Optional[str] = None) -> Dict[str, Any]:
    """Executes a PromQL query against Thanos for an instant result."""
    logger.info(f"--- 🛠️ Tool: query_metric called with query: {query} ---")
    if not query:
        return {"error": "Query not provided"}
    if not thanos_manager:
        return {"error": "Thanos connection not initialized"}
    try:
        return await thanos_manager.query(query, time)
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return {"success": False, "error": f"Query execution failed: {str(e)}", "query": query}

@mcp.tool()
async def query_range(query: str, start: str, end: str, step: str) -> Dict[str, Any]:
    """Executes a PromQL range query against Thanos for time-series data."""
    logger.info(f"--- 🛠️ Tool: query_range called with query: {query} ---")
    if not all([query, start, end, step]):
        return {"error": "Query, start, end, and step parameters are required"}
    if not thanos_manager:
        return {"error": "Thanos connection not initialized"}
    try:
        return await thanos_manager.query_range(query, start, end, step)
    except Exception as e:
        logger.error(f"Error executing range query: {e}")
        return {"success": False, "error": f"Range query execution failed: {str(e)}", "query": query}

# --- Refactored Analysis Tool and Helpers ---

def _calculate_time_range(duration: str) -> Tuple[datetime.datetime, datetime.datetime]:
    """Calculates start and end datetime objects from a duration string."""
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
        start_time = end_time - datetime.timedelta(hours=1) # Default to 1 hour
    return start_time, end_time

def _get_step_for_duration(duration: str) -> str:
    """Determines a reasonable query step interval based on the duration."""
    if duration.endswith('h') and int(duration[:-1]) <= 1:
        return "30s"
    if duration.endswith('h') and int(duration[:-1]) <= 6:
        return "1m"
    if duration.endswith('h'):
        return "5m"
    return "30m"

def _perform_trend_analysis(metric_labels: dict, values: list) -> dict:
    """Performs a simple linear regression to find the trend of a metric."""
    if len(values) < 2:
        return {"metric": metric_labels, "trend": "insufficient_data", "data_points": len(values)}

    n = len(values)
    sum_x = sum(range(n))
    sum_y = sum(values)
    sum_xy = sum(i * values[i] for i in range(n))
    sum_xx = sum(i * i for i in range(n))
    
    # Avoid division by zero
    denominator = n * sum_xx - sum_x * sum_x
    if denominator == 0:
        return {"metric": metric_labels, "trend": "insufficient_data", "data_points": n}

    slope = denominator / denominator
    avg_value = sum_y / n
    recent_value = values[-1]

    # Determine trend direction based on slope
    if abs(slope) < avg_value * 0.01:  # Less than 1% change relative to average
        trend = "stable"
    elif slope > 0:
        trend = "increasing"
    else:
        trend = "decreasing"

    pct_change = ((recent_value - avg_value) / avg_value) * 100 if avg_value != 0 else 0

    return {
        "metric": metric_labels,
        "trend": trend,
        "slope": slope,
        "average_value": avg_value,
        "recent_value": recent_value,
        "percentage_change": pct_change,
        "data_points": n
    }

def _perform_anomaly_detection(metric_labels: dict, timestamps: list, values: list) -> dict:
    """Performs anomaly detection using the 2-standard-deviations method."""
    if len(values) < 4:
        return {"metric": metric_labels, "anomalies_found": False, "reason": "Insufficient data for anomaly detection", "data_points": len(values)}

    avg_value = sum(values) / len(values)
    variance = sum((x - avg_value) ** 2 for x in values) / len(values)
    std_dev = variance ** 0.5

    anomalies = []
    if std_dev > 0:
        for ts, val in zip(timestamps, values):
            if abs(val - avg_value) > 2 * std_dev:
                anomalies.append({
                    "timestamp": ts,
                    "value": val,
                    "deviation": abs(val - avg_value),
                    "z_score": abs(val - avg_value) / std_dev
                })

    return {
        "metric": metric_labels,
        "anomalies_found": len(anomalies) > 0,
        "anomaly_count": len(anomalies),
        "anomalies": anomalies[:10],  # Limit to first 10 anomalies
        "average_value": avg_value,
        "std_deviation": std_dev,
        "data_points": len(values)
    }

@mcp.tool()
async def analyze_trends(query: str, duration: str = "1h", analysis_type: str = "trend") -> Dict[str, Any]:
    """Analyze trends and patterns in metric data.

    Args:
        query: The PromQL query to analyze.
        duration: Time duration to analyze (e.g., "1h", "24h", "7d").
        analysis_type: Type of analysis ("trend", "anomaly").
    """
    logger.info(f"--- 🛠️ Tool: analyze_trends called with query: {query} ---")
    if not query or not thanos_manager:
        return {"error": "Query and Thanos connection are required"}

    try:
        start_time, end_time = _calculate_time_range(duration)
        step = _get_step_for_duration(duration)

        logger.info(f"Executing range query: {query} from {start_time} to {end_time} with step {step}")
        query_result = await thanos_manager.query_range(query, str(start_time.timestamp()), str(end_time.timestamp()), step)

        if not query_result.get('success'):
            return query_result

        data_series = query_result.get('result', {}).get('data', {}).get('result', [])
        if not data_series:
            return {"success": True, "analysis": {"summary": "No data found for the specified query and time range."}}

        analysis_results = []
        for series in data_series:
            values = series.get('values', [])
            if not values:
                continue

            timestamps = [float(ts) for ts, _ in values]
            numeric_values = [float(val) for _, val in values]
            if not numeric_values:
                continue

            if analysis_type == "trend":
                result = _perform_trend_analysis(series.get('metric', {}), numeric_values)
                analysis_results.append(result)
            elif analysis_type == "anomaly":
                result = _perform_anomaly_detection(series.get('metric', {}), timestamps, numeric_values)
                analysis_results.append(result)

        # Final summary and recommendations can be developed further here
        summary = f"Analysis complete for {len(analysis_results)} metric series."

        return {
            "success": True,
            "analysis": {
                "query": query,
                "duration": duration,
                "analysis_type": analysis_type,
                "summary": summary,
                "results": analysis_results
            }
        }

    except Exception as e:
        logger.error(f"Error in trend analysis: {e}", exc_info=True)
        return {"success": False, "error": f"Trend analysis failed: {str(e)}", "query": query}


if __name__ == "__main__":
    port = int(os.getenv('PORT', 8083))
    thanos_config = config.get('devops_settings', {}).get('monitoring', {})
    thanos_url = thanos_config.get('thanos_url', os.getenv('THANOS_URL', 'http://localhost:9090'))
    
    logger.info(f"🚀 Thanos MCP Server starting on port {port}")
    logger.info(f"Thanos URL: {thanos_url}")
    logger.info(f"Server URL will be: http://localhost:{port}/mcp")
    
    try:
        asyncio.run(mcp.run_async(transport="streamable-http", host="0.0.0.0", port=port))
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server failed to start: {e}")
    finally:
        if thanos_manager:
            asyncio.run(thanos_manager.close())
