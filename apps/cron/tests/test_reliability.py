"""Unit tests for reliability scoring in ping_and_update_reliability."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from apps.cron.ping_and_update_reliability import (
    TRUSTED_DOMAINS,
    process_record,
    update_reliablity_score,
)


class TestUpdateReliablityScore:
    def test_success_increases_score(self, dns_server_factory):
        server = dns_server_factory(reliability=50.0)
        update_reliablity_score(server, no_of_fails=0, no_of_success=2)
        assert server.reliability == pytest.approx(70.0)

    def test_fails_decreases_score(self, dns_server_factory):
        server = dns_server_factory(reliability=50.0)
        update_reliablity_score(server, no_of_fails=1, no_of_success=0)
        assert server.reliability == pytest.approx(30.0)

    def test_mixed_success_and_fails(self, dns_server_factory):
        server = dns_server_factory(reliability=50.0)
        # +20 from 2 success, -20 from 1 fail
        update_reliablity_score(server, no_of_fails=1, no_of_success=2)
        assert server.reliability == pytest.approx(50.0)

    def test_clamps_at_100(self, dns_server_factory):
        server = dns_server_factory(reliability=95.0)
        update_reliablity_score(server, no_of_fails=0, no_of_success=5)
        assert server.reliability == 100

    def test_clamps_at_0(self, dns_server_factory):
        server = dns_server_factory(reliability=10.0)
        update_reliablity_score(server, no_of_fails=3, no_of_success=0)
        assert server.reliability == 0

    def test_no_change_when_zero_counts(self, dns_server_factory):
        server = dns_server_factory(reliability=42.0)
        update_reliablity_score(server, no_of_fails=0, no_of_success=0)
        assert server.reliability == pytest.approx(42.0)


class TestProcessRecord:
    @pytest.mark.asyncio
    async def test_updates_score_and_ips_from_mocks(self, dns_server_factory):
        server = dns_server_factory(
            reliability=50.0,
            ips=["8.8.8.8", "8.8.4.4", "1.2.3.4"],
        )

        ping_results = {"8.8.8.8": True, "8.8.4.4": True, "1.2.3.4": False}
        # 3 success, 2 fail across TRUSTED_DOMAINS (len 5)
        dns_results = [True, True, True, False, False]
        assert len(dns_results) == len(TRUSTED_DOMAINS)

        with (
            patch(
                "apps.cron.ping_and_update_reliability.ping_dns_ips",
                new_callable=AsyncMock,
                return_value=ping_results,
            ),
            patch(
                "apps.cron.ping_and_update_reliability.trusted_domain_resolved",
                new_callable=AsyncMock,
                side_effect=dns_results,
            ),
            patch(
                "apps.cron.ping_and_update_reliability.db_update_queue"
            ) as mock_queue,
        ):
            mock_queue.put = AsyncMock()
            await process_record(server)

        # +30 from 3 success, -40 from 2 fails -> 40
        assert server.reliability == pytest.approx(40.0)
        assert server.ips == ["8.8.8.8", "8.8.4.4"]
        assert server.active is True
        mock_queue.put.assert_awaited_once_with(server)

    @pytest.mark.asyncio
    async def test_marks_inactive_when_no_reachable_ips(self, dns_server_factory):
        server = dns_server_factory(reliability=80.0, ips=["1.2.3.4"])

        with (
            patch(
                "apps.cron.ping_and_update_reliability.ping_dns_ips",
                new_callable=AsyncMock,
                return_value={"1.2.3.4": False},
            ),
            patch(
                "apps.cron.ping_and_update_reliability.trusted_domain_resolved",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "apps.cron.ping_and_update_reliability.db_update_queue"
            ) as mock_queue,
        ):
            mock_queue.put = AsyncMock()
            await process_record(server)

        assert server.ips == []
        assert server.reliability == 0
        assert server.active is False
        mock_queue.put.assert_awaited_once_with(server)
