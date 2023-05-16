"""Base Telenet entity."""
from __future__ import annotations

import logging
from datetime import datetime

import pytz
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TelenetDataUpdateCoordinator
from .const import ATTRIBUTION
from .const import DOMAIN
from .const import NAME
from .const import VERSION
from .const import WEBSITE
from .models import TelenetProduct
from .utils import format_entity_name

_LOGGER = logging.getLogger(__name__)


class TelenetEntity(CoordinatorEntity[TelenetDataUpdateCoordinator]):
    """Base Telenet entity."""

    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: TelenetDataUpdateCoordinator,
        description: EntityDescription,
        product: TelenetProduct,
    ) -> None:
        """Initialize Telenet entities."""
        super().__init__(coordinator)
        self.entity_description = description
        self._product = product
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(self.product.product_plan_identifier))},
            name=f"{self.product.product_plan_label} {self.product.product_plan_identifier}",
            manufacturer=NAME,
            configuration_url=WEBSITE,
            entry_type=DeviceEntryType.SERVICE,
            model=self.product.product_plan_label,
            sw_version=VERSION,
        )
        """
        extra attributes!
        """
        self._attr_unique_id = (
            f"{DOMAIN}_{format_entity_name(self.product.product_key)}"
        )
        self._product_key = self.product.product_key
        self.client = coordinator.client
        self.last_synced = datetime.now(pytz.timezone("UTC"))
        self._attr_name = f"{self.product.product_identifier}".capitalize()
        self._product = product
        _LOGGER.debug(f"[TelenetEntity|init] {self._product_key}")

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if len(self.coordinator.data):
            for product in self.coordinator.data:
                if self._product_key == product.product_key:
                    self.last_synced = datetime.now(pytz.timezone("UTC"))
                    self._product = product
                    self.async_write_ha_state()
                    return
        _LOGGER.debug(
            f"[TelenetEntity|_handle_coordinator_update] {self._attr_unique_id}: async_write_ha_state ignored since API fetch failed or not found",
            True,
        )

    @property
    def product(self) -> TelenetProduct:
        """Return the product for this entity."""
        return self._product

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._product is not None

    async def async_update(self) -> None:
        """Update the entity.  Only used by the generic entity update service."""
        return
