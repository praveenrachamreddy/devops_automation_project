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

"""Example script to run the DevOps Automation Assistant."""

import sys
import os

# Add the project root to the path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from devops_agent_system.agent import root_agent

async def main():
    """Run the DevOps Automation Assistant."""
    print("DevOps Automation Assistant")
    print("=" * 30)
    print("Type 'quit' to exit the conversation")
    print()
    
    # Simple conversation loop
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Assistant: Goodbye!")
                break
                
            # Process the user input with the agent
            response = await root_agent.run_async(user_input)
            print(f"Assistant: {response}")
            print()
            
        except KeyboardInterrupt:
            print("\nAssistant: Goodbye!")
            break
        except Exception as e:
            print(f"Assistant: Sorry, I encountered an error: {e}")
            print()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())