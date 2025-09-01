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

"""Tools for interacting with the session state."""

from google.adk.tools import ToolContext

def save_note(note_name: str, note_content: str, tool_context: ToolContext) -> str:
    """Saves a key-value pair as a note in the current session state.

    Use this to remember information provided by the user during the conversation.

    Args:
        note_name: The name (key) of the note to save.
        note_content: The content (value) of the note to save.
        tool_context: The context object provided by the ADK.

    Returns:
        A string confirming that the note was saved.
    """
    # The ADK automatically tracks changes to the state dictionary.
    # We can simply modify it directly.
    if "notes" not in tool_context.state:
        tool_context.state["notes"] = {}
    
    tool_context.state["notes"][note_name] = note_content
    return f"Note '{note_name}' saved successfully."