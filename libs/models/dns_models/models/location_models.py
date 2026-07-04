from typing import Optional

from beanie import Document
from pydantic import  Field

class Location(Document):
    country: Optional[str] = Field(None, description="Country code (e.g. 'US')")
    city: Optional[str] = Field(None, description="City name")
    latitude: Optional[float] = Field(
        None, ge=-90, le=90, description="Latitude of the location"
    )
    longitude: Optional[float] = Field(
        None, ge=-180, le=180, description="Longitude of the location"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "country": "USA",
                "city": "San Francisco",
                "latitude": 37.7749,
                "longitude": -122.4194,
            }
        }


__all__ = ["Location"]