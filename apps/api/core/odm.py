from beanie import init_beanie
from pymongo import AsyncMongoClient

from ..dns.documents import docs as dns_docs

all_docs = dns_docs


async def initialize_odm(db: AsyncMongoClient) -> None:
    """Initialize Beanie ODM with the MongoDB database."""

    await init_beanie(db, document_models=all_docs)


__all__ = ["initialize_odm"]
