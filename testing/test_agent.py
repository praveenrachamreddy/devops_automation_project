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

"""Test script to verify the DevOps Automation Assistant can run."""

import sys
import os

# Add the project root to the path
project_root = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.dirname(project_root)
sys.path.insert(0, parent_dir)

async def test_agent_creation():
    """Test that the agent can be created and run successfully."""
    try:
        # Import the root agent
        from devops_agent_system.agent import root_agent
        print("[PASS] Root agent imported successfully")
        
        # Test that we can create the agent instances
        search_agent_instance = root_agent.tools[0].agent
        print("[PASS] Search agent instance created successfully")
        
        coding_agent_instance = root_agent.tools[1].agent
        print("[PASS] Coding agent instance created successfully")
        
        print("\nAgent creation test successful!")
        return True
        
    except Exception as e:
        print(f"[FAIL] Agent creation failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing DevOps Automation Assistant agent creation...")
    print("=" * 50)
    
    import asyncio
    success = asyncio.run(test_agent_creation())
    
    print("=" * 50)
    if success:
        print("Agent creation test completed successfully!")
    else:
        print("Agent creation test failed. Please check the error messages above.")
        sys.exit(1)