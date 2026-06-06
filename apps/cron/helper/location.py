from dataclasses import dataclass
from dotenv import get_key
import httpx
import asyncio

from apps.cron.utils import Cache
from dns_models import Location

@dataclass
class Coordinates:
    latitude: float
    longitude: float

class LocationHelper:

    def __init__(self, cache: Cache, client: httpx.AsyncClient):
        self.cache = cache 
        self.client = client 

    def _cache_key(self, city: str, country: str) -> str:
        return f"{city}_{country}"

    async def _acquire_lock(self, key: str):
        """Acquire a lock to prevent multiple concurrent calls to the geocoding API."""
        cache_key = "lock:" + key
        while self.cache.get(cache_key):
            print("Waiting for geocoding lock to be released...")
            await asyncio.sleep(1)
        await self.cache.set(cache_key, True, expire_seconds=2, nx=True) # Set lock with a short TTL to prevent deadlocks

    async def _call_nota(self, city: str, country: str) -> list[float, float] | None:
        """Call the NOTA API to get the latitude and longitude for a given city and country."""
        """Get latitude and longitude from city and country using geopy."""
        URL = "https://nominatim.openstreetmap.org/search"
        try:
            await self._acquire_lock('nominatim')
            
            params = {
                "q": get_key(city, country),
                "format": "json",
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 CrKey/1.54.250320"
            }
            response = await self.client.get(URL, params=params, timeout=10, headers=headers)
            if response.status_code == 429:
                print(f"Rate limited by geocoding API for {city}, {country}")
                return None
            response.raise_for_status()
            data = response.json()
            if data:
                lat = data[0].get("lat")
                lon = data[0].get("lon")
                if lat and lon:
                    return Coordinates(latitude=float(lat), longitude=float(lon))
        except httpx.HTTPError as e:
            print(f"Failed to get lat/long for {city}, {country} from Nominatim: {e}", e)
        return None

    async def _call_open_meteo(self, city: str, country: str) -> list[float, float] | None:
        """Call the Open-Meteo API to get the latitude and longitude for a given city and country."""
        URL = "https://geocoding-api.open-meteo.com/v1/search"
        COUNT = 1
        try:
            
            params = {
                "name": city,
                "count": COUNT,
                "countryCode": country,
            }
            response = await self.client.get(URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            result = data.get("results", [])
            if not result or not isinstance(result, list) or not len(result) > 0:
                return None 
            first_result = result[0]
            if "latitude" in first_result and "longitude" in first_result:
                return Coordinates(
                    latitude=float(first_result["latitude"]),
                    longitude=float(first_result["longitude"])
                )

        except httpx.HTTPError as e:
            print(f"Failed to get lat/long for {city}, {country} from Open-Meteo: {e}", e)
        return None

    async def _check_db(self, city: str, country: str) -> Coordinates | None:
        """Check the database for an existing location record for the given city and country."""
        location = await Location.find_one({"city": city, "country": country})
        if location:
            return Coordinates(latitude=location.latitude, longitude=location.longitude)

    async def _save_to_db(self, city: str, country: str, latitude: float, longitude: float) -> Location:
        """Save a new location record to the database."""
        location = Location(city=city, country=country, latitude=latitude, longitude=longitude)
        await location.save()
        return 

    async def get_location(self, city: str, country: str) -> Coordinates | None:
        """Get the latitude and longitude for a given city and country, using caching to minimize API calls."""
        cache_key = self._cache_key(city, country)
        cached_location = self.cache.get(cache_key)
        if cached_location:
            #From cached string to list of floats
            latitude, longitude = map(float, cached_location.split(","))
            return Coordinates(latitude=latitude, longitude=longitude)

        location = await self._check_db(city, country)
        if location:
            latitude, longitude = location.latitude, location.longitude
            res = [latitude, longitude]
            self.cache.set(cache_key, res, expire_seconds=60 * 60 * 24)  # Cache for 24 hours
            return Coordinates(latitude=latitude, longitude=longitude)

        if len(country) > 0: #If country is provided prefer open-meteo 
            location = await self._call_open_meteo(city, country)
        else:
            location = await self._call_nota(city, country)

        if location:
            latitude, longitude = location.latitude, location.longitude
            cache_value = f"{latitude},{longitude}"
            self.cache.set(cache_key, cache_value, expire_seconds=60 * 60 * 24)  # Cache for 24 hours
            await self._save_to_db(city, country, latitude, longitude)
            return Coordinates(latitude=latitude, longitude=longitude)

        return None


import time
