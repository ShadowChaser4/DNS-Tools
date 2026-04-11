from enum import Enum

from pydantic import BaseModel


class DnsLookupType(str, Enum):
    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"
    MX = "MX"
    NS = "NS"
    TXT = "TXT"


class SingleDnsLookupResponse(BaseModel):
    domain: str
    record_type: str
    records: list[str] | None
    dns_resolver_ip: str
    dns_resolver_name: str | None

    class Config:
        json_schema_extra = {
            "example": {
                "domain": "example.com",
                "record_type": "A",
                "records": ["1.1.1.1", "1.0.0.1"],
            }
        }


class DnsLookupResponse(BaseModel):
    records: list[SingleDnsLookupResponse]


__all__ = ["DnsLookupResponse"]
