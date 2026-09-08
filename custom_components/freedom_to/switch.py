"""Switch platform for Freedom.to (Locked Mode)."""
from __future__ import annotations

import logging
from typing import Any, Dict

from homeassistant.components.switch import SwitchEntity
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
    """Set up Freedom.to switches based on a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: FreedomDataUpdateCoordinator = data["coordinator"]

    async_add_entities([FreedomLockedModeSwitch(coordinator, entry)])


class FreedomLockedModeSwitch(CoordinatorEntity[FreedomDataUpdateCoordinator], SwitchEntity):
    """Switch to turn Locked Mode (strong_mode) on or off."""

    _attr_has_entity_name = True
    _attr_name = "Locked Mode"
    _attr_icon = "mdi:lock-alert"

    def __init__(
        self,
        coordinator: FreedomDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._entry = entry
        user_id = coordinator.data.profile.get("id", "default")
        self._attr_unique_id = f"freedom_{user_id}_locked_mode"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, str(user_id))},
            "name": f"Freedom ({coordinator.data.profile.get('name', 'User')})",
            "manufacturer": "Freedom.to",
            "model": "Focus & Website Blocker",
        }

    @property
    def is_on(self) -> bool:
        """Return true if locked mode is enabled."""
        return bool(self.coordinator.data.profile.get("strong_mode", False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on locked mode."""
        await self.coordinator.client.set_locked_mode(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off locked mode."""
        await self.coordinator.client.set_locked_mode(False)
        await self.coordinator.async_request_refresh()
