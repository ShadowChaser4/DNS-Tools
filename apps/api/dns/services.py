import dns.asyncresolver

from .models import DnsServerRecord
from .repository import DnsServerRepository
from .schemas import SingleDnsLookupResponse


class DnsResolverService:

    def __init__(self, repo: DnsServerRepository):
        self.repo = repo

    async def _query_records(
        self, domain: str, record_type: str, dns_server: DnsServerRecord
    ) -> list[str]:
        """
        Query DNS records for a given domain and record type using the specified DNS server.

        Args:
            domain (str): The domain to query.
            record_type (str): The type of DNS record to query (e.g., A, AAAA, CNAME).
            dns_server (DnsServerRecord): The DNS server to use for the query.

        Returns:
            list[str]: A list of the resolved DNS records.
        """
        resolver = dns.asyncresolver.Resolver()
        resolver.nameservers = dns_server.ips
        try:
            answers = await resolver.resolve(domain, record_type)
            return [str(answer) for answer in answers]
        except dns.asyncresolver.NXDOMAIN:
            return []
        except Exception as e:
            print(f"Error occurred while querying DNS records: {e}")
            return []

    async def resolve_dns_record(
        self,
        domain: str,
        record_type: str,
    ) -> list[SingleDnsLookupResponse]:
        """
        Resolve DNS records for a given domain and record type.

        Args:
            domain (str): The domain to resolve.
            record_type (str): The type of DNS record to resolve (e.g., A, AAAA, CNAME).

        Returns:
            list[SingleDnsLookupResponse]: A list of DNS lookup responses containing the resolved records.
        """

        all_dns_servers = await self.repo.find_all()
