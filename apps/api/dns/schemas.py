from pydantic import BaseModel


class SingleDnsLookupResponse(BaseModel):
    domain: str
    record_type: str
    records: list[str] | None


class DnsLookupResponse(BaseModel):
    records: list[SingleDnsLookupResponse]


__all__ = ["DnsLookupResponse"]
