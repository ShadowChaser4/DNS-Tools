"""
Run the API seeder from the project root.

Usage:
    python run_seed.py

This imports the `apps.api.utils.seed` module (so the package context is correct)
and runs its `seed_data` coroutine.
"""

import asyncio

from apps.api.utils import seed
from apps.api.core import connect_to_mongo, close_mongo


async def main_async() -> None:
    await connect_to_mongo()
    try:
        await seed.seed_data()
    finally:
        await close_mongo()



def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
