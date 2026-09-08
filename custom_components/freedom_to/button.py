"""Button platform for Freedom.to."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FreedomDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Freedom.to buttons based on a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: FreedomDataUpdateCoordinator = data["coordinator"]

    async_add_entities([FreedomEndActiveSessionsButton(coordinator, entry)])


class FreedomEndActiveSessionsButton(CoordinatorEntity[FreedomDataUpdateCoordinator], ButtonEntity):
    """Button to quickly end all active sessions."""

    _attr_has_entity_name = True
    _attr_name = "End Active Sessions"
    _attr_icon = "mdi:stop-circle"

    def __init__(
        self,
        coordinator: FreedomDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the button entity."""
        super().__init__(coordinator)
        self._entry = entry
        user_id = coordinator.data.profile.get("id", "default")
        self._attr_unique_id = f"freedom_{user_id}_end_active_sessions"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, str(user_id))},
            "name": f"Freedom ({coordinator.data.profile.get('name', 'User')})",
            "manufacturer": "Freedom.to",
            "model": "Focus & Website Blocker",
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info("Ending all active Freedom sessions via button press")
        await self.coordinator.client.end_all_sessions()
        await self.coordinator.async_request_refresh()
