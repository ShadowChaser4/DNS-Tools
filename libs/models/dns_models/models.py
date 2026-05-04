from typing import List, Literal, Optional

from beanie import Document
from pydantic import BaseModel, Field


class GeoPoint(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: List[float]  # [longitude, latitude]


class DnsServerRecord(Document):
    """Beanie Document representing a DNS server stored in MongoDB."""

    name: str = Field(..., description="DNS server display name")
    ips: List[str] = Field(
        default_factory=list, description="IP addresses for the server"
    )
    country: Optional[str] = Field(None, description="Country code (e.g. 'US')")
    city: Optional[str] = Field(None, description="City name")
    location: Optional[GeoPoint] = Field(
        None, description="Geographic location of the DNS server"
    )
    reputation: Optional[float] = Field(
        None, ge=0, le=100, description="Reputation 0-100"
    )
    reliability: Optional[float] = Field(
        None, ge=0, le=100, description="Reliability 0-100"
    )

    class Settings:
        name = "dns_server_records"  # MongoDB collection name
        indexes = [
            [("location", "2dsphere")],  # Geospatial index for location-based queries
            "name",  # Index on name for faster lookups
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "_id": "650f7f...",
                "name": "Cloudflare DNS",
                "ips": ["1.1.1.1", "1.0.0.1"],
                "country": "USA",
                "city": "San Francisco",
                "location": {"type": "Point", "coordinates": [-122.4194, 37.7749]},
                "reputation": 98.5,
                "reliability": 99.9,
            }
        }


__all__ = ["DnsServerRecord", "GeoPoint"]
