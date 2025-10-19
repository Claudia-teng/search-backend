from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

# Memory for the search assistant
memory = MemorySaver()

# Search tool for the search assistant
search_tool = TavilySearchResults(max_results=4)
tools = [search_tool]

# LLM for the search assistant
search_assistant_llm = ChatOpenAI(model="gpt-4o").bind_tools(tools=tools)

SEARCH_ASSISTANT_PROMPT = """You are a helpful search assistant. 
When users ask questions, you should use the 'tavily_search_results_json' tool to search for current information.
Provide clear, concise summaries based on the search results.
Always use the search tool to get up-to-date information before answering."""
