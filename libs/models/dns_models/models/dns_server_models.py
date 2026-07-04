from datetime import datetime, timezone
from typing import List, Literal, Optional

from beanie import Document
from pydantic import BaseModel, Field


class GeoPoint(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: List[float]  # [longitude, latitude]


class DnsServerRecord(Document):
    """Beanie Document representing a DNS server stored in MongoDB."""

    organization: str = Field(
        ..., description="Organization that operates the DNS server"
    )
    name: str = Field(..., description="DNS server display name")
    ips: List[str] = Field(
        default_factory=list, description="IP addresses for the server"
    )
    country: Optional[str] = Field(None, description="Country code (e.g. 'US')")
    city: Optional[str] = Field(None, description="City name")
    location: Optional[GeoPoint] = Field(
        None, description="Geographic location of the DNS server"
    )
    dnssec: Optional[bool] = Field(
        None, description="Whether the DNS server supports DNSSEC"
    )
    reliability: Optional[float] = Field(
        None, ge=0, le=100, description="Reliability 0-100"
    )
    as_number: int = Field(..., description="Autonomous System Number (ASN)")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Record creation time",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Record last update time",
    )
    last_seen: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Time of last seen",
    )
    identifier: str = Field(..., description="Unique identifier for the DNS server")
    active: bool = Field(
        default=True, description="Whether the DNS server is currently active"
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
                "dnssec": True,
                "identifier": "cloudflare-dns",
                "as_number": 13335,
                "created_at": "2024-09-01T12:00:00Z",
                "updated_at": "2024-09-01T12:00:00Z",
                "last_seen": "2024-09-01T12:00:00Z",
                "organization": "Cloudflare, Inc.",
                "active": True,
            }
        }



__all__ = ["DnsServerRecord", "GeoPoint",]
