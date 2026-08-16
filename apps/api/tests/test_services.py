"""Unit tests for DnsResolverService with mocked DNS resolver (no network)."""

from unittest.mock import AsyncMock, MagicMock, patch

import dns.resolver
import pytest

from apps.api.dns.schemas import DnsMultipleRecordsLookupResponse, DnsServer
from apps.api.dns.services import DnsResolverService
from dns_models import DnsServerRecord


@pytest.fixture
def mock_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(mock_repo: MagicMock) -> DnsResolverService:
    return DnsResolverService(mock_repo)


def _mock_resolver(answers: list | Exception):
    resolver = MagicMock()
    if isinstance(answers, Exception):
        resolver.resolve = AsyncMock(side_effect=answers)
    else:
        resolver.resolve = AsyncMock(return_value=answers)
    return resolver


async def test_query_records_success(
    service: DnsResolverService, sample_dns_server: DnsServerRecord
):
    answers = [MagicMock(__str__=lambda self: "93.184.216.34")]
    with patch(
        "apps.api.dns.services.dns.asyncresolver.Resolver",
        return_value=_mock_resolver(answers),
    ):
        records = await service._query_records("example.com", "A", sample_dns_server)

    assert records == ["93.184.216.34"]


async def test_query_records_nxdomain(
    service: DnsResolverService, sample_dns_server: DnsServerRecord
):
    with patch(
        "apps.api.dns.services.dns.asyncresolver.Resolver",
        return_value=_mock_resolver(dns.resolver.NXDOMAIN()),
    ):
        records = await service._query_records("missing.example", "A", sample_dns_server)

    assert records == []


async def test_query_records_timeout(
    service: DnsResolverService, sample_dns_server: DnsServerRecord
):
    with patch(
        "apps.api.dns.services.dns.asyncresolver.Resolver",
        return_value=_mock_resolver(dns.resolver.LifetimeTimeout()),
    ):
        records = await service._query_records("example.com", "A", sample_dns_server)

    assert records == []


async def test_get_cname_chain_follows_links(
    service: DnsResolverService, sample_dns_server: DnsServerRecord
):
    import dns.asyncresolver as asyncresolver

    first = MagicMock()
    first.target = "cdn.example.com."
    second = MagicMock()
    second.target = "origin.example.com."

    resolver = MagicMock()
    resolver.resolve = AsyncMock(
        side_effect=[
            [first],
            [second],
            dns.resolver.NXDOMAIN(),
        ]
    )

    with (
        patch(
            "apps.api.dns.services.dns.asyncresolver.Resolver", return_value=resolver
        ),
        patch.object(asyncresolver, "NXDOMAIN", dns.resolver.NXDOMAIN),
    ):
        final, chain = await service._get_cname_chain(
            "www.example.com", sample_dns_server
        )

    assert final == "origin.example.com"
    assert "www.example.com" in chain
    assert "cdn.example.com" in chain
    assert "origin.example.com" in chain


async def test_get_cname_chain_detects_cycle(
    service: DnsResolverService, sample_dns_server: DnsServerRecord
):
    bounce = MagicMock()
    bounce.target = "www.example.com."

    resolver = MagicMock()
    resolver.resolve = AsyncMock(return_value=[bounce])

    with patch(
        "apps.api.dns.services.dns.asyncresolver.Resolver", return_value=resolver
    ):
        final, chain = await service._get_cname_chain(
            "www.example.com", sample_dns_server
        )

    assert final == "www.example.com"
    assert chain == ["www.example.com"]


async def test_resolve_dns_record(
    service: DnsResolverService,
    mock_repo: MagicMock,
    sample_dns_servers: list[DnsServerRecord],
):
    mock_repo.aggregate_by_location = AsyncMock(return_value=sample_dns_servers)

    async def fake_query(domain, record_type, dns_server):
        return [f"{dns_server.ips[0]}-result"]

    with patch.object(service, "_query_records", side_effect=fake_query):
        results = await service.resolve_dns_record("example.com", "A")

    assert len(results) == 2
    assert results[0].domain == "example.com"
    assert results[0].record_type == "A"
    assert results[0].records == ["1.1.1.1-result"]
    assert results[0].server is not None
    assert results[0].server.name == "Cloudflare DNS"
    mock_repo.aggregate_by_location.assert_awaited_once_with(total=30)


async def test_resolve_all_dns_records_uses_first_responsive_server(
    service: DnsResolverService,
    mock_repo: MagicMock,
    sample_dns_servers: list[DnsServerRecord],
):
    mock_repo.find_nearby = AsyncMock(return_value=sample_dns_servers)

    async def fake_query(domain, record_type, dns_server):
        if dns_server.name == "Cloudflare DNS" and record_type == "A":
            return ["93.184.216.34"]
        return []

    with patch.object(service, "_query_records", side_effect=fake_query):
        response = await service.resolve_all_dns_records(
            "example.com", 37.77, -122.42, 100
        )

    assert isinstance(response, DnsMultipleRecordsLookupResponse)
    assert response.domain == "example.com"
    assert response.server.name == "Cloudflare DNS"
    a_records = next(r for r in response.records if r.record_type == "A")
    assert a_records.records == ["93.184.216.34"]


async def test_resolve_all_dns_records_no_nearby(
    service: DnsResolverService, mock_repo: MagicMock
):
    mock_repo.find_nearby = AsyncMock(return_value=[])
    result = await service.resolve_all_dns_records("example.com", 0.0, 0.0, 50)
    assert result == []


async def test_get_available_dns_servers(
    service: DnsResolverService,
    mock_repo: MagicMock,
    sample_dns_servers: list[DnsServerRecord],
):
    mock_repo.aggregate_by_location = AsyncMock(return_value=sample_dns_servers)
    servers = await service.get_available_dns_servers()
    assert len(servers) == 2
    assert all(isinstance(s, DnsServer) for s in servers)
    assert servers[0].name == "Cloudflare DNS"
