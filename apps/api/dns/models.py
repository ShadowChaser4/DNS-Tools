"""Backwards-compatible re-exports for DNS models.

These import the canonical model classes from the shared `libs.models`
package so existing imports continue to work while other services consume
the shared package directly.
"""

from dns_models import DnsServerRecord, GeoPoint

__all__ = ["DnsServerRecord", "GeoPoint"]
