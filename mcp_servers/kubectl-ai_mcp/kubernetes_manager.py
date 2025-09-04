import asyncio
import logging
import os
import subprocess
import tempfile
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class KubernetesConnectionManager:
    """Manages Kubernetes cluster connections for the MCP server."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Kubernetes connection manager.
        
        Args:
            config: Configuration dictionary containing Kubernetes settings
        """
        self.config = config.get('devops_settings', {}).get('kubernetes', {})
        self.kubeconfig_path = None
        self.temp_kubeconfig = None
        
    def setup_kubeconfig(self) -> str:
        """Set up kubeconfig for kubectl commands.
        
        Returns:
            Path to the kubeconfig file to use
        """
        # Check if kubeconfig_path is specified in config
        if self.config.get('kubeconfig_path'):
            kubeconfig_path = os.path.expanduser(self.config['kubeconfig_path'])
            if os.path.exists(kubeconfig_path):
                logger.info(f"Using kubeconfig from config: {kubeconfig_path}")
                self.kubeconfig_path = kubeconfig_path
                return kubeconfig_path
        
        # Check if KUBECONFIG environment variable is set
        if 'KUBECONFIG' in os.environ:
            kubeconfig_path = os.environ['KUBECONFIG']
            if os.path.exists(kubeconfig_path):
                logger.info(f"Using kubeconfig from KUBECONFIG env var: {kubeconfig_path}")
                self.kubeconfig_path = kubeconfig_path
                return kubeconfig_path
        
        # Check default kubeconfig location
        default_kubeconfig = os.path.expanduser('~/.kube/config')
        if os.path.exists(default_kubeconfig):
            logger.info(f"Using default kubeconfig: {default_kubeconfig}")
            self.kubeconfig_path = default_kubeconfig
            return default_kubeconfig
        
        # If no existing kubeconfig, create one from config details
        if self.config:
            kubeconfig_path = self._create_kubeconfig_from_config()
            if kubeconfig_path:
                self.kubeconfig_path = kubeconfig_path
                return kubeconfig_path
        
        # Return None if no kubeconfig can be set up
        logger.warning("No kubeconfig available")
        return None
    
    def _create_kubeconfig_from_config(self) -> Optional[str]:
        """Create a kubeconfig file from the configuration details.
        
        Returns:
            Path to the created kubeconfig file, or None if creation failed
        """
        try:
            # Check if we have the required configuration
            api_url = self.config.get('api_url')
            if not api_url:
                logger.warning("No API URL provided in Kubernetes configuration")
                return None
            
            # Create kubeconfig structure
            kubeconfig = {
                'apiVersion': 'v1',
                'kind': 'Config',
                'clusters': [
                    {
                        'name': 'configured-cluster',
                        'cluster': {
                            'server': api_url
                        }
                    }
                ],
                'users': [
                    {
                        'name': 'configured-user',
                        'user': {}
                    }
                ],
                'contexts': [
                    {
                        'name': 'configured-context',
                        'context': {
                            'cluster': 'configured-cluster',
                            'user': 'configured-user',
                            'namespace': 'default'
                        }
                    }
                ],
                'current-context': 'configured-context'
            }
            
            # Add authentication details
            token = self.config.get('token')
            username = self.config.get('username')
            password = self.config.get('password')
            
            if token:
                kubeconfig['users'][0]['user']['token'] = token
            elif username and password:
                kubeconfig['users'][0]['user']['username'] = username
                kubeconfig['users'][0]['user']['password'] = password
            else:
                logger.warning("No authentication details provided in Kubernetes configuration")
                # Try without authentication (some clusters allow this)
                pass
            
            # Create temporary kubeconfig file
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
            yaml.dump(kubeconfig, temp_file)
            temp_file.close()
            
            self.temp_kubeconfig = temp_file.name
            logger.info(f"Created temporary kubeconfig: {self.temp_kubeconfig}")
            return self.temp_kubeconfig
            
        except Exception as e:
            logger.error(f"Error creating kubeconfig from config: {e}")
            return None
    
    def get_kubeconfig_env(self) -> Dict[str, str]:
        """Get environment variables for kubectl commands.
        
        Returns:
            Dictionary of environment variables
        """
        env = os.environ.copy()
        
        # Set KUBECONFIG if we have a valid kubeconfig path
        kubeconfig_path = self.setup_kubeconfig()
        if kubeconfig_path:
            env['KUBECONFIG'] = kubeconfig_path
            
        return env
    
    def cleanup(self):
        """Clean up temporary files."""
        if self.temp_kubeconfig and os.path.exists(self.temp_kubeconfig):
            try:
                os.unlink(self.temp_kubeconfig)
                logger.info(f"Cleaned up temporary kubeconfig: {self.temp_kubeconfig}")
            except Exception as e:
                logger.warning(f"Error cleaning up temporary kubeconfig: {e}")
            self.temp_kubeconfig = None

# Global connection manager instance
kube_manager = None

def initialize_kubernetes_connection(config: Dict[str, Any]) -> KubernetesConnectionManager:
    """Initialize the global Kubernetes connection manager.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        KubernetesConnectionManager instance
    """
    global kube_manager
    kube_manager = KubernetesConnectionManager(config)
    return kube_manager

def get_kubernetes_env() -> Dict[str, str]:
    """Get environment variables for kubectl commands.
    
    Returns:
        Dictionary of environment variables
    """
    global kube_manager
    if kube_manager:
        return kube_manager.get_kubeconfig_env()
    else:
        # Fallback to default environment
        return os.environ.copy()