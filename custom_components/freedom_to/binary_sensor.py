"""Binary sensor platform for Freedom.to."""
from __future__ import annotations

from typing import Any, Dict, Optional

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FreedomDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Freedom.to binary sensor based on a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: FreedomDataUpdateCoordinator = data["coordinator"]

    async_add_entities([FreedomActiveSessionBinarySensor(coordinator, entry)])


class FreedomActiveSessionBinarySensor(CoordinatorEntity[FreedomDataUpdateCoordinator], BinarySensorEntity):
    """Representation of an active Freedom session binary sensor."""

    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_has_entity_name = True
    _attr_name = "Active Session"

    def __init__(
        self,
        coordinator: FreedomDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._entry = entry
        user_id = coordinator.data.profile.get("id", "default")
        self._attr_unique_id = f"freedom_{user_id}_active_session"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, str(user_id))},
            "name": f"Freedom ({coordinator.data.profile.get('name', 'User')})",
            "manufacturer": "Freedom.to",
            "model": "Focus & Website Blocker",
        }

    @property
    def is_on(self) -> bool:
        """Return true if there is an active session."""
        return self.coordinator.data.active_session is not None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the extra state attributes of the session."""
        session = self.coordinator.data.active_session
        if not session:
            return {}

        return {
            "session_id": session.get("id"),
            "name": session.get("name"),
            "duration_minutes": (session.get("duration", 0) or 0) // 60,
            "seconds_till_end": session.get("time_left"),
            "start_time": session.get("active_session_started_at") or session.get("start_time"),
            "devices": session.get("device_ids", []),
            "filter_lists": session.get("filter_list_ids", []),
            "block_everything": session.get("block_everything", False),
            "block_apps": session.get("block_apps", False),
            "recurring": session.get("recurring", False),
        }
