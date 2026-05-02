import asyncio
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
            print(
                f"No {record_type} records found for {domain} using {dns_server.name}"
            )
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

        all_dns_servers = await self.repo.find_all(
            order_by="reputation", order_desc=True
        )
        results = []
        # build coroutine list (don't await here) and then gather
        actions = [
            self._query_records(domain, record_type, dns_server)
            for dns_server in all_dns_servers
        ]

        for dns_server, records in zip(all_dns_servers, await asyncio.gather(*actions)):
            results.append(
                SingleDnsLookupResponse(
                    dns_resolver_name=dns_server.name,
                    dns_resolver_ip=(
                        ", ".join(dns_server.ips) if dns_server.ips else "N/A"
                    ),
                    domain=domain,
                    record_type=record_type,
                    records=records,
                    location=(
                        dns_server.location.coordinates if dns_server.location else None
                    ),
                )
            )
        return results

    async def resolve_all_dns_records(
        self, domain: str, lat: float, long: float, radius: int
    ) -> list[SingleDnsLookupResponse]:
        """
        Resolve all DNS records for a given domain, without following CNAME chains.

        Args:
            domain (str): The domain to resolve.
            lat (float): Latitude for geolocation-based DNS server selection.
            long (float): Longitude for geolocation-based DNS server selection.
            radius (int): Radius in kilometers to search for nearby DNS servers.
        Returns:
            list[SingleDnsLookupResponse]: A list of DNS lookup responses containing the resolved records.
        """

        # first find nearby DNS servers based on lat/long/radius
        nearby_dns_servers = await self.repo.find_nearby(
            lat=lat, lon=long, radius_km=radius, order_by_reputation=True, limit=1
        )
        if not nearby_dns_servers:
            print("No nearby DNS servers found within the specified radius.")
            return []

        # For simplicity, we'll just use the first nearby DNS server found
        dns_server = nearby_dns_servers[0]

        # List types of DNS records to query
        record_types = ["A", "AAAA", "CNAME", "MX", "TXT", "NS"]
        results = []
        actions = [
            self._query_records(domain, record_type, dns_server)
            for record_type in record_types
        ]
        for record_type, records in zip(record_types, await asyncio.gather(*actions)):
            results.append(
                SingleDnsLookupResponse(
                    dns_resolver_name=dns_server.name,
                    dns_resolver_ip=(
                        ", ".join(dns_server.ips) if dns_server.ips else "N/A"
                    ),
                    domain=domain,
                    record_type=record_type,
                    records=records,
                    location=(
                        dns_server.location.coordinates if dns_server.location else None
                    ),
                )
            )
        return results
