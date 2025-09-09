#!/usr/bin/env python3
"""
Test script to verify that all agents can be imported and instantiated correctly.
"""

import sys
import os

# Add the project root to the path so we can import the agents
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
devops_system_path = os.path.join(project_root, 'devops_agent_system')
sys.path.insert(0, project_root)
sys.path.insert(0, devops_system_path)
sys.path.insert(0, os.path.join(devops_system_path, 'agents'))
sys.path.insert(0, os.path.join(devops_system_path, 'agents', 'sub_agents'))

def test_agent_import(agent_name, import_path):
    """Test if an agent can be imported."""
    print(f"Testing {agent_name}...")
    try:
        # Import the agent module
        module = __import__(import_path, fromlist=[agent_name])
        # Get the agent instance
        agent_instance = getattr(module, agent_name)
        # Create the agent
        agent = agent_instance.create_agent()
        print(f"SUCCESS: {agent_name} imported and instantiated correctly")
        return True
    except Exception as e:
        print(f"ERROR: Failed to import {agent_name}: {e}")
        return False

def main():
    """Main test function."""
    print("DevOps Automation Project - Agent Import Test")
    print("=" * 50)
    
    # List of agents to test
    agents_to_test = [
        ("search_agent", "agents.sub_agents.search_agent"),
        ("coding_agent", "agents.sub_agents.coding_agent"),
        ("elasticsearch_agent", "agents.sub_agents.elasticsearch_agent"),
        ("simple_mcp_agent", "agents.sub_agents.simple_mcp_agent"),
        ("kubectl_ai_agent", "agents.sub_agents.kubectl_ai_agent"),
        ("monitoring_agent", "agents.sub_agents.monitoring_agent"),
        ("cicd_agent", "agents.sub_agents.cicd_agent"),
        ("infrastructure_agent", "agents.sub_agents.infrastructure_agent"),
        ("deployment_agent", "agents.sub_agents.deployment_agent"),
    ]
    
    # Test each agent
    results = []
    for agent_name, import_path in agents_to_test:
        result = test_agent_import(agent_name, import_path)
        results.append((agent_name, result))
    
    # Print summary
    print("\nSummary:")
    print("-" * 30)
    success_count = 0
    for agent_name, success in results:
        status = "SUCCESS" if success else "ERROR"
        print(f"   {agent_name}: {status}")
        if success:
            success_count += 1
    
    print(f"\n{success_count}/{len(agents_to_test)} agents imported successfully")
    
    if success_count == len(agents_to_test):
        print("\nAll agents imported successfully! The system is ready to use.")
    else:
        print("\nSome agents failed to import. Please check the errors above.")

if __name__ == "__main__":
    main()