from itertools import count


from ..core import initialize_odm
from ..dns.models import DnsServer

DNS_SEVERS = [
    {
        "name": "Cloudflare DNS",
        "ips": ["1.1.1.1", "1.0.0.1"],
        "country": "US",
        "reputation": 98.5,
        "reliability": 99.9,
    },
    {
        "name": "Google Public DNS",
        "ips": ["8.8.8.8", "8.8.4.4"],
        "country": "US",
        "reputation": 97.0,
        "reliability": 99.8,
    },
    {
        "name": "OpenDNS",
        "ips": ["208.67.222.222", "208.67.220.220"],
        "country": "US",
        "reputation": 95.0,
        "reliability": 99.7,
    },
]

async def seed_data(app) -> None:
    """Seed the database with initial data.

    Expects `app` with `state.mongo_db` already set (see `connect_to_mongo`).
    """
    db = getattr(app.state, "mongo_db", None)
    if db is None:
        raise RuntimeError("MongoDB is not connected on app.state.mongo_db")

    await initialize_odm(db)
    if await DnsServer.count() == 0:
        docs = [DnsServer(**data) for data in DNS_SEVERS]
        await DnsServer.insert_many(docs)
