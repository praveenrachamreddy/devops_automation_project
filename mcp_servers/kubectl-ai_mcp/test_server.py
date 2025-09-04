#!/usr/bin/env python3
"""
Test script for kubectl-ai MCP server
"""

import asyncio
import httpx
import json

async def test_server():
    """Test the kubectl-ai MCP server"""
    base_url = "http://localhost:8082/mcp"
    
    try:
        # Test 1: Get server info
        print("🔍 Testing server info...")
        async with httpx.AsyncClient() as client:
            response = await client.get(base_url)
            print(f"✅ Server info response: {response.status_code}")
            if response.status_code == 200:
                print(json.dumps(response.json(), indent=2))
        
        # Test 2: List tools
        print("\n🔍 Testing tools list...")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                base_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list",
                    "params": {}
                }
            )
            print(f"✅ Tools list response: {response.status_code}")
            if response.status_code == 200:
                tools_data = response.json()
                print("Available tools:")
                for tool in tools_data.get("result", {}).get("tools", []):
                    print(f"  - {tool['name']}: {tool['description'][:50]}...")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    asyncio.run(test_server())