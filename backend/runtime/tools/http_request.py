import httpx
from langchain_core.tools import tool


@tool
def http_request(url: str, method: str = "GET", body: str = "") -> str:
    """Make an HTTP request to any URL. Method: GET or POST."""
    try:
        with httpx.Client(timeout=10) as client:
            if method.upper() == "POST":
                resp = client.post(url, content=body)
            else:
                resp = client.get(url)
        return f"Status: {resp.status_code}\nBody: {resp.text[:2000]}"
    except Exception as e:
        return f"Request failed: {e}"
