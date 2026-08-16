"""Shared fixtures for dns-api unit tests (no live Mongo or DNS)."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from dns_models import DnsServerRecord, GeoPoint


@pytest.fixture
def sample_geo_point() -> GeoPoint:
    return GeoPoint(coordinates=[-122.4194, 37.7749])


@pytest.fixture
def sample_dns_server(sample_geo_point: GeoPoint) -> DnsServerRecord:
    # model_construct avoids Beanie CollectionWasNotInitialized (no live Mongo).
    return DnsServerRecord.model_construct(
        organization="Cloudflare, Inc.",
        name="Cloudflare DNS",
        ips=["1.1.1.1", "1.0.0.1"],
        country="US",
        city="San Francisco",
        location=sample_geo_point,
        dnssec=True,
        reliability=99.9,
        as_number=13335,
        identifier="cloudflare-dns",
        active=True,
    )


@pytest.fixture
def sample_dns_servers(sample_dns_server: DnsServerRecord) -> list[DnsServerRecord]:
    second = DnsServerRecord.model_construct(
        organization="Google",
        name="Google Public DNS",
        ips=["8.8.8.8", "8.8.4.4"],
        country="US",
        city="Mountain View",
        location=GeoPoint(coordinates=[-122.084, 37.422]),
        dnssec=True,
        reliability=98.5,
        as_number=15169,
        identifier="google-dns",
        active=True,
    )
    return [sample_dns_server, second]


@pytest.fixture
def mock_mongo_db() -> MagicMock:
    db = MagicMock()
    db.command = AsyncMock(return_value={"ok": 1})
    return db


@pytest.fixture
def app(mocker, mock_mongo_db: MagicMock):
    """FastAPI app with Mongo lifespan dependencies mocked."""
    mocker.patch(
        "apps.api.main.connect_to_mongo",
        new_callable=AsyncMock,
        return_value=mock_mongo_db,
    )
    mocker.patch("apps.api.main.initialize_odm", new_callable=AsyncMock)
    mocker.patch("apps.api.main.close_mongo", new_callable=AsyncMock)

    from apps.api.main import app as fastapi_app

    yield fastapi_app
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def client(app) -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
