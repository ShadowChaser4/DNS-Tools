from fastapi import APIRouter, Depends

from .schemas import DnsLookupResponse
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
) -> DnsLookupResponse:
    """
    Perform a DNS lookup for a given domain.
    """
    # Placeholder for DNS lookup logic
    records = await service.resolve_dns_record(domain, "A")
    return DnsLookupResponse(records=records)


__all__ = ["router"]
