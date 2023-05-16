"""Config flow to configure the Telenet integration."""
import logging
from abc import ABC
from abc import abstractmethod
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.config_entries import ConfigFlow
from homeassistant.config_entries import OptionsFlow
from homeassistant.const import CONF_LANGUAGE
from homeassistant.const import CONF_PASSWORD
from homeassistant.const import CONF_USERNAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowHandler
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import SelectSelector
from homeassistant.helpers.selector import SelectSelectorConfig
from homeassistant.helpers.selector import SelectSelectorMode
from homeassistant.helpers.selector import TextSelector
from homeassistant.helpers.selector import TextSelectorConfig
from homeassistant.helpers.selector import TextSelectorType
from homeassistant.helpers.typing import UNDEFINED

from .client import TelenetClient
from .const import DEFAULT_LANGUAGE
from .const import DOMAIN
from .const import LANGUAGE_CHOICES
from .const import NAME
from .exceptions import BadCredentialsException
from .exceptions import TelenetServiceException
from .models import TelenetConfigEntryData

_LOGGER = logging.getLogger(__name__)

DEFAULT_ENTRY_DATA = TelenetConfigEntryData(
    username=None,
    password=None,
    language=DEFAULT_LANGUAGE,
)

LANGUAGE_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=LANGUAGE_CHOICES,
        mode=SelectSelectorMode.DROPDOWN,
        translation_key=CONF_LANGUAGE,
    )
)


class TelenetCommonFlow(ABC, FlowHandler):
    """Base class for Telenet flows."""

    def __init__(self, initial_data: TelenetConfigEntryData) -> None:
        """Initialize TelenetCommonFlow."""
        self.initial_data = initial_data
        self.new_entry_data = TelenetConfigEntryData()
        self.new_title: str | None = None

    @abstractmethod
    def finish_flow(self) -> FlowResult:
        """Finish the flow."""

    def new_data(self):
        """Construct new data."""
        return DEFAULT_ENTRY_DATA | self.initial_data | self.new_entry_data

    async def async_validate_input(self, user_input: dict[str, Any]) -> None:
        """Validate user credentials."""

        client = TelenetClient(
            username=user_input[CONF_USERNAME],
            password=user_input[CONF_PASSWORD],
            language=user_input[CONF_LANGUAGE],
        )

        user_details = await self.hass.async_add_executor_job(client.login)

        return user_details

    async def async_step_connection_init(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Handle connection configuration."""
        errors: dict = {}

        if user_input is not None:
            user_input = self.new_data() | user_input
            test = await self.test_connection(user_input)
            if not test["errors"]:
                self.new_title = test["user_details"].get("username")
                self.new_entry_data |= user_input
                await self.async_set_unique_id(
                    f"{DOMAIN}_" + test["user_details"].get("customer_number")
                )
                self._abort_if_unique_id_configured()
                _LOGGER.debug(f"New account {self.new_title} added")
                return self.finish_flow()
            errors = test["errors"]
        fields = {
            vol.Required(CONF_USERNAME): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT, autocomplete="username")
            ),
            vol.Required(CONF_PASSWORD): TextSelector(
                TextSelectorConfig(
                    type=TextSelectorType.PASSWORD, autocomplete="current-password"
                )
            ),
            vol.Required(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): LANGUAGE_SELECTOR,
        }
        return self.async_show_form(
            step_id="connection_init",
            data_schema=vol.Schema(fields),
            errors=errors,
        )

    async def async_step_language(self, user_input: dict | None = None) -> FlowResult:
        """Configure language."""
        errors: dict = {}

        if user_input is not None:
            if user_input[CONF_LANGUAGE] not in LANGUAGE_CHOICES:
                errors["base"] = "language_not_found"
            if not errors:
                self.new_entry_data |= TelenetConfigEntryData(
                    language=user_input[CONF_LANGUAGE],
                )
                _LOGGER.debug(f"Language set to : {user_input[CONF_LANGUAGE]}")
                return self.finish_flow()

        fields = {
            vol.Required(CONF_LANGUAGE): LANGUAGE_SELECTOR,
        }
        return self.async_show_form(
            step_id="language",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(fields), {"language": self.initial_data.get(CONF_LANGUAGE)}
            ),
            errors=errors,
        )

    async def test_connection(self, user_input: dict | None = None) -> dict:
        """Test the connection to Telenet."""
        errors: dict = {}
        user_details: dict = {}

        if user_input is not None:
            user_input = self.new_data() | user_input
            try:
                user_details = await self.async_validate_input(user_input)
            except AssertionError as exception:
                errors["base"] = "cannot_connect"
                _LOGGER.debug(f"[async_step_password|login] AssertionError {exception}")
            except ConnectionError:
                errors["base"] = "cannot_connect"
            except TelenetServiceException:
                errors["base"] = "service_error"
            except BadCredentialsException:
                errors["base"] = "invalid_auth"
            except Exception as exception:
                errors["base"] = "unknown"
                _LOGGER.debug(exception)
        return {"user_details": user_details, "errors": errors}

    async def async_step_password(self, user_input: dict | None = None) -> FlowResult:
        """Configure password."""
        errors: dict = {}

        if user_input is not None:
            user_input = self.new_data() | user_input
            test = await self.test_connection(user_input)
            if not test["errors"]:
                self.new_entry_data |= TelenetConfigEntryData(
                    password=user_input[CONF_PASSWORD],
                )
                _LOGGER.debug(
                    f"Password changed for {test['user_details'].get('customer_number')}"
                )
                return self.finish_flow()

        fields = {
            vol.Required(CONF_PASSWORD): cv.string,
        }
        return self.async_show_form(
            step_id="password",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(fields),
                self.initial_data
                | TelenetConfigEntryData(
                    password=None,
                ),
            ),
            errors=errors,
        )


class TelenetOptionsFlow(TelenetCommonFlow, OptionsFlow):
    """Handle Telenet options."""

    general_settings: dict

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize Telenet options flow."""
        self.config_entry = config_entry
        super().__init__(initial_data=config_entry.data)  # type: ignore[arg-type]

    @callback
    def finish_flow(self) -> FlowResult:
        """Update the ConfigEntry and finish the flow."""
        new_data = DEFAULT_ENTRY_DATA | self.initial_data | self.new_entry_data
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            data=new_data,
            title=self.new_title or UNDEFINED,
        )
        self.hass.async_create_task(
            self.hass.config_entries.async_reload(self.config_entry.entry_id)
        )
        return self.async_create_entry(title="", data={})

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage Telenet options."""
        return self.async_show_menu(
            step_id="options_init",
            menu_options=[
                "language",
                "password",
            ],
        )


class TelenetConfigFlow(TelenetCommonFlow, ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Telenet."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize Telenet Config Flow."""
        super().__init__(initial_data=DEFAULT_ENTRY_DATA)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> TelenetOptionsFlow:
        """Get the options flow for this handler."""
        return TelenetOptionsFlow(config_entry)

    @callback
    def finish_flow(self) -> FlowResult:
        """Create the ConfigEntry."""
        title = self.new_title or NAME
        return self.async_create_entry(
            title=title,
            data=DEFAULT_ENTRY_DATA | self.new_entry_data,
        )

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle a flow initialized by the user."""
        return await self.async_step_connection_init()
