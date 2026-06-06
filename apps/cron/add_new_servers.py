import asyncio
import logging

from .location_convergency import update_location
from .dns_fetcher import  fetch_dns_servers


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

async def main(): 
    try: 
        await fetch_dns_servers()
        logger.info("Successfully fetched DNS servers and updated MongoDB")
    except Exception as e:
        logger.error(f"Error fetching DNS servers: {e}", exc_info=True)
    try:
        await update_location()
        logger.info("Successfully updated locations for DNS servers")
    except Exception as e:
        logger.error(f"Error updating locations: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
    
    