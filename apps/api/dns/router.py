from typing import Annotated

from fastapi import APIRouter, Depends, Query

from .schemas import DnsLookupResponse, DnsLookupType
from .services import DnsResolverService

router = APIRouter(prefix="/dns", tags=["DNS"])


def get_dns_service() -> "DnsResolverService":
    from .repository import DnsServerRepository
    from .models import DnsServerRecord

    return DnsResolverService(DnsServerRepository(DnsServerRecord))


@router.get("/lookup/{domain}", response_model=DnsLookupResponse)
async def dns_lookup(
    domain: str,
    service: DnsResolverService = Depends(get_dns_service),
    type: DnsLookupType = DnsLookupType.A,
) -> DnsLookupResponse:
    """
    Perform a DNS lookup for a given domain against a specified record type and multiple DNS servers.
    """
    # Placeholder for DNS lookup logic
    records = await service.resolve_dns_record(domain, type.value)
    return DnsLookupResponse(records=records)


@router.get("/deep-lookup/{domain}", response_model=DnsLookupResponse)
async def deep_dns_lookup(
    domain: str,
    lat: float,
    lon: float,
    radius: Annotated[
        int,
        "Radius in kilometers to search for nearby DNS servers",
        Query(
            gt=0, lt=10000
        ),  # Validate that radius is greater than 0 and less than 10,000 km
    ],
    service: DnsResolverService = Depends(get_dns_service),
) -> DnsLookupResponse:
    """
    Perform a DNS lookup for a given domain against a single DNS server, resolving all record types and following CNAME chains as necessary.
    """
    # Placeholder for deep DNS lookup logic
    if radius <= 0:
        raise ValueError("Radius must be greater than 0")

    records = await service.resolve_all_dns_records(domain, lat, lon, radius)
    return DnsLookupResponse(records=records)


__all__ = ["router"]
