"""DataUpdateCoordinator for Freedom.to integration."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any, Dict, List, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .freedom_client import FreedomApiError, FreedomAuthError, FreedomClient

_LOGGER = logging.getLogger(__name__)


class FreedomData:
    """Class to hold structured data fetched from Freedom.to."""

    def __init__(self) -> None:
        """Initialize data containers."""
        self.profile: Dict[str, Any] = {}
        self.devices: List[Dict[str, Any]] = []
        self.filter_lists: List[Dict[str, Any]] = []
        self.schedules: List[Dict[str, Any]] = []
        self.active_session: Optional[Dict[str, Any]] = None
        self.stats: Dict[str, Any] = {}
        self.latest_concluded_session: Optional[Dict[str, Any]] = None


class FreedomDataUpdateCoordinator(DataUpdateCoordinator[FreedomData]):
    """Class to manage fetching Freedom.to data from the API."""

    def __init__(self, hass: HomeAssistant, client: FreedomClient) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client
        self.data = FreedomData()

    async def _async_update_data(self) -> FreedomData:
        """Fetch data from Freedom endpoints."""
        try:
            profile = await self.client.get_profile()
            devices = await self.client.get_devices()
            filter_lists = await self.client.get_filter_lists()
            schedules = await self.client.get_schedules()
            stats = await self.client.get_concluded_stats()

            # Find if there is an active session
            active_session = None
            for sch in schedules:
                if sch.get("active") is True:
                    active_session = sch
                    break

            # Fetch latest concluded session
            latest_concluded = None
            try:
                concluded = await self.client.get_concluded_sessions(page=1)
                sessions_list = concluded.get("concluded_sessions", [])
                if sessions_list:
                    latest_concluded = sessions_list[0]
            except Exception as err:
                _LOGGER.debug("Could not fetch concluded sessions: %s", err)

            freedom_data = FreedomData()
            freedom_data.profile = profile
            freedom_data.devices = devices
            freedom_data.filter_lists = filter_lists
            freedom_data.schedules = schedules
            freedom_data.active_session = active_session
            freedom_data.stats = stats
            freedom_data.latest_concluded_session = latest_concluded

            return freedom_data

        except (FreedomAuthError, FreedomApiError) as err:
            raise UpdateFailed(f"Error communicating with Freedom.to: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error updating Freedom.to data: {err}") from err
