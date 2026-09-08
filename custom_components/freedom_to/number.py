"""Number platform for Freedom.to (Ad-hoc session duration selector)."""
from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DEFAULT_DURATION, DEFAULT_SESSION_DURATION, DOMAIN
from .coordinator import FreedomDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Freedom.to number entities based on a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: FreedomDataUpdateCoordinator = data["coordinator"]

    async_add_entities([FreedomSessionDurationNumber(coordinator, entry)])


class FreedomSessionDurationNumber(CoordinatorEntity[FreedomDataUpdateCoordinator], NumberEntity):
    """Entity to select custom session duration right from dashboard."""

    _attr_has_entity_name = True
    _attr_name = "Session Duration"
    _attr_icon = "mdi:clock-fast"
    _attr_native_min_value = 5
    _attr_native_max_value = 240
    _attr_native_step = 5
    _attr_mode = NumberMode.SLIDER
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES

    def __init__(
        self,
        coordinator: FreedomDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the duration number entity."""
        super().__init__(coordinator)
        self._entry = entry
        user_id = coordinator.data.profile.get("id", "default")
        self._attr_unique_id = f"freedom_{user_id}_session_duration_selector"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, str(user_id))},
            "name": f"Freedom ({coordinator.data.profile.get('name', 'User')})",
            "manufacturer": "Freedom.to",
            "model": "Focus & Website Blocker",
        }

        # Initialize default value from options
        default_val = entry.options.get(CONF_DEFAULT_DURATION, DEFAULT_SESSION_DURATION)
        coordinator.data.selected_duration_minutes = default_val

    @property
    def native_value(self) -> float:
        """Return the current selected session duration."""
        return float(self.coordinator.data.selected_duration_minutes)

    async def async_set_native_value(self, value: float) -> None:
        """Set the session duration."""
        self.coordinator.data.selected_duration_minutes = int(value)
        self.async_write_ha_state()
