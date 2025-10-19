from langchain_core.messages import AIMessageChunk


def serialise_ai_message_chunk(chunk):
    """
    Serialize AIMessageChunk to string content.

    Args:
        chunk: AIMessageChunk object from LangChain

    Returns:
        str: Content of the chunk

    Raises:
        TypeError: If chunk is not an AIMessageChunk
    """
    if isinstance(chunk, AIMessageChunk):
        return chunk.content
    else:
        raise TypeError(
            f"Object of type {type(chunk).__name__} is not correctly formatted for serialisation"
        )


def extract_urls_from_search_results(search_results):
    """
    Extract URLs from Tavily search results.

    Args:
        search_results: List of search result dictionaries

    Returns:
        list: List of URLs extracted from search results
    """
    urls = []
    if isinstance(search_results, list):
        for item in search_results:
            if isinstance(item, dict) and "url" in item:
                urls.append(item["url"])
    return urls
