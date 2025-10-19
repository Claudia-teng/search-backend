from typing import Annotated, TypedDict

from langchain_core.messages import SystemMessage, ToolMessage
from langgraph.graph import END, StateGraph, add_messages

from config import SEARCH_ASSISTANT_PROMPT, memory, search_assistant_llm, search_tool

# ============================================================================
# STATE DEFINITION
# ============================================================================


class State(TypedDict):
    """Graph state containing conversation messages."""

    messages: Annotated[list, add_messages]


# ============================================================================
# AGENT NODES
# ============================================================================


async def user_proxy(state: State):
    """
    User proxy agent that acts as a coordinator between user and search assistant.
    Simply passes through messages.

    Args:
        state: Current graph state

    Returns:
        State: Unchanged state
    """
    return state


async def search_assistant(state: State, config):
    """
    Search assistant agent that processes queries and calls search tools when needed.
    Adds system message if not present and invokes the LLM with tools.

    Args:
        state: Current graph state
        config: Runtime configuration for streaming

    Returns:
        dict: Updated state with AI response
    """
    messages = state["messages"]

    # Add system message if not already present
    if not messages or not any(
        hasattr(m, "type") and m.type == "system" for m in messages
    ):
        messages = [SystemMessage(content=SEARCH_ASSISTANT_PROMPT)] + messages

    # Pass config to ainvoke to enable proper streaming
    result = await search_assistant_llm.ainvoke(messages, config=config)
    return {"messages": [result]}


async def tool_node(state):
    """
    Tool execution node that handles tool calls from the LLM.
    Currently supports tavily_search_results_json tool.

    Args:
        state: Current graph state

    Returns:
        dict: Updated state with tool results
    """
    tool_calls = state["messages"][-1].tool_calls
    tool_messages = []

    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call["id"]

        # Handle the search tool
        if tool_name == "tavily_search_results_json":
            search_results = await search_tool.ainvoke(tool_args)

            tool_message = ToolMessage(
                content=str(search_results), tool_call_id=tool_id, name=tool_name
            )
            tool_messages.append(tool_message)

    return {"messages": tool_messages}


# ============================================================================
# ROUTER FUNCTIONS
# ============================================================================


async def user_proxy_router(state: State):
    """
    Router for user_proxy to decide next step.
    Routes to search_assistant for new queries, or END when response is complete.

    Args:
        state: Current graph state

    Returns:
        str: Next node name or END
    """
    messages = state["messages"]

    # Check if we just received a final response from search_assistant
    if len(messages) > 1:
        last_message = messages[-1]
        if hasattr(last_message, "type") and last_message.type == "ai":
            # If AI message has no pending tool calls, we're done
            if not (hasattr(last_message, "tool_calls") and last_message.tool_calls):
                return END

    # Otherwise, route to search_assistant
    return "search_assistant"


async def tools_router(state: State):
    """
    Router that decides if we need to call tools or return to user_proxy.
    Checks if the last message contains tool calls.

    Args:
        state: Current graph state

    Returns:
        str: "tool_node" or "user_proxy"
    """
    last_message = state["messages"][-1]

    if hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0:
        return "tool_node"
    else:
        return "user_proxy"


# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================


def build_graph():
    """
    Build and compile the agent graph.

    Returns:
        CompiledGraph: The compiled LangGraph
    """
    graph_builder = StateGraph(State)

    # Add nodes for both agents and tool execution
    graph_builder.add_node("user_proxy", user_proxy)
    graph_builder.add_node("search_assistant", search_assistant)
    graph_builder.add_node("tool_node", tool_node)

    # Set entry point to user_proxy
    graph_builder.set_entry_point("user_proxy")

    # Define the flow:
    # user_proxy -> [search_assistant or END]
    # search_assistant -> [tool_node or user_proxy]
    # tool_node -> search_assistant
    graph_builder.add_conditional_edges("user_proxy", user_proxy_router)
    graph_builder.add_conditional_edges("search_assistant", tools_router)
    graph_builder.add_edge("tool_node", "search_assistant")

    # Compile the graph with memory checkpointing
    return graph_builder.compile(checkpointer=memory)


# Create the compiled graph instance
graph = build_graph()
