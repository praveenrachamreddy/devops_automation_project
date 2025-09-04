import logging
import os
import httpx
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ThanosConnectionManager:
    """Manages Thanos/Prometheus connection for the MCP server."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Thanos connection manager.
        
        Args:
            config: Configuration dictionary containing Thanos settings
        """
        self.config = config.get('devops_settings', {}).get('monitoring', {})
        self.client = None
        self._setup_client()
        
    def _setup_client(self):
        """Set up the HTTP client for Thanos connections."""
        # Get configuration values
        thanos_url = self.config.get('thanos_url', os.getenv('THANOS_URL', 'http://localhost:9090'))
        thanos_token = self.config.get('thanos_token', os.getenv('THANOS_TOKEN', ''))
        ssl_verify = self.config.get('ssl_verify', True)
        timeout = self.config.get('timeout', 30)
        
        # Log connection details (without sensitive information)
        logger.info(f"Setting up Thanos connection to: {thanos_url}")
        logger.info(f"SSL verification: {ssl_verify}")
        logger.info(f"Timeout: {timeout}s")
        
        # Set up headers
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Thanos-MCP-Server/1.0'
        }
        
        # Add authentication if token is provided
        if thanos_token:
            headers['Authorization'] = f'Bearer {thanos_token}'
            logger.info("Authentication token configured")
        
        # Create HTTP client
        self.client = httpx.AsyncClient(
            base_url=thanos_url,
            headers=headers,
            verify=ssl_verify,
            timeout=timeout
        )
        
        logger.info("Thanos HTTP client initialized")
    
    async def query(self, query: str, time: Optional[str] = None) -> Dict[str, Any]:
        """Execute an instant query against Thanos.
        
        Args:
            query: PromQL query string
            time: Evaluation timestamp (RFC3339 or Unix timestamp)
            
        Returns:
            Query result dictionary
        """
        try:
            params = {'query': query}
            if time:
                params['time'] = time
                
            response = await self.client.get('/api/v1/query', params=params)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Query executed successfully: {query[:50]}...")
            return {
                'success': True,
                'result': result
            }
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during query: {e}")
            return {
                'success': False,
                'error': f'HTTP error: {str(e)}',
                'query': query
            }
        except Exception as e:
            logger.error(f"Error during query execution: {e}")
            return {
                'success': False,
                'error': f'Query execution failed: {str(e)}',
                'query': query
            }
    
    async def query_range(self, query: str, start: str, end: str, step: str) -> Dict[str, Any]:
        """Execute a range query against Thanos.
        
        Args:
            query: PromQL query string
            start: Start time (RFC3339 or Unix timestamp)
            end: End time (RFC3339 or Unix timestamp)
            step: Query resolution step width
            
        Returns:
            Query result dictionary
        """
        try:
            params = {
                'query': query,
                'start': start,
                'end': end,
                'step': step
            }
                
            response = await self.client.get('/api/v1/query_range', params=params)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Range query executed successfully: {query[:50]}...")
            return {
                'success': True,
                'result': result
            }
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during range query: {e}")
            return {
                'success': False,
                'error': f'HTTP error: {str(e)}',
                'query': query
            }
        except Exception as e:
            logger.error(f"Error during range query execution: {e}")
            return {
                'success': False,
                'error': f'Range query execution failed: {str(e)}',
                'query': query
            }
    
    async def list_series(self, match: Optional[str] = None) -> Dict[str, Any]:
        """List series matching the provided selectors.
        
        Args:
            match: Series selector (e.g., 'up', 'job="api-server"')
            
        Returns:
            Series list dictionary
        """
        try:
            params = {}
            if match:
                params['match[]'] = match
                
            response = await self.client.get('/api/v1/series', params=params)
            response.raise_for_status()
            
            result = response.json()
            logger.info("Series listing executed successfully")
            return {
                'success': True,
                'result': result
            }
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during series listing: {e}")
            return {
                'success': False,
                'error': f'HTTP error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error during series listing: {e}")
            return {
                'success': False,
                'error': f'Series listing failed: {str(e)}'
            }
    
    async def get_labels(self) -> Dict[str, Any]:
        """Get list of label names.
        
        Returns:
            Label names dictionary
        """
        try:
            response = await self.client.get('/api/v1/labels')
            response.raise_for_status()
            
            result = response.json()
            logger.info("Labels retrieval executed successfully")
            return {
                'success': True,
                'result': result
            }
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during labels retrieval: {e}")
            return {
                'success': False,
                'error': f'HTTP error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error during labels retrieval: {e}")
            return {
                'success': False,
                'error': f'Labels retrieval failed: {str(e)}'
            }
    
    async def get_label_values(self, label_name: str) -> Dict[str, Any]:
        """Get list of label values for a given label name.
        
        Args:
            label_name: Name of the label to get values for
            
        Returns:
            Label values dictionary
        """
        try:
            response = await self.client.get(f'/api/v1/label/{label_name}/values')
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Label values retrieval executed successfully for: {label_name}")
            return {
                'success': True,
                'result': result
            }
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during label values retrieval: {e}")
            return {
                'success': False,
                'error': f'HTTP error: {str(e)}',
                'label': label_name
            }
        except Exception as e:
            logger.error(f"Error during label values retrieval: {e}")
            return {
                'success': False,
                'error': f'Label values retrieval failed: {str(e)}',
                'label': label_name
            }
    
    async def get_metadata(self, metric: Optional[str] = None) -> Dict[str, Any]:
        """Get metadata for metrics.
        
        Args:
            metric: Optional metric name to get metadata for
            
        Returns:
            Metadata dictionary
        """
        try:
            params = {}
            if metric:
                params['metric'] = metric
                
            response = await self.client.get('/api/v1/metadata', params=params)
            response.raise_for_status()
            
            result = response.json()
            logger.info("Metadata retrieval executed successfully")
            return {
                'success': True,
                'result': result
            }
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during metadata retrieval: {e}")
            return {
                'success': False,
                'error': f'HTTP error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error during metadata retrieval: {e}")
            return {
                'success': False,
                'error': f'Metadata retrieval failed: {str(e)}'
            }
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test the connection to Thanos.
        
        Returns:
            Connection test result
        """
        try:
            response = await self.client.get('/-/healthy')
            if response.status_code == 200:
                logger.info("Thanos connection test successful")
                return {
                    'success': True,
                    'message': 'Successfully connected to Thanos'
                }
            else:
                logger.warning(f"Thanos health check failed with status: {response.status_code}")
                return {
                    'success': False,
                    'error': f'Thanos health check failed: {response.status_code}'
                }
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during connection test: {e}")
            return {
                'success': False,
                'error': f'HTTP error during connection test: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error during connection test: {e}")
            return {
                'success': False,
                'error': f'Connection test failed: {str(e)}'
            }
    
    async def close(self):
        """Close the HTTP client connection."""
        if self.client:
            await self.client.aclose()
            logger.info("Thanos HTTP client closed")

# Global connection manager instance
thanos_manager = None

def initialize_thanos_connection(config: Dict[str, Any]) -> ThanosConnectionManager:
    """Initialize the global Thanos connection manager.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        ThanosConnectionManager instance
    """
    global thanos_manager
    thanos_manager = ThanosConnectionManager(config)
    return thanos_manager

def get_thanos_manager() -> Optional[ThanosConnectionManager]:
    """Get the global Thanos connection manager.
    
    Returns:
        ThanosConnectionManager instance or None
    """
    global thanos_manager
    return thanos_manager