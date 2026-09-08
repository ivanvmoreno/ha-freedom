"""Config flow for Freedom.to integration."""
from __future__ import annotations

import copy
import logging
from typing import Any, Dict, List, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_DEFAULT_DURATION,
    CONF_SCAN_INTERVAL,
    CONF_TEMPLATES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SESSION_DURATION,
    DOMAIN,
)
from .coordinator import FreedomDataUpdateCoordinator
from .freedom_client import FreedomAuthError, FreedomClient

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def validate_input(hass: HomeAssistant, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the user credentials against Freedom.to."""
    session = async_get_clientsession(hass)
    client = FreedomClient(
        email=data[CONF_EMAIL],
        password=data[CONF_PASSWORD],
        session=session,
    )
    await client.login(force=True)
    profile = await client.get_profile()
    return {"title": profile.get("name") or data[CONF_EMAIL], "user_id": profile.get("id")}


class FreedomConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Freedom.to."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_EMAIL].lower())
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, user_input)
            except FreedomAuthError:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception in Freedom config flow")
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                    options={
                        CONF_TEMPLATES: [
                            {
                                "name": "Pomodoro 25m",
                                "duration": 25,
                                "block_everything": False,
                                "block_apps": False,
                            },
                            {
                                "name": "Deep Work 60m",
                                "duration": 60,
                                "block_everything": False,
                                "block_apps": False,
                            },
                        ],
                        CONF_DEFAULT_DURATION: DEFAULT_SESSION_DURATION,
                        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow handler for Freedom."""
        return FreedomOptionsFlowHandler(config_entry)


class FreedomOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Freedom.to (Templates, Durations, Polling)."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry
        self._options = dict(config_entry.options)
        self._templates: List[Dict[str, Any]] = list(
            self._options.get(CONF_TEMPLATES, [])
        )

    def _get_coordinator(self) -> Optional[FreedomDataUpdateCoordinator]:
        """Retrieve the live coordinator if available."""
        entry_data = self.hass.data.get(DOMAIN, {}).get(self._config_entry.entry_id)
        if entry_data:
            return entry_data.get("coordinator")
        return None

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage main options menu."""
        return self.async_show_menu(
            step_id="init",
            menu_options=[
                "general_settings",
                "add_template",
                "manage_templates",
            ],
        )

    async def async_step_general_settings(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage general integration settings."""
        if user_input is not None:
            self._options.update(user_input)
            return self.async_create_entry(title="", data=self._options)

        current_duration = self._options.get(
            CONF_DEFAULT_DURATION, DEFAULT_SESSION_DURATION
        )
        current_scan = self._options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        schema = vol.Schema(
            {
                vol.Required(CONF_DEFAULT_DURATION, default=current_duration): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=1440)
                ),
                vol.Required(CONF_SCAN_INTERVAL, default=current_scan): vol.All(
                    vol.Coerce(int), vol.Range(min=10, max=300)
                ),
            }
        )

        return self.async_show_form(step_id="general_settings", data_schema=schema)

    async def async_step_add_template(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Add a new focus session template."""
        coordinator = self._get_coordinator()
        device_options = {}
        filter_options = {}

        if coordinator and coordinator.data:
            for d in coordinator.data.devices:
                device_options[str(d["id"])] = f"{d.get('name')} ({d.get('os')})"
            for f in coordinator.data.filter_lists:
                filter_options[str(f["id"])] = f.get("name")

        if user_input is not None:
            new_tpl = {
                "name": user_input["name"].strip(),
                "duration": int(user_input["duration"]),
                "device_ids": [int(x) for x in user_input.get("device_ids", [])],
                "filter_list_ids": [int(x) for x in user_input.get("filter_list_ids", [])],
                "block_everything": bool(user_input.get("block_everything", False)),
                "block_apps": bool(user_input.get("block_apps", False)),
            }
            # Remove any existing template with same name
            self._templates = [t for t in self._templates if t.get("name") != new_tpl["name"]]
            self._templates.append(new_tpl)
            self._options[CONF_TEMPLATES] = self._templates
            return self.async_create_entry(title="", data=self._options)

        schema_dict: Dict[Any, Any] = {
            vol.Required("name", default="Deep Focus 45m"): str,
            vol.Required("duration", default=45): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=1440)
            ),
        }

        if device_options:
            schema_dict[vol.Optional("device_ids", default=list(device_options.keys()))] = (
                cv.multi_select(device_options)
            )
        if filter_options:
            schema_dict[vol.Optional("filter_list_ids", default=list(filter_options.keys()))] = (
                cv.multi_select(filter_options)
            )

        schema_dict[vol.Optional("block_everything", default=False)] = bool
        schema_dict[vol.Optional("block_apps", default=False)] = bool

        return self.async_show_form(
            step_id="add_template",
            data_schema=vol.Schema(schema_dict),
        )

    async def async_step_manage_templates(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """View or delete existing templates."""
        if not self._templates:
            return self.async_abort(reason="no_templates")

        template_options = {
            t["name"]: f"{t['name']} ({t['duration']} min)" for t in self._templates
        }

        if user_input is not None:
            to_delete = user_input.get("delete_templates", [])
            self._templates = [t for t in self._templates if t["name"] not in to_delete]
            self._options[CONF_TEMPLATES] = self._templates
            return self.async_create_entry(title="", data=self._options)

        schema = vol.Schema(
            {
                vol.Optional("delete_templates", default=[]): cv.multi_select(
                    template_options
                ),
            }
        )

        return self.async_show_form(step_id="manage_templates", data_schema=schema)
