import httpx

from ..utils import Cache

cache = Cache()


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
        async with httpx.AsyncClient() as client:
            params = {
                "q": get_key(city, country),
                "format": "json",
            }
            response = await client.get(URL, params=params, timeout=10)
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
