"""Sensor platform for Freedom.to."""
from __future__ import annotations

from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
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
    """Set up Freedom.to sensors based on a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: FreedomDataUpdateCoordinator = data["coordinator"]

    async_add_entities(
        [
            FreedomSessionTimeRemainingSensor(coordinator, entry),
            FreedomActiveSessionNameSensor(coordinator, entry),
            FreedomConcludedSessionsCountSensor(coordinator, entry),
            FreedomFocusTimeLast7DaysSensor(coordinator, entry),
            FreedomLatestConcludedSessionSensor(coordinator, entry),
        ]
    )


class FreedomBaseSensor(CoordinatorEntity[FreedomDataUpdateCoordinator], SensorEntity):
    """Base class for Freedom sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: FreedomDataUpdateCoordinator,
        entry: ConfigEntry,
        key: str,
    ) -> None:
        """Initialize the base sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._key = key
        user_id = coordinator.data.profile.get("id", "default")
        self._attr_unique_id = f"freedom_{user_id}_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, str(user_id))},
            "name": f"Freedom ({coordinator.data.profile.get('name', 'User')})",
            "manufacturer": "Freedom.to",
            "model": "Focus & Website Blocker",
        }


class FreedomSessionTimeRemainingSensor(FreedomBaseSensor):
    """Sensor for remaining time in current active session."""

    _attr_name = "Session Time Remaining"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:timer-sand"

    def __init__(self, coordinator: FreedomDataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "session_time_remaining")

    @property
    def native_value(self) -> Optional[int]:
        """Return remaining time in minutes."""
        session = self.coordinator.data.active_session
        if not session:
            return 0
        time_left = session.get("time_left")
        if time_left is not None:
            return max(0, int(round(time_left / 60)))
        return 0


class FreedomActiveSessionNameSensor(FreedomBaseSensor):
    """Sensor for current active session name."""

    _attr_name = "Active Session Name"
    _attr_icon = "mdi:shield-check"

    def __init__(self, coordinator: FreedomDataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "active_session_name")

    @property
    def native_value(self) -> Optional[str]:
        """Return the name of the active session or None."""
        session = self.coordinator.data.active_session
        if session:
            return session.get("name") or "Focus Session"
        return "None"


class FreedomConcludedSessionsCountSensor(FreedomBaseSensor):
    """Sensor for total concluded sessions count."""

    _attr_name = "Concluded Sessions Count"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:counter"

    def __init__(self, coordinator: FreedomDataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "concluded_sessions_count")

    @property
    def native_value(self) -> int:
        """Return total concluded sessions count."""
        return self.coordinator.data.profile.get("concluded_sessions_count", 0)


class FreedomFocusTimeLast7DaysSensor(FreedomBaseSensor):
    """Sensor for total focus time accumulated in the last 7 days (in hours)."""

    _attr_name = "Focus Time Last 7 Days"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:chart-timeline-variant-shimmer"

    def __init__(self, coordinator: FreedomDataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "focus_time_last_7_days")

    @property
    def native_value(self) -> float:
        """Return focus hours in last 7 days."""
        duration_seconds = self.coordinator.data.stats.get("duration", 0)
        return round(duration_seconds / 3600.0, 1)


class FreedomLatestConcludedSessionSensor(FreedomBaseSensor):
    """Sensor displaying details of the latest concluded session."""

    _attr_name = "Latest Concluded Session"
    _attr_icon = "mdi:history"

    def __init__(self, coordinator: FreedomDataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "latest_concluded_session")

    @property
    def native_value(self) -> Optional[str]:
        """Return session name / timestamp."""
        session = self.coordinator.data.latest_concluded_session
        if not session:
            return "None"
        return session.get("name") or "Focus Session"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return details of the session."""
        session = self.coordinator.data.latest_concluded_session
        if not session:
            return {}
        return {
            "session_id": session.get("id"),
            "duration_minutes": (session.get("duration", 0) or 0) // 60,
            "start_at": session.get("start_at"),
            "end_at": session.get("end_at"),
            "note": session.get("note"),
            "type": session.get("type"),
        }
