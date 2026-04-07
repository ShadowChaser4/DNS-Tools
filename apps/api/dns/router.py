from fastapi import APIRouter, FastAPI

from .schemas import DnsLookupResponse


app = FastAPI()
router = APIRouter(prefix="/dns", tags=["DNS"])


@router.get("/lookup/{domain}", response_model=DnsLookupResponse)
async def dns_lookup(
    domain: str,
) -> DnsLookupResponse:
    """
    Perform a DNS lookup for a given domain.
    """
    # Placeholder for DNS lookup logic
    return DnsLookupResponse(records=[])


__all__ = ["router"]
