#!/usr/bin/env python3
# Copyright 2025 Praveen Rachamreddy
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Test script to verify the Elasticsearch agent."""

import sys
import os

# Add the project root to the path
project_root = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.dirname(project_root)
sys.path.insert(0, parent_dir)

async def test_elasticsearch_agent():
    """Test that the Elasticsearch agent can be imported and instantiated."""
    try:
        # Import the Elasticsearch agent
        from devops_agent_system.agents.sub_agents.elasticsearch_agent import elasticsearch_agent
        print("[PASS] Elasticsearch agent imported successfully")
        
        # Test that we can create the agent instance
        agent_instance = elasticsearch_agent.create_agent()
        print("[PASS] Elasticsearch agent instance created successfully")
        
        print("\nElasticsearch agent test successful!")
        return True
        
    except Exception as e:
        print(f"[FAIL] Elasticsearch agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Elasticsearch agent...")
    print("=" * 50)
    
    import asyncio
    success = asyncio.run(test_elasticsearch_agent())
    
    print("=" * 50)
    if success:
        print("Elasticsearch agent test completed successfully!")
    else:
        print("Elasticsearch agent test failed. Please check the error messages above.")
        sys.exit(1)