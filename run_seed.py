"""
Run the API seeder from the project root.

Usage:
    python run_seed.py

This imports the `apps.api.utils.seed` module (so the package context is correct)
and runs its `seed_data` coroutine.
"""

import asyncio
from fastapi import FastAPI

from apps.api.utils import seed
from apps.api.core import connect_to_mongo, close_mongo


async def main_async() -> None:
    app = FastAPI()
    await connect_to_mongo(app)
    try:
        await seed.seed_data(app)
    finally:
        await close_mongo(app)


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
