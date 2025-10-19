import ast
import json
from typing import Optional
from uuid import uuid4

from langchain_core.messages import HumanMessage

from graph import graph
from utils import extract_urls_from_search_results, serialise_ai_message_chunk


async def generate_chat_responses(message: str, checkpoint_id: Optional[str] = None):
    """
    Generate streaming chat responses with search capabilities.

    Yields SSE events:
    - checkpoint: New conversation checkpoint ID
    - content: Streaming AI response chunks
    - search_start: Search initiated with query
    - search_results: URLs from search results
    - end: Response complete

    Args:
        message: User's input message
        checkpoint_id: Optional conversation checkpoint ID for continuing conversations

    Yields:
        str: Server-Sent Events formatted strings
    """
    is_new_conversation = checkpoint_id is None

    if is_new_conversation:
        # Generate new checkpoint ID for first message in conversation
        new_checkpoint_id = str(uuid4())
        config = {"configurable": {"thread_id": new_checkpoint_id}}

        # Initialize with first message
        events = graph.astream_events(
            {"messages": [HumanMessage(content=message)]}, version="v2", config=config
        )

        # Send the checkpoint ID
        checkpoint_data = f'data: {{"type": "checkpoint", "checkpoint_id": "{new_checkpoint_id}"}}\n\n'
        print(f"Yielding: {checkpoint_data.strip()}")
        yield checkpoint_data
    else:
        # Continue existing conversation
        config = {"configurable": {"thread_id": checkpoint_id}}
        events = graph.astream_events(
            {"messages": [HumanMessage(content=message)]}, version="v2", config=config
        )

    async for event in events:
        event_type = event["event"]

        # Stream AI response tokens
        if event_type == "on_chat_model_stream":
            chunk_content = serialise_ai_message_chunk(event["data"]["chunk"])

            # Skip empty chunks
            if chunk_content:
                # Escape special characters for safe JSON parsing
                safe_content = chunk_content.replace("'", "\\'").replace("\n", "\\n")
                content_data = (
                    f'data: {{"type": "content", "content": "{safe_content}"}}\n\n'
                )
                print(f"Yielding: {content_data.strip()}")
                yield content_data

        # Detect when search is initiated
        elif event_type == "on_chat_model_end":
            tool_calls = (
                event["data"]["output"].tool_calls
                if hasattr(event["data"]["output"], "tool_calls")
                else []
            )
            search_calls = [
                call
                for call in tool_calls
                if call["name"] == "tavily_search_results_json"
            ]

            if search_calls:
                # Signal that a search is starting
                search_query = search_calls[0]["args"].get("query", "")
                safe_query = (
                    search_query.replace('"', '\\"')
                    .replace("'", "\\'")
                    .replace("\n", "\\n")
                )
                search_start_data = (
                    f'data: {{"type": "search_start", "query": "{safe_query}"}}\n\n'
                )
                print(f"Yielding: {search_start_data.strip()}")
                yield search_start_data

        # Extract and send search result URLs
        elif event_type == "on_chain_end" and event.get("name") == "tool_node":
            try:
                output = event["data"]["output"]
                messages = output.get("messages", [])

                for msg in messages:
                    # Check if this is a ToolMessage with search results
                    if (
                        hasattr(msg, "name")
                        and msg.name == "tavily_search_results_json"
                    ):
                        # Parse the string representation of search results
                        search_results = ast.literal_eval(msg.content)

                        # Extract URLs from search results
                        urls = extract_urls_from_search_results(search_results)

                        if urls:
                            # Send URLs to client
                            urls_json = json.dumps(urls)
                            search_results_data = f'data: {{"type": "search_results", "urls": {urls_json}}}\n\n'
                            print(f"Yielding: {search_results_data.strip()}")
                            yield search_results_data
            except Exception:
                pass  # Silently handle any parsing errors

    # Send end event
    end_data = f'data: {{"type": "end"}}\n\n'
    print(f"Yielding: {end_data.strip()}")
    yield end_data
