## 🔄 Changes from Previous Version

- **Multi-round conversations**: Added support for multiple rounds of back-and-forth conversation for iterative searching and refinement and
- **Framework migration**: Migrated from AG2 to LangGraph for better streaming support and state management
- **Search provider update**: Switched from SerpAPI to Tavily for AI-optimized search results with better LangChain integration
- **Streaming architecture**: Implemented Server-Sent Events (SSE) for real-time response streaming

## 🏗️ Architecture

### Why LangGraph over AG2?

Migrated from AG2 to LangGraph for the following reasons:

- **AG2's WebSocket limitation**: The previous implementation using [AG2's WebSocket approach](https://docs.ag2.ai/latest/docs/use-cases/notebooks/notebooks/agentchat_websockets/) has a critical flaw - `on_connect` executes only once, which doesn't support multiple rounds of conversation (asking and answering repeatedly).

- **Built-in SSE support**: LangGraph provides native Server-Sent Events (SSE) streaming via `astream_events()`, which perfectly fits our streaming requirements.

### System Architecture

```
Client → FastAPI (app.py) → Streaming Layer (streaming.py) → LangGraph (graph.py)
                                                                    ↓
                                                          ┌─────────────────┐
                                                          │  2 Agents:      │
                                                          │  • user_proxy   │
                                                          │  • search_asst  │
                                                          └─────────────────┘
                                                                    ↓
                                                          ┌─────────────────┐
                                                          │ Tool Executor   │
                                                          │ • Tavily Search │
                                                          └─────────────────┘
```

**Agent Flow:**

1. `user_proxy` - Coordinator agent (entry point)
2. `search_assistant` - GPT-4o powered agent with tool-calling capabilities
3. `tool_node` - Tool executor for Tavily search

## 💾 Memory

### Development (Current)

- **MemorySaver**: Built-in in-memory checkpointing for conversation history
- Thread-based state persistence using UUID checkpoint IDs
- Suitable for development and testing

### Production (Recommended)

For production deployments, migrate to **PostgreSQL Saver**:

- **Short-term memory**: Recent conversation context
- **Long-term memory**: Historical user interactions
- **Pagination**: Efficient handling of large conversation histories

## 🔍 Search API

### Why Tavily over SerpAPI?

**Tavily Search API** is used over SerpAPI for these reasons:

| Feature                   | Tavily                                             | SerpAPI                            |
| ------------------------- | -------------------------------------------------- | ---------------------------------- |
| **AI-Optimized**          | ✅ Specifically designed for LLM/AI agents         | ❌ General-purpose search scraping |
| **Response Format**       | Clean, structured JSON perfect for LLM consumption | Raw HTML/complex nested data       |
| **Content Quality**       | Pre-processed, relevant snippets                   | Requires additional parsing        |
| **LangChain Integration** | Native `TavilySearchResults` tool                  | Manual implementation needed       |
| **Speed**                 | Optimized for AI workflows                         | Generic web scraping speed         |

Tavily is built specifically for AI agents and returns clean, contextual results that GPT-4o can directly use without extensive preprocessing.

## 🚀 Installation and Start

### Prerequisites

- Python
- OpenAI API key
- Tavily API key

### Setup

1. **Clone the repository**

```bash
git clone <repository-url>
cd search-backend
```

2. **Create and activate virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

5. **Start the server**

```bash
uvicorn app:app --reload
```

The API will be available at `http://localhost:8000`

## 📡 API Endpoints

### `GET /chat_stream/{message}`

Streaming chat endpoint with conversational memory.

**Parameters:**

- `message` (path) - User's input message
- `checkpoint_id` (query, optional) - Conversation thread ID for continuing existing conversations

**Response:** Server-Sent Events (SSE) stream

**SSE Event Types:**

- `checkpoint` - New conversation checkpoint ID (first message only)
- `content` - Streaming AI response chunks
- `search_start` - Search initiated with query
- `search_results` - URLs from search results
- `end` - Response complete

**Example:**

```bash
# New conversation
curl "http://localhost:8000/chat_stream/What%20is%20LangGraph?"

# Continue conversation
curl "http://localhost:8000/chat_stream/Tell%20me%20more?checkpoint_id=abc-123-def-456"
```

**SSE Stream Example:**

## 🛠️ Project Structure

```
search-backend/
├── app.py              # FastAPI application and routes
├── streaming.py        # SSE event generation and streaming logic
├── graph.py            # LangGraph workflow and agent definitions
├── config.py           # Configuration (LLM, tools, memory, prompts)
├── utils.py            # Helper functions (serialization, parsing)
├── requirements.txt    # Python dependencies
├── .env                # Environment variables (not in repo)
└── README.md          # This file
```

## 📚 Reference

https://github.com/harishneel1/perplexity_2.0
