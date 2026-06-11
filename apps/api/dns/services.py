import asyncio
import dns.asyncresolver

from .models import DnsServerRecord
from .repository import DnsServerRepository
from .schemas import (
    DnsMultipleRecordsLookupResponse,
    DnsServer,
    SingleDnsLookupResponse,
)


class DnsResolverService:

    def __init__(self, repo: DnsServerRepository):
        self.repo = repo

    async def _get_cname_chain(
        self, domain: str, dns_server: DnsServerRecord
    ) -> tuple[str, list[str]]:
        """
        Recursively resolve CNAME records for a given domain until final domain is recieved.

        Args:
            domain (str): The domain to resolve.
            dns_server (DnsServerRecord): The DNS server to use for the query (For best scenario, we'll query with DNS server that has more than 99% reliability).
        Returns:
            tuple[str, list[str]]: A tuple containing the final resolved domain and a list of CNAMEs in the chain.
        """
        visited = set()
        answer_domain = domain
        while True:
            if answer_domain in visited:
                print(
                    f"Circular CNAME detected for {answer_domain} using {dns_server.name}"
                )
                break
            visited.add(answer_domain)

            resolver = dns.asyncresolver.Resolver()
            resolver.nameservers = dns_server.ips
            try:
                answers = await resolver.resolve(answer_domain, "CNAME")
                answer_domain = str(answers[0].target).rstrip(".")
            except dns.asyncresolver.NXDOMAIN:
                print(
                    f"No CNAME record found for {answer_domain} using {dns_server.name}"
                )
                break
            except Exception as e:
                print(f"Error occurred while resolving CNAME: {e}")
                break

        return answer_domain, list(visited)

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
        resolver.lifetime = 5.0
        try:
            answers = await resolver.resolve(domain, record_type)
            return [str(answer) for answer in answers]
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            print(
                f"No {record_type} records found for {domain} using {dns_server.name}"
            )
            return []
        except dns.resolver.LifetimeTimeout:
            print(f"DNS query timed out for {domain} using {dns_server.name}")
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

        all_dns_servers = await self.repo.aggregate_by_location(total=30)
        results = []
        # build coroutine list (don't await here) and then gather
        actions = [
            self._query_records(domain, record_type, dns_server)
            for dns_server in all_dns_servers
        ]

        for dns_server, records in zip(
            all_dns_servers, await asyncio.gather(*actions, return_exceptions=True)
        ):
            if isinstance(records, Exception):
                print(f"Error occurred while querying DNS records: {records}")
                continue
            results.append(
                SingleDnsLookupResponse(
                    domain=domain,
                    record_type=record_type,
                    records=records,
                    server=DnsServer(**dns_server.model_dump()) if dns_server else None,
                )
            )
        return results

    async def resolve_all_dns_records(
        self, domain: str, lat: float, long: float, radius: int
    ) -> DnsMultipleRecordsLookupResponse:
        """
        Resolve all DNS records for a given domain, without following CNAME chains.

        Args:
            domain (str): The domain to resolve.
            lat (float): Latitude for geolocation-based DNS server selection.
            long (float): Longitude for geolocation-based DNS server selection.
            radius (int): Radius in kilometers to search for nearby DNS servers.
        Returns:
            DnsMultipleRecordsLookupResponse: A response containing the resolved records and DNS server informations.
        """

        # first find nearby DNS servers based on lat/long/radius
        nearby_dns_servers = await self.repo.find_nearby(
            lat=lat, lon=long, radius_km=radius, order_by_reputation=True, limit=5
        )
        if not nearby_dns_servers:
            print("No nearby DNS servers found within the specified radius.")
            return []

        record_types = ["A", "AAAA", "CNAME", "MX", "TXT", "NS"]

        # Try each nearby server in order; use the first one that responds
        dns_server = None
        results = []
        for candidate in nearby_dns_servers:
            actions = [
                self._query_records(domain, record_type, candidate)
                for record_type in record_types
            ]
            candidate_results = await asyncio.gather(*actions)
            # Consider server usable if at least one record type returned data
            if any(candidate_results):
                dns_server = candidate
                results = list(candidate_results)
                print(f"Using DNS server: {candidate.name} ({candidate.ips})")
                break
            print(f"DNS server {candidate.name} unresponsive, trying next.")

        if not dns_server:
            # All candidates failed; return empty results with last candidate as server
            dns_server = nearby_dns_servers[-1]
            results = [[] for _ in record_types]

        return DnsMultipleRecordsLookupResponse(
            domain=domain,
            records=[
                SingleDnsLookupResponse(
                    domain=domain,
                    record_type=record_type,
                    records=records,
                    server=DnsServer(**dns_server.model_dump()),
                )
                for record_type, records in zip(record_types, results)
            ],
            server=DnsServer(**dns_server.model_dump()),
        )

    async def get_available_dns_servers(self) -> list[DnsServer]:
        """
        Retrieve a list of available DNS servers.

        Returns:
            list[DnsServer]: A list of DNS server objects.
        """
        dns_servers = await self.repo.aggregate_by_location(total=30)
        return [DnsServer(**dns_server.model_dump()) for dns_server in dns_servers]
