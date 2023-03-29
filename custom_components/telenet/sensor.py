"""Telenet sensor platform."""
from __future__ import annotations

from typing import TypedDict

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory, EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TelenetDataUpdateCoordinator
from .const import _LOGGER, DOMAIN, NETWORK_ICON, SENSOR_ICONS, VERSION
from .entity import TelenetEntity
from .models import TelenetProduct
from .utils import format_entity_name


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Telenet sensors."""
    _LOGGER.debug(f"[sensor|async_setup_entry|async_add_entities|start]")
    coordinator: TelenetDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        TelenetSensor(
            coordinator,
            idx,
            SensorEntityDescription(
                key=str(product.product_name),
                name=product.product_name,
                entity_category=EntityCategory.DIAGNOSTIC,
                device_class=f"{DOMAIN}__product_status",
            ),
            product=product,
        )
        for idx, product in enumerate(coordinator.data)
    )


class TelenetSensor(TelenetEntity, SensorEntity):
    """Representation of a Telenet sensor."""

    def __init__(
        self,
        coordinator: TelenetDataUpdateCoordinator,
        context: int,
        description: EntityDescription,
        product: TelenetProduct,
    ) -> None:
        """Set entity ID."""
        super().__init__(coordinator, context, description, product)
        self.entity_id = (
            f"sensor.{DOMAIN}_{format_entity_name(self.product.product_name)}"
        )

    @property
    def native_value(self) -> str:
        """Return the status of the monitor."""
        return self.product.product_state

    @property
    def icon(self) -> str:
        """Return the status of the monitor."""
        return SENSOR_ICONS.get(self.product.product_type)

    @property
    def extra_state_attributes(self):
        """Return attributes for sensor."""
        if not self.coordinator.data:
            return {}

        attributes = {
            "last_synced": self.last_synced,
        }
        return attributes
