import time
from langchain_core.tools import tool
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import RatelimitException


@tool
def web_search(query: str) -> str:
    """Search the web for current information on a topic."""
    delays = [2, 5, 10]
    for attempt, delay in enumerate(delays + [None]):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))
            if not results:
                return "No results found."
            return "\n\n".join(
                f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}"
                for r in results
            )
        except RatelimitException:
            if delay is None:
                return "Search unavailable due to rate limiting. Please try again in a minute."
            time.sleep(delay)
