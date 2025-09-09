#!/usr/bin/env python3
"""
Test client for the improved streaming SSE endpoint.
This demonstrates how to consume the streaming events from your DevOps agent system.
"""

import requests
import json
import uuid
import time

def test_new_sse_endpoint():
    """Test the new /chat_sse endpoint with proper ADK event handling."""
    print("\n" + "="*80)
    print("NEW SSE ENDPOINT TEST: /chat_sse")
    print("="*80)
    
    BACKEND_URL = "http://localhost:8000/chat_sse"
    
    # Test queries that should trigger various agent behaviors
    test_queries = [
        "Search for the latest Kubernetes security vulnerabilities",
        "What are the current trends in DevOps automation?",
        "Help me analyze my code repository for security issues"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}: {query}")
        print('='*60)
        
        # Prepare request payload
        payload = {
            "query": query,
            "user_id": f"test_user_{i}",
            "session_id": str(uuid.uuid4())
        }
        
        try:
            # Make streaming request
            response = requests.post(
                BACKEND_URL, 
                json=payload, 
                stream=True, 
                timeout=120,
                headers={"Accept": "text/event-stream"}
            )
            response.raise_for_status()
            
            print(f"Connected to streaming endpoint...")
            print("Receiving events:")
            print("-" * 40)
            
            event_count = 0
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data:'):
                    event_count += 1
                    event_data_str = line[len('data:'):].strip()
                    
                    if not event_data_str:
                        continue
                    
                    try:
                        event_data = json.loads(event_data_str)
                        
                        # Pretty print the event
                        print(f"Event #{event_count}:")
                        print(f"  Type: {event_data.get('event_type', 'Unknown')}")
                        print(f"  Author: {event_data.get('author', 'N/A')}")
                        
                        if event_data.get('content_text'):
                            print(f"  Content: {event_data['content_text'][:100]}...")
                            
                        if event_data.get('tool_calls'):
                            print(f"  Tool Calls: {len(event_data['tool_calls'])}")
                            for tool_call in event_data['tool_calls']:
                                print(f"    - {tool_call.get('name', 'Unknown Tool')}")
                                
                        if event_data.get('tool_responses'):
                            print(f"  Tool Responses: {len(event_data['tool_responses'])}")
                            for tool_response in event_data['tool_responses']:
                                response_text = str(tool_response.get('response', ''))
                                print(f"    - {tool_response.get('name', 'Unknown Tool')}: {response_text[:50]}...")
                                
                        if event_data.get('error_message'):
                            print(f"  ERROR: {event_data['error_message']}")
                            
                        if event_data.get('is_final_response'):
                            print("  [FINAL RESPONSE]")
                            
                        print()
                        
                    except json.JSONDecodeError:
                        print(f"  Raw data: {event_data_str}")
                        
            print(f"Stream completed. Total events received: {event_count}")
            
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
            
        # Wait between tests
        if i < len(test_queries):
            print(f"\nWaiting 2 seconds before next test...")
            time.sleep(2)

def test_simple_query():
    """Test with a simple query to verify basic functionality."""
    print("\n" + "="*80)
    print("SIMPLE TEST: Basic functionality")
    print("="*80)
    
    BACKEND_URL = "http://localhost:8000/chat_sse"
    
    payload = {
        "query": "Hello, can you help me with DevOps?",
        "user_id": "simple_test_user",
        "session_id": str(uuid.uuid4())
    }
    
    try:
        response = requests.post(
            BACKEND_URL, 
            json=payload, 
            stream=True, 
            timeout=30,
            headers={"Accept": "text/event-stream"}
        )
        response.raise_for_status()
        
        print("Receiving simple query response:")
        print("-" * 40)
        
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data:'):
                event_data_str = line[len('data:'):].strip()
                if event_data_str:
                    try:
                        event_data = json.loads(event_data_str)
                        if event_data.get('content_text'):
                            print(f"Response: {event_data['content_text']}")
                        elif event_data.get('error_message'):
                            print(f"Error: {event_data['error_message']}")
                    except json.JSONDecodeError:
                        print(f"Raw: {event_data_str}")
        
        print("Simple test completed successfully.")
        
    except Exception as e:
        print(f"Simple test failed: {e}")

def test_original_endpoint():
    """Test the original /chat/stream endpoint for comparison."""
    print("\n" + "="*80)
    print("ORIGINAL ENDPOINT TEST: /chat/stream")
    print("="*80)
    
    url = "http://localhost:8000/chat/stream"
    payload = {
        "message": "Search for latest DevOps trends and analyze my code",
        "user_id": "test_user",
        "session_id": "test_session_123"
    }
    
    try:
        response = requests.post(url, json=payload, stream=True, timeout=60)
        response.raise_for_status()
        
        print("Streaming response from original endpoint:")
        event_count = 0
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data:'):
                event_count += 1
                data = line[len('data:'):].strip()
                if data:
                    try:
                        event = json.loads(data)
                        print(f"Event #{event_count}: {event}")
                    except json.JSONDecodeError:
                        print(f"Raw data #{event_count}: {data}")
        
        print(f"Original endpoint completed. Total events: {event_count}")
    
    except Exception as e:
        print(f"Error: {e}")

def test_streaming_chat():
    """Test the streaming chat endpoint (legacy test for compatibility)."""
    url = "http://localhost:8000/chat/stream"
    
    # Test message
    payload = {
        "message": "Hello, can you help me with a DevOps task?",
        "user_id": "test_user_123",
        "session_id": None  # Will create a new session
    }
    
    print("Testing streaming chat endpoint...")
    print(f"Sending request to: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("-" * 50)
    
    try:
        # Send POST request with streaming
        with requests.post(url, json=payload, stream=True) as r:
            r.raise_for_status()
            print("Response received. Streaming data:")
            print("-" * 50)
            
            # Process the streaming response
            for line in r.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: '):
                        # Parse the JSON data
                        json_data = json.loads(decoded_line[6:])  # Remove 'data: ' prefix
                        print(f"Event: {json_data}")
                        
        print("-" * 50)
        print("Streaming completed successfully!")
        
    except requests.exceptions.RequestException as e:
        print(f"Error during request: {e}")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    print("🧪 Testing Improved Streaming Implementation")
    print("Make sure your DevOps agent server is running on localhost:8000")
    print("\nStarting tests...")
    
    # Test simple query first
    test_simple_query()
    
    # Test original endpoint for comparison  
    test_original_endpoint()
    
    # Then test complex queries with new endpoint
    test_new_sse_endpoint()
    
    print("\n🎉 Testing completed!")
