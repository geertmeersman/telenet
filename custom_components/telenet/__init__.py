"""Telenet integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LANGUAGE, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from requests.exceptions import ConnectionError

from .client import TelenetClient
from .const import COORDINATOR_UPDATE_INTERVAL, DOMAIN, PLATFORMS
from .exceptions import TelenetException, TelenetServiceException
from .models import TelenetProduct

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Telenet from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    client = TelenetClient(
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        language=entry.data[CONF_LANGUAGE],
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
    """Data update coordinator for Telenet."""

    data: list[TelenetProduct]
    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry_id: str,
        dev_reg: dr.DeviceRegistry,
        client: TelenetClient,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=COORDINATOR_UPDATE_INTERVAL,
        )
        self._debug = _LOGGER.isEnabledFor(logging.DEBUG)
        self._config_entry_id = config_entry_id
        self._device_registry = dev_reg
        self.client = client
        self.hass = hass

    async def _async_update_data(self) -> dict | None:
        """Update data."""
        if self._debug:
            products = await self.hass.async_add_executor_job(
                self.client.products_refreshed
            )
        else:
            try:
                products = await self.hass.async_add_executor_job(
                    self.client.products_refreshed
                )
            except ConnectionError as exception:
                raise UpdateFailed(f"ConnectionError {exception}") from exception
            except TelenetServiceException as exception:
                raise UpdateFailed(
                    f"TelenetServiceException {exception}"
                ) from exception
            except TelenetException as exception:
                raise UpdateFailed(f"TelenetException {exception}") from exception
            except Exception as exception:
                raise UpdateFailed(f"Exception {exception}") from exception

        products: list[TelenetProduct] = products

        current_products = {
            list(device.identifiers)[0][1]
            for device in dr.async_entries_for_config_entry(
                self._device_registry, self._config_entry_id
            )
        }

        if type(products) is list and len(products) > 0:
            fetched_products = {
                str(product.product_plan_identifier) for product in products
            }
            _LOGGER.debug(
                f"[init|TelenetDataUpdateCoordinator|_async_update_data|fetched_products] {fetched_products}"
            )
            if stale_products := current_products - fetched_products:
                for product_identifier in stale_products:
                    if device := self._device_registry.async_get_device(
                        {(DOMAIN, product_identifier)}
                    ):
                        _LOGGER.debug(
                            f"[init|TelenetDataUpdateCoordinator|_async_update_data|async_remove_device] {product_identifier}",
                            True,
                        )
                        self._device_registry.async_remove_device(device.id)

            # If there are new products, we should reload the config entry so we can
            # create new devices and entities.
            if self.data and fetched_products - {
                str(product.product_plan_identifier) for product in self.data
            }:
                # _LOGGER.debug(f"[init|TelenetDataUpdateCoordinator|_async_update_data|async_reload] {product.product_name}")
                self.hass.async_create_task(
                    self.hass.config_entries.async_reload(self._config_entry_id)
                )
                return None
            return products
        return []
