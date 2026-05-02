from typing import List, Optional

from beanie import Document
from pydantic import Field


class DnsServerRecord(Document):
    """Beanie Document representing a DNS server stored in MongoDB."""

    name: str = Field(..., description="DNS server display name")
    ips: List[str] = Field(
        default_factory=list, description="IP addresses for the server"
    )
    country: Optional[str] = Field(None, description="Country code (e.g. 'US')")
    city: Optional[str] = Field(None, description="City name")
    lat: Optional[float] = Field(None, ge=-90, le=90, description="Latitude")
    lon: Optional[float] = Field(None, ge=-180, le=180, description="Longitude")
    reputation: Optional[float] = Field(
        None, ge=0, le=100, description="Reputation 0-100"
    )
    reliability: Optional[float] = Field(
        None, ge=0, le=100, description="Reliability 0-100"
    )

    class Settings:
        name = "dns_server_records"  # MongoDB collection name

    class Config:
        json_schema_extra = {
            "example": {
                "_id": "650f7f...",
                "name": "Cloudflare DNS",
                "ips": ["1.1.1.1", "1.0.0.1"],
                "country": "USA",
                "city": "San Francisco",
                "lat": 37.7749,
                "lon": -122.4194,
                "reputation": 98.5,
                "reliability": 99.9,
            }
        }


__all__ = ["DnsServerRecord"]
