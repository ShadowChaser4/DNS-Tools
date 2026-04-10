"""MongoDB connection helpers and FastAPI dependency.

Provides:
- `get_db()` dependency (yield) that provides an `AsyncMongoClient` for request handlers.

Usage:
1. In your FastAPI app, call `connect_to_mongo` on startup and `
close_mongo` on shutdown to manage the shared client lifecycle.
2. Use `get_db` as a dependency in your routers to access the database.

Example:
```python
from fastapi import FastAPI, Depends
from .db import connect_to_mongo, close_mongo, get_db
app = FastAPI()

def lifespan(app: FastAPI):
    await connect_to_mongo(app)
    try:
        yield
    finally:
        await close_mongo()


@app.get("/items/")
async def read_items(db=Depends(get_db)):
    items = await db["items"].find().to_list(100)
    return items

```
"""

from __future__ import annotations

import os
from typing import AsyncGenerator, Optional

from fastapi import FastAPI
from pymongo import AsyncMongoClient

from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file if present

# Configuration via env vars (override in your deployment)
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "dns_tools")

# Shared client (created on startup)
_mongo_client: Optional[AsyncMongoClient] = None


async def connect_to_mongo(app: FastAPI) -> None:
    """Create a shared AsyncMongoClient and store it in the app state."""
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = AsyncMongoClient(MONGODB_URI)
        app.state.mongo_client = _mongo_client
        app.state.mongo_db = _mongo_client[MONGODB_DB]


async def close_mongo(app: FastAPI) -> None:
    """Close the shared AsyncMongoClient on shutdown."""
    global _mongo_client
    if _mongo_client is not None:
        await _mongo_client.close()
        _mongo_client = None
        app.state.mongo_client = None
        app.state.mongo_db = None


async def get_db() -> AsyncGenerator[AsyncMongoClient, None]:
    """FastAPI dependency that yields an `AsyncMongoClient`.

    If the shared client was not created (e.g., startup not wired), this
    creates a short-lived client for the scope of the dependency and closes
    it afterwards.
    """
    if _mongo_client is None:
        client = AsyncMongoClient(MONGODB_URI)
        try:
            yield client[MONGODB_DB]
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise e
        finally:
            client.close()
    else:
        yield _mongo_client[MONGODB_DB]


def get_client() -> Optional[AsyncMongoClient]:
    """Return the shared motor client (or None if not connected)."""
    return _mongo_client


__all__ = ["connect_to_mongo", "close_mongo", "get_db", "get_client"]
