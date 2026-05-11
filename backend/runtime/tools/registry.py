from .web_search import web_search
from .scrape_url import scrape_url
from .http_request import http_request

TOOL_REGISTRY = {
    "web_search": web_search,
    "scrape_url": scrape_url,
    "http_request": http_request,
}


def get_tools(tool_names: list[str]):
    return [TOOL_REGISTRY[name] for name in tool_names if name in TOOL_REGISTRY]
