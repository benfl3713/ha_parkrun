"""Config flow for Parkrun integration."""
from __future__ import annotations

import logging
import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("user_id"): str,
        vol.Optional("name", default="Parkrun"): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    user_id = data["user_id"]
    
    # Validate that user_id is numeric
    if not user_id.isdigit():
        raise InvalidUserID
    
    # Basic validation - we could add more sophisticated checks here
    if len(user_id) < 4 or len(user_id) > 10:
        raise InvalidUserID
    
    # Return info that you want to store in the config entry.
    return {"title": f"Parkrun - {data['name']}", "user_id": user_id, "name": data["name"]}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Parkrun."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except InvalidUserID:
                errors["user_id"] = "invalid_user_id"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Check if this user_id is already configured
                await self.async_set_unique_id(user_input["user_id"])
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class InvalidUserID(HomeAssistantError):
    """Error to indicate that the user ID is invalid."""
