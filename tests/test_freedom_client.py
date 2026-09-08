"""Tests for FreedomClient."""
import pytest
from freedom_client import FreedomClient, FreedomAuthError

@pytest.mark.asyncio
async def test_live_freedom_client_lifecycle():
    client = FreedomClient("contacto@ivanmoreno.me", "ykh@TUG6tcz3fbj8xud")
    try:
        # 1. Login
        logged_in = await client.login()
        assert logged_in is True

        # 2. Get profile
        profile = await client.get_profile()
        assert profile.get("email") == "contacto@ivanmoreno.me"
        assert profile.get("name") == "Iván Moreno"
        assert "strong_mode" in profile

        # 3. Get devices
        devices = await client.get_devices()
        assert isinstance(devices, list)
        assert len(devices) > 0

        # 4. Get filter lists
        filters = await client.get_filter_lists()
        assert isinstance(filters, list)

        # 5. Get schedules
        schedules = await client.get_schedules()
        assert isinstance(schedules, list)

        # 6. Get stats
        stats = await client.get_concluded_stats()
        assert "duration" in stats

        # 7. Get concluded sessions
        history = await client.get_concluded_sessions(page=1)
        assert "concluded_sessions" in history
        assert "meta" in history

    finally:
        await client.close()


@pytest.mark.asyncio
async def test_invalid_login():
    client = FreedomClient("contacto@ivanmoreno.me", "wrong_password_test")
    try:
        with pytest.raises(FreedomAuthError):
            await client.login()
    finally:
        await client.close()
