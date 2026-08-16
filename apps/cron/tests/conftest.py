"""Shared fixtures for dns-cron unit tests."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from dns_models import DnsServerRecord, Location


@pytest.fixture(autouse=True)
def stub_beanie_collections():
    """Allow constructing Beanie Documents without a live Mongo connection."""
    originals = {}
    for model in (DnsServerRecord, Location):
        originals[model] = model._document_settings
        settings = MagicMock()
        settings.pymongo_collection = MagicMock()
        model._document_settings = settings
    yield
    for model, original in originals.items():
        model._document_settings = original


SAMPLE_CSV = """\
ip_address,name,as_number,as_org,country_code,city,version,error,dnssec,reliability,checked_at,created_at
8.8.8.8,dns.google.,15169,GOOGLE,US,Mountain View,,,true,1.00,2023-08-17 22:01:10,2023-04-26 22:18:09
8.8.4.4,dns.google.,15169,GOOGLE,US,Mountain View,,,true,0.95,2023-08-17 22:01:10,2023-04-26 22:18:09
1.1.1.1,one.one.one.one,13335,CLOUDFLARENET,US,San Francisco,,,true,0.99,2023-08-17 22:01:10,2023-04-26 22:18:09
"""

SAMPLE_CSV_ROW = {
    "ip_address": "8.8.8.8",
    "name": "dns.google.",
    "as_number": "15169",
    "as_org": "GOOGLE",
    "country_code": "US",
    "city": "Mountain View",
    "version": "",
    "error": "",
    "dnssec": "true",
    "reliability": "1.00",
    "checked_at": "2023-08-17 22:01:10",
    "created_at": "2023-04-26 22:18:09",
}


@pytest.fixture
def sample_csv() -> str:
    return SAMPLE_CSV


@pytest.fixture
def sample_csv_row() -> dict:
    return dict(SAMPLE_CSV_ROW)


@pytest.fixture
def sample_server_list() -> list[dict]:
    """Two CSV rows that share the same ASN+name identifier."""
    return [
        dict(SAMPLE_CSV_ROW),
        {
            **SAMPLE_CSV_ROW,
            "ip_address": "8.8.4.4",
            "reliability": "0.95",
        },
    ]


def make_dns_server_record(**overrides) -> DnsServerRecord:
    """Factory for in-memory DnsServerRecord instances (no Mongo required)."""
    defaults = {
        "organization": "GOOGLE",
        "name": "dns.google.",
        "ips": ["8.8.8.8", "8.8.4.4"],
        "country": "US",
        "city": "Mountain View",
        "dnssec": True,
        "reliability": 50.0,
        "as_number": 15169,
        "identifier": "15169_dns.google.",
        "active": True,
        "last_seen": datetime.now(timezone.utc),
    }
    defaults.update(overrides)
    return DnsServerRecord(**defaults)


@pytest.fixture
def dns_server_record() -> DnsServerRecord:
    return make_dns_server_record()


@pytest.fixture
def dns_server_factory():
    return make_dns_server_record
