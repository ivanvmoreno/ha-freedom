"""Select platform for Freedom.to (Ad-hoc blocklist selector)."""
from __future__ import annotations

import logging
from typing import List, Optional

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FreedomDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

ALL_BLOCKLISTS = "All Blocklists"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Freedom.to select entities based on a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: FreedomDataUpdateCoordinator = data["coordinator"]

    async_add_entities([FreedomBlocklistSelect(coordinator, entry)])


class FreedomBlocklistSelect(CoordinatorEntity[FreedomDataUpdateCoordinator], SelectEntity):
    """Entity to select active blocklist for ad-hoc sessions."""

    _attr_has_entity_name = True
    _attr_name = "Session Blocklist"
    _attr_icon = "mdi:format-list-checks"

    def __init__(
        self,
        coordinator: FreedomDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the blocklist select entity."""
        super().__init__(coordinator)
        self._entry = entry
        user_id = coordinator.data.profile.get("id", "default")
        self._attr_unique_id = f"freedom_{user_id}_session_blocklist_selector"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, str(user_id))},
            "name": f"Freedom ({coordinator.data.profile.get('name', 'User')})",
            "manufacturer": "Freedom.to",
            "model": "Focus & Website Blocker",
        }
        self._current_option = ALL_BLOCKLISTS

    @property
    def options(self) -> List[str]:
        """Return list of available blocklist names."""
        opts = [ALL_BLOCKLISTS]
        for fl in self.coordinator.data.filter_lists:
            name = fl.get("name")
            if name and name not in opts:
                opts.append(name)
        return opts

    @property
    def current_option(self) -> str:
        """Return currently selected blocklist option."""
        if self._current_option in self.options:
            return self._current_option
        return ALL_BLOCKLISTS

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        self._current_option = option

        if option == ALL_BLOCKLISTS:
            self.coordinator.data.selected_blocklist_id = None
        else:
            for fl in self.coordinator.data.filter_lists:
                if fl.get("name") == option:
                    self.coordinator.data.selected_blocklist_id = fl.get("id")
                    break

        self.async_write_ha_state()
