from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from streaming import generate_chat_responses

app = FastAPI(
    title="Search Assistant API",
    description="AI-powered search assistant with streaming responses",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type"],
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Search Assistant API",
        "version": "1.0.0",
        "endpoints": {
            "chat_stream": "/chat_stream/{message}",
        },
    }


@app.get("/chat_stream/{message}")
async def chat_stream(message: str, checkpoint_id: Optional[str] = Query(None)):
    """
    Streaming chat endpoint that accepts a message and optional checkpoint_id.

    Args:
        message: User's input message
        checkpoint_id: Optional conversation checkpoint ID for continuing conversations

    Returns:
        StreamingResponse: Server-Sent Events (SSE) stream with chat responses

    SSE Event Types:
        - checkpoint: New conversation checkpoint ID
        - content: Streaming AI response chunks
        - search_start: Search initiated with query
        - search_results: URLs from search results
        - end: Response complete
    """
    return StreamingResponse(
        generate_chat_responses(message, checkpoint_id), media_type="text/event-stream"
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
