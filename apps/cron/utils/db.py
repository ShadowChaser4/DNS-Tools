import os
from typing import Optional


from pymongo import AsyncMongoClient, MongoClient
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file if present

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "dns_tools")


__mongo_client: Optional[AsyncMongoClient] = None


async def connect_to_mongo() -> AsyncMongoClient:
    """Create a shared AsyncMongoClient and store it in the app state."""
    global __mongo_client
    if __mongo_client is None:
        __mongo_client = AsyncMongoClient(MONGODB_URI)
    return __mongo_client


async def close_mongo() -> None:
    """Close the shared AsyncMongoClient on shutdown."""
    global __mongo_client
    if __mongo_client is not None:
        await __mongo_client.close()
        __mongo_client = None


async def get_db() -> AsyncMongoClient:
    """Get the shared AsyncMongoClient instance."""
    if __mongo_client is None:
        raise RuntimeError(
            "MongoDB client is not connected. Call connect_to_mongo() first."
        )
    return __mongo_client[MONGODB_DB]
