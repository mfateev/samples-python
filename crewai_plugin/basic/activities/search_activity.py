"""Search activity for CrewAI samples.

This activity simulates a web search. In a real implementation,
you would use an actual search API (e.g., Serper, Google, DuckDuckGo).
"""

from temporalio import activity


@activity.defn
async def search_web(query: str) -> str:
    """Search the web for information.

    This is a simulated search activity. In production, replace this
    with a real search API implementation.

    Args:
        query: The search query

    Returns:
        Simulated search results
    """
    # Heartbeat to show activity is making progress
    activity.heartbeat(f"Searching for: {query}")

    # Simulated search results
    # In production, use a real search API like:
    # - Serper API (https://serper.dev/)
    # - DuckDuckGo Search
    # - Google Custom Search API
    return f"""Search Results for: "{query}"

1. **Introduction to {query}**
   A comprehensive overview of {query} covering the fundamentals
   and key concepts that every beginner should know.
   Source: example.com/intro-{query.replace(' ', '-').lower()}

2. **Advanced {query} Techniques**
   Deep dive into advanced topics and best practices for
   working with {query} in production environments.
   Source: example.com/advanced-{query.replace(' ', '-').lower()}

3. **{query} in 2024: Trends and Predictions**
   Expert analysis of current trends and future predictions
   for {query} in the coming year.
   Source: example.com/trends-{query.replace(' ', '-').lower()}
"""
