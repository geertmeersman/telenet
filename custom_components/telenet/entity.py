"""Base Telenet entity."""
from __future__ import annotations

from datetime import datetime

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
from .utils import log_debug


class TelenetEntity(CoordinatorEntity[TelenetDataUpdateCoordinator]):
    """Base Telenet entity."""

    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: TelenetDataUpdateCoordinator,
        context: int,
        description: EntityDescription,
        product: TelenetProduct,
    ) -> None:
        """Initialize Telenet entities."""
        super().__init__(coordinator, context=context)
        self.entity_description = description
        self._product = product
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(self.product.product_plan_identifier))},
            name=self.product.product_plan_identifier,
            manufacturer=NAME,
            configuration_url=WEBSITE,
            entry_type=DeviceEntryType.SERVICE,
            model=self.product.product_description,
            sw_version=VERSION,
        )
        """
        extra attributes!
        """
        self.context = (context,)
        self._attr_unique_id = f"{DOMAIN}_{format_entity_name(self.product.product_key)}"
        self.client = coordinator.client
        self.last_synced = datetime.now()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        log_debug(f"[TelenetEntity|_handle_coordinator_update] {self._attr_unique_id}")
        self.last_synced = datetime.now()
        # self._attr_is_on = self.coordinator.data[self.context]["state"]
        self.async_write_ha_state()

    @property
    def id_suffix(self) -> str:
        """Return id suffix."""
        if self.product.product_suffix is None:
            suffix = ""
        else:
            suffix = f"_{self.product.product_suffix}"
        return f"{self.product.product_identifier}{suffix}"

    @property
    def _products(self) -> list[TelenetProduct]:
        """Return all products."""
        return self.coordinator.data or []

    @property
    def product(self) -> TelenetProduct:
        """Return the product for this entity."""
        return next(
            (
                product
                for product in self._products
                if str(product.product_identifier) == self.entity_description.key
            ),
            self._product,
        )

    """
    @property
    def product_available(self) -> bool:
        return bool(
            self.product.product_state is not None
        )
    """
