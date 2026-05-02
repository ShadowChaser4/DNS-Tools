from ..core import initialize_odm
from ..dns.models import DnsServerRecord

DNS_SEVERS = [
    {
        "name": "Cloudflare DNS",
        "ips": ["1.1.1.1", "1.0.0.1"],
        "country": "US",
        "city": "San Francisco",
        "reputation": 98.5,
        "reliability": 99.9,
        "location": {"type": "Point", "coordinates": [-122.4194, 37.7749]},
    },
    {
        "name": "Google Public DNS",
        "ips": ["8.8.8.8", "8.8.4.4"],
        "country": "US",
        "city": "Mountain View",
        "reputation": 97.0,
        "reliability": 99.8,
        "location": {"type": "Point", "coordinates": [-122.0839, 37.3861]},
    },
    {
        "name": "OpenDNS",
        "ips": ["208.67.222.222", "208.67.220.220"],
        "country": "US",
        "city": "Austin",
        "reputation": 95.0,
        "reliability": 99.7,
        "location": {"type": "Point", "coordinates": [-97.7431, 30.2672]},
    },
    {
        "name": "Md Masud Rana Roni t/a RV Cyber World",
        "ips": ["103.157.237.34"],
        "country": "Bangladesh",
        "city": "Dhaka",
        "reputation": 85.0,
        "reliability": 72.0,
        "location": {"type": "Point", "coordinates": [90.4125, 23.8103]},
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
    if await DnsServerRecord.count() == 0:
        docs = [DnsServerRecord(**data) for data in DNS_SEVERS]
        await DnsServerRecord.insert_many(docs)
