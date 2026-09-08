"""Button platform for Freedom.to."""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_TEMPLATES, DOMAIN
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

    buttons: List[ButtonEntity] = [
        FreedomEndActiveSessionsButton(coordinator, entry),
        FreedomStartCustomSessionButton(coordinator, entry),
    ]

    # Dynamically create buttons for configured session templates
    templates: List[Dict[str, Any]] = entry.options.get(CONF_TEMPLATES, [])
    for tpl in templates:
        buttons.append(FreedomTemplateSessionButton(coordinator, entry, tpl))

    async_add_entities(buttons)


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


class FreedomStartCustomSessionButton(CoordinatorEntity[FreedomDataUpdateCoordinator], ButtonEntity):
    """Button to start a custom session using current slider/dropdown settings."""

    _attr_has_entity_name = True
    _attr_name = "Start Focus Session"
    _attr_icon = "mdi:play-circle"

    def __init__(
        self,
        coordinator: FreedomDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the button entity."""
        super().__init__(coordinator)
        self._entry = entry
        user_id = coordinator.data.profile.get("id", "default")
        self._attr_unique_id = f"freedom_{user_id}_start_custom_session"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, str(user_id))},
            "name": f"Freedom ({coordinator.data.profile.get('name', 'User')})",
            "manufacturer": "Freedom.to",
            "model": "Focus & Website Blocker",
        }

    async def async_press(self) -> None:
        """Handle starting custom session."""
        duration = self.coordinator.data.selected_duration_minutes or 25
        blocklist_id = self.coordinator.data.selected_blocklist_id
        filter_ids = [blocklist_id] if blocklist_id else None

        _LOGGER.info("Starting custom Freedom session: %d min", duration)
        await self.coordinator.client.start_session(
            duration_minutes=duration,
            filter_list_ids=filter_ids,
        )
        await self.coordinator.async_request_refresh()


class FreedomTemplateSessionButton(CoordinatorEntity[FreedomDataUpdateCoordinator], ButtonEntity):
    """Button representing a pre-configured focus session template."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:lightning-bolt"

    def __init__(
        self,
        coordinator: FreedomDataUpdateCoordinator,
        entry: ConfigEntry,
        template: Dict[str, Any],
    ) -> None:
        """Initialize template button."""
        super().__init__(coordinator)
        self._entry = entry
        self._template = template
        user_id = coordinator.data.profile.get("id", "default")
        safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", template["name"].lower())
        self._attr_unique_id = f"freedom_{user_id}_template_{safe_name}"
        self._attr_name = f"Start: {template['name']}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, str(user_id))},
            "name": f"Freedom ({coordinator.data.profile.get('name', 'User')})",
            "manufacturer": "Freedom.to",
            "model": "Focus & Website Blocker",
        }

    async def async_press(self) -> None:
        """Trigger session using template config."""
        duration = self._template.get("duration", 25)
        filter_ids = self._template.get("filter_list_ids") or None
        device_ids = self._template.get("device_ids") or None
        block_everything = self._template.get("block_everything", False)
        block_apps = self._template.get("block_apps", False)

        _LOGGER.info("Triggering template session '%s' (%d min)", self._template["name"], duration)
        await self.coordinator.client.start_session(
            duration_minutes=duration,
            filter_list_ids=filter_ids,
            device_ids=device_ids,
            block_everything=block_everything,
            block_apps=block_apps,
        )
        await self.coordinator.async_request_refresh()
