"""Config flow to configure the Telenet integration."""
from typing import Any

from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_LANGUAGE, CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import _LOGGER, DOMAIN, NAME


class TelenetConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Telenet."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Invoke when a user initiates a flow via the user interface."""
        data_schema = {
            vol.Required(CONF_USERNAME): cv.string,
            vol.Required(CONF_PASSWORD): cv.string,
            vol.Required(CONF_LANGUAGE, default="nl"): vol.In( ["nl", "fr", "en"] )
        }
        errors: dict[str, str] = {}

        if user_input is not None:
            return self.async_create_entry(title=NAME, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema),
            errors=errors,
        )
