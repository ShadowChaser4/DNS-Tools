import httpx
import asyncio

from utils import Cache

cache = Cache()


import time


def acquire_lock(
    key: str = "geocoding", timeout: int = 10, wait: int = 30, interval: float = 0.2
) -> bool:
    """
    Try to acquire a Redis lock, waiting until it becomes available.

    - timeout: lock expiry in Redis
    - wait: max time to wait for lock acquisition
    - interval: retry delay
    """
    lock_key = f"lock:{key}"
    start = time.time()

    while True:
        if cache.set(lock_key, "1", ex=timeout, nx=True):
            return True

        if time.time() - start > wait:
            return False  # gave up

        time.sleep(interval)


def get_key(city: str, country: str) -> str:
    """Generate a Redis key for caching location data."""
    return f"{city},{country}" if city and len(city) > 0 else country


async def get_lat_long_from_cache(
    city: str, country: str
) -> tuple[float, float] | None:
    """Get latitude and longitude from Redis cache."""
    key = f"location:{get_key(city, country)}"
    cached_value = cache.get(key)
    if cached_value:
        try:
            lat_str, lon_str = cached_value.split(",")
            return float(lat_str), float(lon_str)
        except ValueError:
            print(f"Invalid cache format for {key}: {cached_value}")
            return None
    return None


async def get_lat_long_from_city_country(
    city: str, country: str
) -> tuple[float, float] | None:
    """Get latitude and longitude from city and country using geopy."""
    URL = "https://nominatim.openstreetmap.org/search"
    try:
        acquire_lock()
        async with httpx.AsyncClient() as client:
            params = {
                "q": get_key(city, country),
                "format": "json",
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 CrKey/1.54.250320"
            }
            response = await client.get(URL, params=params, timeout=10, headers=headers)
            if response.status_code == 429:
                print(f"Rate limited by geocoding API for {city}, {country}")
                return None
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except httpx.HTTPError as e:
        print(f"Failed to get lat/long for {city}, {country}: {e}")
    return None


__all__ = ["get_lat_long_from_cache", "get_lat_long_from_city_country"]
