"""HTTP tests for DNS router with dependency overrides (no live Mongo/DNS)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.dns.router import get_dns_service
from apps.api.dns.schemas import (
    DnsLookupResponse,
    DnsMultipleRecordsLookupResponse,
    DnsServer,
    SingleDnsLookupResponse,
)
from dns_models import GeoPoint


@pytest.fixture
def mock_dns_service() -> MagicMock:
    return MagicMock()


@pytest.fixture
def client_with_service(client, app, mock_dns_service: MagicMock):
    app.dependency_overrides[get_dns_service] = lambda: mock_dns_service
    yield client
    app.dependency_overrides.pop(get_dns_service, None)


def _sample_server() -> DnsServer:
    return DnsServer(
        name="Cloudflare DNS",
        ips=["1.1.1.1"],
        location=GeoPoint(coordinates=[-122.4194, 37.7749]),
        reliability=99.9,
        city="San Francisco",
        country="US",
    )


def test_list_dns_servers(client_with_service, mock_dns_service: MagicMock):
    mock_dns_service.get_available_dns_servers = AsyncMock(
        return_value=[_sample_server()]
    )
    response = client_with_service.get("/dns/servers")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Cloudflare DNS"
    assert data[0]["ips"] == ["1.1.1.1"]


def test_dns_lookup(client_with_service, mock_dns_service: MagicMock):
    server = _sample_server()
    mock_dns_service.resolve_dns_record = AsyncMock(
        return_value=[
            SingleDnsLookupResponse(
                domain="example.com",
                record_type="A",
                records=["93.184.216.34"],
                server=server,
            )
        ]
    )
    response = client_with_service.get("/dns/lookup/example.com?type=A")
    assert response.status_code == 200
    body = DnsLookupResponse.model_validate(response.json())
    assert len(body.records) == 1
    assert body.records[0].records == ["93.184.216.34"]
    mock_dns_service.resolve_dns_record.assert_awaited_once_with("example.com", "A")


def test_dns_lookup_default_type(client_with_service, mock_dns_service: MagicMock):
    mock_dns_service.resolve_dns_record = AsyncMock(return_value=[])
    response = client_with_service.get("/dns/lookup/example.com")
    assert response.status_code == 200
    mock_dns_service.resolve_dns_record.assert_awaited_once_with("example.com", "A")


def test_dns_lookup_invalid_type(client_with_service, mock_dns_service: MagicMock):
    response = client_with_service.get("/dns/lookup/example.com?type=INVALID")
    assert response.status_code == 422
    mock_dns_service.resolve_dns_record.assert_not_called()


def test_lookup_by_location(client_with_service, mock_dns_service: MagicMock):
    server = _sample_server()
    mock_dns_service.resolve_all_dns_records = AsyncMock(
        return_value=DnsMultipleRecordsLookupResponse(
            domain="example.com",
            records=[
                SingleDnsLookupResponse(
                    domain="example.com",
                    record_type="A",
                    records=["93.184.216.34"],
                    server=server,
                )
            ],
            server=server,
        )
    )
    response = client_with_service.get(
        "/dns/lookup/by-location/example.com",
        params={"lat": 37.77, "lon": -122.42, "radius": 100},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["domain"] == "example.com"
    assert data["server"]["name"] == "Cloudflare DNS"
    mock_dns_service.resolve_all_dns_records.assert_awaited_once_with(
        "example.com", 37.77, -122.42, 100
    )


def test_lookup_by_location_missing_params(
    client_with_service, mock_dns_service: MagicMock
):
    response = client_with_service.get("/dns/lookup/by-location/example.com")
    assert response.status_code == 422
    mock_dns_service.resolve_all_dns_records.assert_not_called()


def test_lookup_by_location_radius_too_small(
    client_with_service, mock_dns_service: MagicMock
):
    response = client_with_service.get(
        "/dns/lookup/by-location/example.com",
        params={"lat": 0, "lon": 0, "radius": 0},
    )
    assert response.status_code == 422
    mock_dns_service.resolve_all_dns_records.assert_not_called()


def test_lookup_by_location_radius_too_large(
    client_with_service, mock_dns_service: MagicMock
):
    response = client_with_service.get(
        "/dns/lookup/by-location/example.com",
        params={"lat": 0, "lon": 0, "radius": 10000},
    )
    assert response.status_code == 422
    mock_dns_service.resolve_all_dns_records.assert_not_called()
