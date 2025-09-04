import asyncio
import json
import logging
import os
import ssl
from typing import Dict, Any, List, Optional

from elasticsearch import AsyncElasticsearch
from dotenv import load_dotenv
import httpx
from fastmcp import FastMCP

load_dotenv()

# --- Logging Setup ---
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s]: %(message)s",
)

# --- Elasticsearch Configuration ---
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "https://localhost:9200")
ELASTICSEARCH_USERNAME = os.getenv("ELASTICSEARCH_USERNAME", "elastic")
ELASTICSEARCH_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD", "changeme")
ELASTICSEARCH_SSL_SKIP_VERIFY = os.getenv("ELASTICSEARCH_SSL_SKIP_VERIFY", "false").lower() == "true"

# --- Elasticsearch Client Manager ---
class ElasticsearchClientManager:
    def __init__(self):
        self.es_client = None

    async def get_client(self) -> AsyncElasticsearch:
        if self.es_client is None or not await self.es_client.ping():
            logger.info("Creating new Elasticsearch client...")
            if self.es_client:
                await self.close_client()
            ssl_context = None
            if ELASTICSEARCH_SSL_SKIP_VERIFY:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            
            self.es_client = AsyncElasticsearch(
                hosts=[ELASTICSEARCH_URL],
                basic_auth=(ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD),
                ssl_context=ssl_context,
                verify_certs=not ELASTICSEARCH_SSL_SKIP_VERIFY,
                request_timeout=10
            )
            try:
                info = await self.es_client.info()
                logger.info(f"Successfully connected to Elasticsearch. Cluster: {info['cluster_name']}")
            except Exception as e:
                logger.error(f"Failed to connect to Elasticsearch: {e}")
                await self.close_client()
                raise
        return self.es_client

    async def close_client(self):
        if self.es_client:
            await self.es_client.close()
            self.es_client = None

es_manager = ElasticsearchClientManager()

# --- FastMCP Server Setup ---
mcp = FastMCP("Elasticsearch MCP Server 📊")

@mcp.tool()
async def test_connection() -> Dict[str, Any]:
    """Test the connection to Elasticsearch.
    
    Returns:
        A dictionary containing connection status and cluster information.
    """
    logger.info("--- 🛠️ Tool: test_connection called ---")
    try:
        es = await es_manager.get_client()
        info = await es.info()
        stats = await es.cluster.stats()
        return {
            "success": True,
            "message": "Successfully connected to Elasticsearch",
            "cluster_info": {
                "cluster_name": info.get("cluster_name"),
                "version": info.get("version", {}).get("number"),
                "node_count": stats.get("nodes", {}).get("count", {}).get("total"),
            }
        }
    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        return {"success": False, "message": f"Error testing connection: {e}"}

@mcp.tool()
async def list_indices(pattern: str = "*") -> Dict[str, Any]:
    """List all available Elasticsearch indices, with an optional filter pattern.
    
    Args:
        pattern: Pattern to filter indices (e.g., "logs-*"). Defaults to "*".
        
    Returns:
        A dictionary containing the list of indices.
    """
    logger.info(f"--- 🛠️ Tool: list_indices called with pattern: {pattern} ---")
    try:
        es = await es_manager.get_client()
        indices = await es.indices.get(index=pattern)
        index_list = list(indices.keys())
        return {
            "success": True,
            "message": f"Found {len(index_list)} indices",
            "indices": index_list
        }
    except Exception as e:
        logger.error(f"Error listing indices: {e}")
        return {"success": False, "message": f"Error listing indices: {e}", "indices": []}

@mcp.tool()
async def get_mappings(index_name: str) -> Dict[str, Any]:
    """Get field mappings for a specific Elasticsearch index.
    
    Args:
        index_name: Name of the index to get mappings for.
        
    Returns:
        A dictionary containing the index mappings.
    """
    logger.info(f"--- 🛠️ Tool: get_mappings called for index: {index_name} ---")
    try:
        es = await es_manager.get_client()
        mappings = await es.indices.get_mapping(index=index_name)
        return {
            "success": True,
            "message": f"Retrieved mappings for index '{index_name}'",
            "index": index_name,
            "mappings": mappings.body
        }
    except Exception as e:
        logger.error(f"Error getting mappings for index '{index_name}': {e}")
        return {"success": False, "message": f"Error getting mappings for index '{index_name}': {e}", "mappings": {}}

@mcp.tool()
async def search(index_name: str, query: Dict[str, Any]) -> Dict[str, Any]:
    """Perform an Elasticsearch search with the provided query DSL.
    
    Args:
        index_name: Name of the index to search.
        query: Elasticsearch query DSL as a dictionary.
        
    Returns:
        A dictionary containing the search results.
    """
    logger.info(f"--- 🛠️ Tool: search called for index: {index_name} ---")
    try:
        es = await es_manager.get_client()
        response = await es.search(index=index_name, body=query)
        total_hits = response['hits']['total']['value']
        return {
            "success": True,
            "message": f"Search completed successfully. Found {total_hits} documents.",
            "total": total_hits,
            "hits": response['hits']['hits']
        }
    except Exception as e:
        logger.error(f"Error performing search on index '{index_name}': {e}")
        return {"success": False, "message": f"Error performing search on index '{index_name}': {e}", "hits": []}

@mcp.tool()
async def esql(query: str) -> Dict[str, Any]:
    """Perform an ES|QL query.
    
    Args:
        query: ES|QL query string.
        
    Returns:
        A dictionary containing the query results.
    """
    logger.info(f"--- 🛠️ Tool: esql called with query: {query} ---")
    try:
        es = await es_manager.get_client()
        # ES|QL is available in Elasticsearch 8.0+
        response = await es.perform_request(
            method="POST",
            path="/_query",
            body={"query": query}
        )
        return {
            "success": True,
            "message": "ES|QL query completed successfully.",
            "results": response.body
        }
    except Exception as e:
        logger.error(f"Error performing ES|QL query: {e}")
        return {"success": False, "message": f"Error performing ES|QL query: {e}", "results": {}}

@mcp.tool()
async def get_shards(indices: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get shard information for all or specific indices.
    
    Args:
        indices: List of indices to get shard information for. If None, gets all shards.
        
    Returns:
        A dictionary containing shard information.
    """
    logger.info(f"--- 🛠️ Tool: get_shards called for indices: {indices} ---")
    try:
        es = await es_manager.get_client()
        if indices:
            response = await es.cat.shards(index=indices, format="json")
        else:
            response = await es.cat.shards(format="json")
        return {
            "success": True,
            "message": "Retrieved shard information",
            "shards": response.body
        }
    except Exception as e:
        logger.error(f"Error getting shard information: {e}")
        return {"success": False, "message": f"Error getting shard information: {e}", "shards": []}

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8081))
    logger.info(f"🚀 Elasticsearch MCP Server starting on port {port}")
    logger.info("Available tools: test_connection, list_indices, get_mappings, search, esql, get_shards")
    logger.info(f"Server URL will be: http://localhost:{port}/mcp")
    
    try:
        # Could also use 'sse' transport, host="0.0.0.0" required for Cloud Run.
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
        asyncio.run(es_manager.close_client())