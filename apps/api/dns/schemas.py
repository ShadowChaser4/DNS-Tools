from enum import Enum
from typing import Optional
from pydantic import BaseModel

from .models import GeoPoint


class DnsLookupType(str, Enum):
    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"
    MX = "MX"
    NS = "NS"
    TXT = "TXT"


class DnsServer(BaseModel):
    name: str
    ips: list[str]
    location: GeoPoint
    reputation: float | None
    reliability: float | None
    city: Optional[str] = None
    country: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Cloudflare DNS",
                "ips": ["1.1.1.1", "1.0.0.1"],
                "location": {"type": "Point", "coordinates": [-122.4194, 37.7749]},
                "reputation": 98.5,
                "reliability": 99.9,
                "city": "San Francisco",
                "country": "USA",
            }
        }


class SingleDnsLookupResponse(BaseModel):
    domain: str
    record_type: str
    records: list[str] | None
    server: Optional[DnsServer] = None

    class Config:
        json_schema_extra = {
            "example": {
                "domain": "example.com",
                "record_type": "A",
                "records": ["1.1.1.1", "1.0.0.1"],
                "server": {
                    "name": "example.com",
                    "ips": ["1.1.1.1", "1.0.0.1"],
                    "location": {"type": "Point", "coordinates": [-122.0839, 37.3861]},
                    "reputation": 0.9,
                    "reliability": 0.8,
                },
            }
        }


class DnsLookupResponse(BaseModel):
    records: list[SingleDnsLookupResponse]


class DnsMultipleRecordsLookupResponse(BaseModel):
    domain: str
    records: list[SingleDnsLookupResponse]
    server: DnsServer


__all__ = [
    "DnsLookupResponse",
    "DnsServer",
    "SingleDnsLookupResponse",
    "DnsLookupType",
    "DnsMultipleRecordsLookupResponse",
]
