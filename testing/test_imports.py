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

"""Test script to verify the DevOps Automation Assistant setup."""

import sys
import os

# Add the project root to the path
project_root = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.dirname(project_root)
sys.path.insert(0, parent_dir)

def test_imports():
    """Test that all modules can be imported successfully."""
    try:
        # Test base agent import
        from devops_agent_system.agents.base_agent import BaseAgent
        print("[PASS] BaseAgent imported successfully")
        
        # Test search agent import
        from devops_agent_system.agents.sub_agents.search_agent import search_agent
        print("[PASS] SearchAgent imported successfully")
        
        # Test coding agent import
        from devops_agent_system.agents.sub_agents.coding_agent import coding_agent
        print("[PASS] CodingAgent imported successfully")
        
        # Test elasticsearch agent import
        from devops_agent_system.agents.sub_agents.elasticsearch_agent import elasticsearch_agent
        print("[PASS] ElasticsearchAgent imported successfully")
        
        # Test session tools import
        from devops_agent_system.tools.session_tools import save_note
        print("[PASS] Session tools imported successfully")
        
        # Test main agent import
        from devops_agent_system.agent import root_agent
        print("[PASS] Root agent imported successfully")
        
        print("\nAll imports successful! The basic structure is working correctly.")
        return True
        
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing DevOps Automation Assistant setup...")
    print("=" * 50)
    
    success = test_imports()
    
    print("=" * 50)
    if success:
        print("Setup verification completed successfully!")
    else:
        print("Setup verification failed. Please check the error messages above.")
        sys.exit(1)