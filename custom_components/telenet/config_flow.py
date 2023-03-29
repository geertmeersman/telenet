"""Config flow to configure the Telenet integration."""
from typing import Any

from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_LANGUAGE, CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import _LOGGER, DOMAIN, NAME, DEFAULT_LANGUAGE, LANGUAGE_CHOICES

from .utils import *

class TelenetConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Telenet."""

    VERSION = 1

    async def _show_setup_form(self, errors=None, user_input=None):
        """Show the setup form to the user."""

        username = ""
        language=DEFAULT_LANGUAGE

        if user_input is not None:
            if CONF_USERNAME in user_input:
                username = user_input[CONF_USERNAME]
            if CONF_LANGUAGE in user_input:
                language = user_input[CONF_LANGUAGE]
    
        data_schema = {
            vol.Required(CONF_USERNAME, default=username): cv.string,
            vol.Required(CONF_PASSWORD): cv.string,
            vol.Required(CONF_LANGUAGE, default=language): vol.In( LANGUAGE_CHOICES )
        }
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema),
            errors=errors or {},
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Invoke when a user initiates a flow via the user interface."""

        if user_input is None:
            return await self._show_setup_form()

        errors: dict[str, str] = {}

        session = TelenetSession(user_input[CONF_USERNAME],user_input[CONF_PASSWORD])
        try:
            user_details = await self.hass.async_add_executor_job(session.login)
        except AssertionError as ex:
            errors["base"] = "cannot_connect"
            _LOGGER.error(f"[async_step_user|login] AssertionError {ex}")
            return await self._show_setup_form(errors, user_input)
        except Exception as ex:
            errors["base"] = "cannot_connect"
            return await self._show_setup_form(errors, user_input)

        await self.async_set_unique_id("telenet_"+user_details.get("customer_number"))
        self._abort_if_unique_id_configured()

        return self.async_create_entry(title=NAME, data=user_input)
