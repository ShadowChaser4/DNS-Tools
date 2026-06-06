import httpx
import logging  
from beanie.odm.operators.update.general import Set

from dns_models import DnsServerRecord, GeoPoint, Location
from apps.cron.utils import Cache
from apps.cron.helper.location import LocationHelper

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)


async def get_location_and_update_pairs(pairs): 
    """
    Get location information for each city-country pair and return updated pairs.

    """
    client = httpx.AsyncClient()
    cache = Cache()
    location_helper = LocationHelper(cache=cache, client=client)

    for pair in pairs:
        city = pair.get("city")
        country = pair.get("country") or ""
        if not city and not country:
            continue
        try: 
            location = await location_helper.get_location(city, country)
            if location:
                logger.info(f"Updating location for {city}, {country} to {location}")
                geo_point = GeoPoint(coordinates=[location.longitude, location.latitude])
                await DnsServerRecord.find(
                    DnsServerRecord.city == city,
                    DnsServerRecord.country == country,
                ).update(Set({"location": geo_point}))
        except Exception as e:
            logger.error(f"Error updating location for {city}, {country}: {e}", exc_info=True)
    await client.aclose()

async def update_location():
    """Update location for all DNS servers that are missing it."""
    from beanie import init_beanie
    from apps.cron.utils.db import connect_to_mongo, close_mongo, MONGODB_DB
    
    client = await connect_to_mongo()
    await init_beanie(
        database=client[MONGODB_DB], document_models=[DnsServerRecord, Location]
    )
    
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
    await get_location_and_update_pairs(pairs)
    
    await close_mongo()


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    asyncio.run(update_location())
