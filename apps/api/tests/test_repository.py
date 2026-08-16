"""Unit tests for DnsServerRepository helpers and mocked Beanie calls."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.dns.repository import DnsServerRepository
from dns_models import DnsServerRecord, GeoPoint


@pytest.fixture
def repo() -> DnsServerRepository:
    return DnsServerRepository(MagicMock())


async def test_equi_distant_geo_points_count(repo: DnsServerRepository):
    points = await repo._get_equi_distant_geo_points_over_globe(10)
    assert len(points) == 10
    assert all(isinstance(p, GeoPoint) for p in points)
    assert all(p.type == "Point" for p in points)


async def test_equi_distant_geo_points_coordinate_ranges(repo: DnsServerRepository):
    points = await repo._get_equi_distant_geo_points_over_globe(8)
    for point in points:
        lon, lat = point.coordinates
        assert -180 <= lon <= 180
        assert -90 <= lat <= 90


async def test_equi_distant_geo_points_poles_for_two(repo: DnsServerRepository):
    """With two points, Fibonacci sphere places them near the poles."""
    points = await repo._get_equi_distant_geo_points_over_globe(2)
    assert len(points) == 2
    _, first_lat = points[0].coordinates
    _, last_lat = points[1].coordinates
    assert first_lat == pytest.approx(90.0, abs=0.01)
    assert last_lat == pytest.approx(-90.0, abs=0.01)


async def test_equi_distant_geo_points_zero(repo: DnsServerRepository):
    points = await repo._get_equi_distant_geo_points_over_globe(0)
    assert points == []


async def test_equi_distant_geo_points_one_raises(repo: DnsServerRepository):
    with pytest.raises(ZeroDivisionError):
        await repo._get_equi_distant_geo_points_over_globe(1)


async def test_find_nearby_builds_geo_query(
    sample_dns_server: DnsServerRecord,
):
    mock_collection = MagicMock()
    mock_query = MagicMock()
    mock_query.to_list = AsyncMock(return_value=[sample_dns_server])
    mock_collection.find.return_value = mock_query

    repo = DnsServerRepository(mock_collection)
    results = await repo.find_nearby(
        lat=37.77, lon=-122.42, radius_km=50, order_by_reputation=True, limit=1
    )

    assert results == [sample_dns_server]
    mock_collection.find.assert_called_once()
    query_filter = mock_collection.find.call_args[0][0]
    assert query_filter["location"]["$near"]["$maxDistance"] == 50_000
    assert query_filter["location"]["$near"]["$geometry"]["coordinates"] == [
        -122.42,
        37.77,
    ]
    assert query_filter["dnssec"] is True
    assert query_filter["name"] == {"$regex": "^.{2,}$"}


async def test_find_nearby_returns_empty_on_error():
    mock_collection = MagicMock()
    mock_collection.find.side_effect = RuntimeError("mongo down")
    repo = DnsServerRepository(mock_collection)
    assert await repo.find_nearby(0.0, 0.0, 100) == []


async def test_find_all_applies_limit_and_sort():
    mock_collection = MagicMock()
    chain = MagicMock()
    chain.limit.return_value = chain
    chain.skip.return_value = chain
    chain.sort.return_value = chain
    chain.to_list = AsyncMock(return_value=[])
    mock_collection.find.return_value = chain

    repo = DnsServerRepository(mock_collection)
    await repo.find_all(limit=5, offset=2, order_by="reliability", order_desc=True)

    mock_collection.find.assert_called_once_with()
    chain.limit.assert_called_once_with(5)
    chain.skip.assert_called_once_with(2)
    chain.sort.assert_called_once_with(("reliability", -1))
