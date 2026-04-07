from fastapi import APIRouter, Depends

from ..core.db import get_db
from .schemas import DnsLookupResponse


router = APIRouter(prefix="/dns", tags=["DNS"])


def get_dns_service(db=Depends(get_db)):
    from .services import DnsResolverService

    return DnsResolverService(db)


@router.get("/lookup/{domain}", response_model=DnsLookupResponse)
async def dns_lookup(
    domain: str,
    service=Depends(get_dns_service),
) -> DnsLookupResponse:
    """
    Perform a DNS lookup for a given domain.
    """
    # Placeholder for DNS lookup logic
    return DnsLookupResponse(records=[])


__all__ = ["router"]
