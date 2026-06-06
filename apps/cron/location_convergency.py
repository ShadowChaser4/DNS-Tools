import httpx
import logging  
from beanie.odm.operators.update.general import Set

from dns_models import DnsServerRecord, GeoPoint, Location
from apps.cron.utils import Cache

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

async def update_location():
    """Update location for all DNS servers that are missing it."""
    from beanie import init_beanie
    from apps.cron.utils.db import connect_to_mongo, close_mongo, MONGODB_DB
    from apps.cron.helper.location import LocationHelper

    client = await connect_to_mongo()
    await init_beanie(
        database=client[MONGODB_DB], document_models=[DnsServerRecord, Location]
    )
    location_helper = LocationHelper(cache=Cache(), client=httpx.AsyncClient())

    # Find all records missing location
    pairs = await DnsServerRecord.aggregate(
        [
            {
                "$group": {
                    "_id": {
                        "city": "$city",
                        "country": "$country",
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "city": "$_id.city",
                    "country": "$_id.country",
                }
            },
        ]
    ).to_list()
    logger.info(
        f"Found {len(pairs)} unique city-country pairs to update location for",
        pairs[:5],
    )
    for pair in pairs:
        city = pair.get("city")
        country = pair.get("country") or ""
        if not city and not country:
            continue
        location = await location_helper.get_location(city, country)
        if location:
            logger.info(f"Updating location for {city}, {country} to {location}")
            geo_point = GeoPoint(coordinates=[location[1], location[0]])
            await DnsServerRecord.find(
                DnsServerRecord.city == city,
                DnsServerRecord.country == country,
            ).update(Set({"location": geo_point}))
    await close_mongo()
