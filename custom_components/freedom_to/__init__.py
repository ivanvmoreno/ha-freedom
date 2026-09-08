"""The Freedom.to integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    SERVICE_ADD_SESSION_NOTE,
    SERVICE_END_ALL_SESSIONS,
    SERVICE_END_SESSION,
    SERVICE_SET_LOCKED_MODE,
    SERVICE_START_SESSION,
)
from .coordinator import FreedomDataUpdateCoordinator
from .freedom_client import FreedomClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.BUTTON,
]

# Service Schemas
SERVICE_START_SESSION_SCHEMA = vol.Schema(
    {
        vol.Optional("duration", default=25): cv.positive_int,
        vol.Optional("filter_list_ids"): vol.All(cv.ensure_list, [cv.positive_int]),
        vol.Optional("filter_list_names"): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional("device_ids"): vol.All(cv.ensure_list, [cv.positive_int]),
        vol.Optional("device_names"): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional("block_everything", default=False): cv.boolean,
        vol.Optional("block_apps", default=False): cv.boolean,
    }
)

SERVICE_END_SESSION_SCHEMA = vol.Schema(
    {
        vol.Optional("schedule_id"): cv.positive_int,
    }
)

SERVICE_SET_LOCKED_MODE_SCHEMA = vol.Schema(
    {
        vol.Required("enabled"): cv.boolean,
    }
)

SERVICE_ADD_SESSION_NOTE_SCHEMA = vol.Schema(
    {
        vol.Required("note"): cv.string,
        vol.Optional("session_id"): cv.positive_int,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Freedom.to from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass)
    client = FreedomClient(
        email=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD],
        session=session,
    )

    coordinator = FreedomDataUpdateCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    async def async_handle_start_session(call: ServiceCall) -> None:
        """Handle starting a focus session."""
        duration = call.data.get("duration", 25)
        filter_list_ids = call.data.get("filter_list_ids")
        filter_list_names = call.data.get("filter_list_names")
        device_ids = call.data.get("device_ids")
        device_names = call.data.get("device_names")
        block_everything = call.data.get("block_everything", False)
        block_apps = call.data.get("block_apps", False)

        # Resolve filter_list_names if provided
        if filter_list_names and not filter_list_ids:
            filter_list_ids = []
            for fl in coordinator.data.filter_lists:
                if fl.get("name") in filter_list_names:
                    filter_list_ids.append(fl["id"])

        # Resolve device_names if provided
        if device_names and not device_ids:
            device_ids = []
            for dev in coordinator.data.devices:
                if dev.get("name") in device_names:
                    device_ids.append(dev["id"])

        await client.start_session(
            duration_minutes=duration,
            filter_list_ids=filter_list_ids,
            device_ids=device_ids,
            block_everything=block_everything,
            block_apps=block_apps,
        )
        await coordinator.async_request_refresh()

    async def async_handle_end_all_sessions(call: ServiceCall) -> None:
        """Handle ending all active sessions."""
        await client.end_all_sessions()
        await coordinator.async_request_refresh()

    async def async_handle_end_session(call: ServiceCall) -> None:
        """Handle ending a specific session."""
        schedule_id = call.data.get("schedule_id")
        if not schedule_id and coordinator.data.active_session:
            schedule_id = coordinator.data.active_session.get("id")

        if schedule_id:
            await client.end_session(schedule_id)
            await coordinator.async_request_refresh()
        else:
            _LOGGER.warning("No active session or schedule_id provided to end")

    async def async_handle_set_locked_mode(call: ServiceCall) -> None:
        """Handle setting locked mode."""
        enabled = call.data.get("enabled", False)
        await client.set_locked_mode(enabled)
        await coordinator.async_request_refresh()

    async def async_handle_add_session_note(call: ServiceCall) -> None:
        """Handle adding a note to a session."""
        note = call.data.get("note", "")
        session_id = call.data.get("session_id")
        if not session_id and coordinator.data.latest_concluded_session:
            session_id = coordinator.data.latest_concluded_session.get("id")

        if session_id:
            await client.save_session_note(session_id, note)
            await coordinator.async_request_refresh()
        else:
            _LOGGER.warning("No session_id or latest concluded session available to add note")

    hass.services.async_register(
        DOMAIN, SERVICE_START_SESSION, async_handle_start_session, schema=SERVICE_START_SESSION_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_END_ALL_SESSIONS, async_handle_end_all_sessions
    )
    hass.services.async_register(
        DOMAIN, SERVICE_END_SESSION, async_handle_end_session, schema=SERVICE_END_SESSION_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_LOCKED_MODE, async_handle_set_locked_mode, schema=SERVICE_SET_LOCKED_MODE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_ADD_SESSION_NOTE, async_handle_add_session_note, schema=SERVICE_ADD_SESSION_NOTE_SCHEMA
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        entry_data = hass.data[DOMAIN].pop(entry.entry_id, None)
        if entry_data:
            await entry_data["client"].close()
    return unload_ok
