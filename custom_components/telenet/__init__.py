"""Telenet integration."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone, tzinfo

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import TelenetClient
from .const import _LOGGER, COORDINATOR_UPDATE_INTERVAL, DOMAIN, PLATFORMS
from .exceptions import TelenetException, TelenetServiceException
from .models import TelenetProduct


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Telenet from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    username: str = entry.data[CONF_USERNAME]
    password: str = entry.data[CONF_PASSWORD]

    client = TelenetClient(
        username=username,
        password=password
    )

    dev_reg = dr.async_get(hass)
    hass.data[DOMAIN][entry.entry_id] = coordinator = TelenetDataUpdateCoordinator(
        hass,
        config_entry_id=entry.entry_id,
        dev_reg=dev_reg,
        client=client,
    )

    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class TelenetDataUpdateCoordinator(DataUpdateCoordinator):
    """Data update coordinator for Telenet"""

    data: list[TelenetProduct]
    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry_id: str,
        dev_reg: dr.DeviceRegistry,
        client: client,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=COORDINATOR_UPDATE_INTERVAL,
        )
        self._config_entry_id = config_entry_id
        self._device_registry = dev_reg
        self.client = client
        self.hass = hass

    async def _async_update_data(self) -> dict | None:
        """Update data."""
        try:
            user_details = await self.hass.async_add_executor_job(self.client.login)
            products = await self.hass.async_add_executor_job(self.client.products)
        except TelenetServiceException as exception:
            raise UpdateFailed(exception) from exception
        except TelenetException as exception:
            raise UpdateFailed(exception) from exception
        except Exception as exception:
            raise UpdateFailed(exception) from exception

        products: list[TelenetProduct] = products

        current_products = {
            list(device.identifiers)[0][1]
            for device in dr.async_entries_for_config_entry(
                self._device_registry, self._config_entry_id
            )
        }

        fetched_products = {str(product.product_identifier) for product in products}
        _LOGGER.debug(f"[init|TelenetDataUpdateCoordinator|_async_update_data|fetched_products] {fetched_products}")
        if stale_products := current_products - fetched_products:
            for product_identifier in stale_products:
                if device := self._device_registry.async_get_device(
                    {(DOMAIN, product_identifier)}
                ):
                    _LOGGER.debug(f"[init|TelenetDataUpdateCoordinator|_async_update_data|async_remove_device] {product_identifier}")
                    self._device_registry.async_remove_device(device.id)

        # If there are new products, we should reload the config entry so we can
        # create new devices and entities.
        if self.data and fetched_products - {
            str(product.product_identifier) for product in self.data
        }:
            #_LOGGER.debug(f"[init|TelenetDataUpdateCoordinator|_async_update_data|async_reload] {product.product_name}")
            self.hass.async_create_task(
                self.hass.config_entries.async_reload(self._config_entry_id)
            )
            return None
        return products
