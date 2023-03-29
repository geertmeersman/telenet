"""Config flow to configure the Telenet integration."""
from typing import Any

from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_LANGUAGE, CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .client import TelenetClient
from .const import _LOGGER, DEFAULT_LANGUAGE, DOMAIN, LANGUAGE_CHOICES, NAME
from .exceptions import BadCredentialsException, TelenetServiceException
from .utils import *


class TelenetConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Telenet."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize Nest Protect Config Flow."""
        super().__init__()

        self._config_entry = None

    async def async_validate_input(self, user_input: dict[str, Any]) -> None:
        """Validate user credentials."""

        client = TelenetClient(
            username=user_input[CONF_USERNAME],
            password=user_input[CONF_PASSWORD]
        )

        user_details = await self.hass.async_add_executor_job(client.login)

        await self.async_set_unique_id(f"{DOMAIN}_"+user_details.get("customer_number"))
        self._abort_if_unique_id_configured()

        return user_details

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

        try:
            user_details = await self.async_validate_input(user_input)
        except AssertionError as exception:
            errors["base"] = "cannot_connect"
            _LOGGER.error(f"[async_step_user|login] AssertionError {exception}")
            return await self._show_setup_form(errors, user_input)
        except TelenetServiceException as exception:
            errors["base"] = "service_error"
            return await self._show_setup_form(errors, user_input)
        except BadCredentialsException:
            errors["base"] = "invalid_auth"
            return await self._show_setup_form(errors, user_input)
        except Exception as exception:
            errors["base"] = "unknown"
            _LOGGER.critical(exception)
        else:
            return self.async_create_entry(title=NAME, data=user_input)

        return await self._show_setup_form(errors, user_input)
