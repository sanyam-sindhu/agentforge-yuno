import httpx
from bs4 import BeautifulSoup
from langchain_core.tools import tool


@tool
def scrape_url(url: str) -> str:
    """Fetch and extract readable text content from a URL."""
    try:
        response = httpx.get(url, timeout=5, follow_redirects=True)
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return text[:1500]
    except Exception as e:
        return f"Failed to scrape URL: {e}"
