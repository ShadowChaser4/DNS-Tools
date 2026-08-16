"""Unit tests for apps.cron.helper.location.LocationHelper."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from apps.cron.helper.location import Coordinates, LocationHelper


@pytest.fixture
def mock_cache():
    cache = MagicMock()
    cache.get = MagicMock(return_value=None)
    cache.set = MagicMock(return_value=True)
    return cache


@pytest.fixture
def mock_client():
    client = AsyncMock(spec=httpx.AsyncClient)
    return client


@pytest.fixture
def location_helper(mock_cache, mock_client) -> LocationHelper:
    return LocationHelper(cache=mock_cache, client=mock_client)


class TestCacheKey:
    def test_cache_key_format(self, location_helper: LocationHelper):
        assert location_helper._cache_key("Paris", "FR") == "Paris_FR"
        assert location_helper._cache_key("", "US") == "_US"


class TestGetLocation:
    @pytest.mark.asyncio
    async def test_cache_hit_skips_network_and_db(
        self, location_helper: LocationHelper, mock_cache, mock_client
    ):
        mock_cache.get.return_value = "37.7749,-122.4194"
        location_helper._check_db = AsyncMock()
        location_helper._call_open_meteo = AsyncMock()
        location_helper._call_nota = AsyncMock()

        result = await location_helper.get_location("San Francisco", "US")

        assert result == Coordinates(latitude=37.7749, longitude=-122.4194)
        mock_cache.get.assert_called_once_with("San Francisco_US")
        location_helper._check_db.assert_not_awaited()
        location_helper._call_open_meteo.assert_not_awaited()
        location_helper._call_nota.assert_not_awaited()
        mock_client.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_db_hit_caches_and_skips_http(
        self, location_helper: LocationHelper, mock_cache, mock_client
    ):
        mock_cache.get.return_value = None
        location_helper._check_db = AsyncMock(
            return_value=Coordinates(latitude=48.8566, longitude=2.3522)
        )
        location_helper._call_open_meteo = AsyncMock()
        location_helper._call_nota = AsyncMock()

        result = await location_helper.get_location("Paris", "FR")

        assert result == Coordinates(latitude=48.8566, longitude=2.3522)
        mock_cache.set.assert_called_once()
        location_helper._call_open_meteo.assert_not_awaited()
        location_helper._call_nota.assert_not_awaited()
        mock_client.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_open_meteo_when_country_provided(
        self, location_helper: LocationHelper, mock_cache
    ):
        mock_cache.get.return_value = None
        location_helper._check_db = AsyncMock(return_value=None)
        location_helper._call_open_meteo = AsyncMock(
            return_value=Coordinates(latitude=40.7128, longitude=-74.006)
        )
        location_helper._call_nota = AsyncMock()
        location_helper._save_to_db = AsyncMock()

        result = await location_helper.get_location("New York", "US")

        assert result == Coordinates(latitude=40.7128, longitude=-74.006)
        location_helper._call_open_meteo.assert_awaited_once_with("New York", "US")
        location_helper._call_nota.assert_not_awaited()
        location_helper._save_to_db.assert_awaited_once()
        mock_cache.set.assert_called_once_with(
            "New York_US", "40.7128,-74.006", expire_seconds=60 * 60 * 24
        )

    @pytest.mark.asyncio
    async def test_nominatim_when_country_empty(
        self, location_helper: LocationHelper, mock_cache
    ):
        mock_cache.get.return_value = None
        location_helper._check_db = AsyncMock(return_value=None)
        location_helper._call_nota = AsyncMock(
            return_value=Coordinates(latitude=51.5074, longitude=-0.1278)
        )
        location_helper._call_open_meteo = AsyncMock()
        location_helper._save_to_db = AsyncMock()

        result = await location_helper.get_location("London", "")

        assert result == Coordinates(latitude=51.5074, longitude=-0.1278)
        location_helper._call_nota.assert_awaited_once_with("London", "")
        location_helper._call_open_meteo.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_none_when_all_sources_miss(
        self, location_helper: LocationHelper, mock_cache
    ):
        mock_cache.get.return_value = None
        location_helper._check_db = AsyncMock(return_value=None)
        location_helper._call_open_meteo = AsyncMock(return_value=None)

        result = await location_helper.get_location("Nowhere", "XX")

        assert result is None
        mock_cache.set.assert_not_called()
