import os
from backend.core.config import get_settings

settings = get_settings()

os.environ.setdefault("LANGFUSE_PUBLIC_KEY", settings.langfuse_public_key)
os.environ.setdefault("LANGFUSE_SECRET_KEY", settings.langfuse_secret_key)
host = settings.langfuse_base_url or settings.langfuse_host
os.environ.setdefault("LANGFUSE_HOST", host)

from langfuse import get_client  


def get_langfuse():
    return get_client()
