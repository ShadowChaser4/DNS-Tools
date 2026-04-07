from typing import List, Optional

from beanie import Document
from pydantic import Field


class DnsServer(Document):
    """Beanie Document representing a DNS server stored in MongoDB."""

    name: str = Field(..., description="DNS server display name")
    ips: List[str] = Field(
        default_factory=list, description="IP addresses for the server"
    )
    country: Optional[str] = Field(None, description="Country code or name")
    reputation: Optional[float] = Field(
        None, ge=0, le=100, description="Reputation 0-100"
    )
    reliability: Optional[float] = Field(
        None, ge=0, le=100, description="Reliability 0-100"
    )

    class Settings:
        name = "dns_servers"

    class Config:
        json_schema_extra = {
            "example": {
                "_id": "650f7f...",
                "name": "Cloudflare DNS",
                "ips": ["1.1.1.1", "1.0.0.1"],
                "country": "US",
                "reputation": 98.5,
                "reliability": 99.9,
            }
        }


__all__ = ["DnsServer"]
