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

import requests
import json
import uuid
import sys

# --- Configuration ---
SERVER_URL = "http://localhost:8000/chat"
USER_ID = "test_user_001"  # Hardcoded user ID for testing

def main():
    print("--- DevOps Agent Test Client ---")
    print("Connecting to server at:", SERVER_URL)

    session_id = str(uuid.uuid4())
    print(f"Generated new session_id: {session_id}")
    print("Type 'exit' or 'quit' to end the session.")
    print("-" * 30)

    while True:
        try:
            query = input("You: ")
            if query.lower() in ['exit', 'quit']:
                print("Ending session. Goodbye!")
                break

            payload = {
                "user_id": USER_ID,
                "session_id": session_id,
                "query": query
            }

            with requests.post(SERVER_URL, json=payload, stream=True, timeout=300) as response:
                response.raise_for_status()

                print("Agent: ", end="")
                sys.stdout.flush()

                for line in response.iter_lines():
                    if line:
                        try:
                            event = json.loads(line.decode('utf-8'))

                            # Handle error event
                            if "error" in event:
                                print(f"\n[ERROR]: {event['error']}")
                                break

                            # Print text content as it arrives
                            content_parts = event.get("content", [])
                            if content_parts:
                                print(" ".join(content_parts), end=" ")
                                sys.stdout.flush()

                        except json.JSONDecodeError:
                            print(f"\n[ERROR] Failed to decode JSON line: {line.decode('utf-8')}", file=sys.stderr)

                print()  # Newline after full agent response

        except requests.exceptions.RequestException as e:
            print(f"\n[ERROR] Cannot connect to the server: {e}")
            print("Ensure the FastAPI server is running (e.g., `python main.py`).")
            break
        except KeyboardInterrupt:
            print("\nEnding session. Goodbye!")
            break

if __name__ == "__main__":
    main()
