import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from backend.core.database import Base, get_db
from backend.main import app

# Each test module gets isolated via its own DB file set in the module itself.
# This conftest just suppresses the loop scope warning.
pytest_plugins = ["pytest_asyncio"]
