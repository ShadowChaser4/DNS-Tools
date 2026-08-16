"""Unit tests for apps.cron.dns_fetcher."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from apps.cron.dns_fetcher import (
    build_batches,
    get_dns_servers_csv,
    is_datetime,
    parse_csv_to_dicts,
    parse_to_db_model,
    safe_float,
)


class TestParseCsvToDicts:
    def test_parses_headers_and_rows(self, sample_csv: str):
        rows = parse_csv_to_dicts(sample_csv)
        assert len(rows) == 3
        assert rows[0]["ip_address"] == "8.8.8.8"
        assert rows[0]["name"] == "dns.google."
        assert rows[2]["ip_address"] == "1.1.1.1"

    def test_empty_body_returns_empty_list(self):
        csv_data = "ip_address,name\n"
        assert parse_csv_to_dicts(csv_data) == []


class TestSafeFloat:
    def test_valid_float(self):
        assert safe_float("1.00") == 1.0
        assert safe_float("0.95") == pytest.approx(0.95)

    def test_invalid_returns_none(self):
        assert safe_float("not-a-number") is None
        assert safe_float(None) is None  # type: ignore[arg-type]


class TestIsDatetime:
    def test_valid_format(self):
        assert is_datetime("2023-08-17 22:01:10") is True

    def test_invalid_formats(self):
        assert is_datetime("2023-08-17T22:01:10Z") is False
        assert is_datetime("") is False
        assert is_datetime("not-a-date") is False


class TestParseToDbModel:
    def test_builds_record_from_grouped_rows(self, sample_server_list: list[dict]):
        record = parse_to_db_model(sample_server_list, "15169_dns.google.")
        assert record is not None
        assert record.identifier == "15169_dns.google."
        assert record.name == "dns.google."
        assert record.organization == "GOOGLE"
        assert record.country == "US"
        assert record.city == "Mountain View"
        assert record.as_number == 15169
        assert record.dnssec is True
        assert set(record.ips) == {"8.8.8.8", "8.8.4.4"}
        # reliability "1.00" from first row -> * 100
        assert record.reliability == pytest.approx(100.0)
        assert isinstance(record.last_seen, datetime)

    def test_uses_checked_at_when_valid(self, sample_csv_row: dict):
        record = parse_to_db_model([sample_csv_row], "15169_dns.google.")
        assert record is not None
        # CSV string is accepted by is_datetime; Pydantic coerces to datetime
        assert record.last_seen == datetime(2023, 8, 17, 22, 1, 10)

    def test_falls_back_to_now_for_invalid_checked_at(self, sample_csv_row: dict):
        row = {**sample_csv_row, "checked_at": "2023-08-17T22:01:10Z"}
        before = datetime.now(timezone.utc)
        record = parse_to_db_model([row], "15169_dns.google.")
        after = datetime.now(timezone.utc)
        assert record is not None
        assert isinstance(record.last_seen, datetime)
        assert before <= record.last_seen <= after

    def test_dnssec_false(self, sample_csv_row: dict):
        row = {**sample_csv_row, "dnssec": "false"}
        record = parse_to_db_model([row], "id")
        assert record is not None
        assert record.dnssec is False

    def test_missing_reliability(self, sample_csv_row: dict):
        row = {**sample_csv_row, "reliability": ""}
        record = parse_to_db_model([row], "id")
        assert record is not None
        assert record.reliability is None

    def test_returns_none_on_empty_list(self):
        assert parse_to_db_model([], "id") is None


class TestBuildBatches:
    def test_even_batches(self):
        batches = list(build_batches(range(6), 2))
        assert batches == [[0, 1], [2, 3], [4, 5]]

    def test_remainder_batch(self):
        batches = list(build_batches([1, 2, 3, 4, 5], 2))
        assert batches == [[1, 2], [3, 4], [5]]

    def test_empty_iterable(self):
        assert list(build_batches([], 10)) == []

    def test_batch_larger_than_items(self):
        assert list(build_batches([1, 2], 10)) == [[1, 2]]


class TestGetDnsServersCsv:
    @pytest.mark.asyncio
    async def test_returns_response_text(self):
        mock_response = MagicMock()
        mock_response.text = "ip_address,name\n8.8.8.8,dns.google."
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("apps.cron.dns_fetcher.httpx.AsyncClient", return_value=mock_client):
            result = await get_dns_servers_csv()

        assert result == "ip_address,name\n8.8.8.8,dns.google."
        mock_client.get.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_runtime_error_on_http_error(self):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.ConnectError("connection failed")
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("apps.cron.dns_fetcher.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(RuntimeError, match="Could not fetch DNS servers"):
                await get_dns_servers_csv()
