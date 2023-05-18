"""Telenet sensor platform."""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CURRENCY_EURO
from homeassistant.const import DATA_GIGABYTES
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import TelenetDataUpdateCoordinator
from .const import DOMAIN
from .entity import TelenetEntity
from .models import TelenetProduct
from .utils import format_entity_name

_LOGGER = logging.getLogger(__name__)


@dataclass
class TelenetSensorDescription(SensorEntityDescription):
    """Class to describe a Telenet sensor."""

    value_fn: Callable[[Any], StateType] | None = None


SENSOR_DESCRIPTIONS: list[SensorEntityDescription] = [
    TelenetSensorDescription(key="internet", icon="mdi:web"),
    TelenetSensorDescription(key="mobile", icon="mdi:cellphone"),
    TelenetSensorDescription(key="dtv", icon="mdi:television-box"),
    TelenetSensorDescription(key="telephone", icon="mdi:phone-classic"),
    TelenetSensorDescription(key="bundle", icon="mdi:database-cog"),
    TelenetSensorDescription(key="modem", icon="mdi:lan-connect"),
    TelenetSensorDescription(key="network", icon="mdi:lan"),
    TelenetSensorDescription(key="wifi", icon="mdi:wifi"),
    TelenetSensorDescription(key="qr", icon="mdi:qrcode-scan"),
    TelenetSensorDescription(key="user", icon="mdi:face-man"),
    TelenetSensorDescription(key="mailbox", icon="mdi:email"),
    TelenetSensorDescription(key="customer", icon="mdi:human-greeting-variant"),
    TelenetSensorDescription(
        key="euro",
        icon="mdi:currency-eur",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=CURRENCY_EURO,
    ),
    TelenetSensorDescription(
        key="data_usage",
        value_fn=lambda state: round(state, 2),
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=DATA_GIGABYTES,
        icon="mdi:summit",
    ),
    TelenetSensorDescription(
        key="usage_percentage",
        value_fn=lambda state: round(state, 1),
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:finance",
    ),
    TelenetSensorDescription(
        key="usage_percentage_mobile",
        value_fn=lambda state: round(state, 1),
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:signal-4g",
    ),
    TelenetSensorDescription(key="mobile_voice", icon="mdi:phone"),
    TelenetSensorDescription(key="mobile_data", icon="mdi:signal-4g"),
    TelenetSensorDescription(key="mobile_sms", icon="mdi:message-processing"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Telenet sensors."""
    _LOGGER.debug("[sensor|async_setup_entry|async_add_entities|start]")
    coordinator: TelenetDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[TelenetSensor] = []

    SUPPORTED_KEYS = {
        description.key: description for description in SENSOR_DESCRIPTIONS
    }

    # _LOGGER.debug(f"[sensor|async_setup_entry|async_add_entities|SUPPORTED_KEYS] {SUPPORTED_KEYS}")

    if coordinator.data is not None:
        for product in coordinator.data:
            if description := SUPPORTED_KEYS.get(product.product_description_key):
                if product.native_unit_of_measurement is not None:
                    native_unit_of_measurement = product.native_unit_of_measurement
                else:
                    native_unit_of_measurement = description.native_unit_of_measurement
                sensor_description = TelenetSensorDescription(
                    key=str(product.product_key),
                    name=product.product_name,
                    value_fn=description.value_fn,
                    native_unit_of_measurement=native_unit_of_measurement,
                    icon=description.icon,
                )

                _LOGGER.debug(
                    f"[sensor|async_setup_entry|adding] {product.product_identifier}"
                )
                entities.append(
                    TelenetSensor(
                        coordinator=coordinator,
                        description=sensor_description,
                        product=product,
                    )
                )
            else:
                _LOGGER.debug(
                    f"[sensor|async_setup_entry|no support type found] {product.product_identifier}, type: {product.product_description_key}, keys: {SUPPORTED_KEYS.get(product.product_description_key)}",
                    True,
                )

        async_add_entities(entities)


class TelenetSensor(TelenetEntity, SensorEntity):
    """Representation of a Telenet sensor."""

    entity_description: TelenetSensorDescription

    def __init__(
        self,
        coordinator: TelenetDataUpdateCoordinator,
        description: EntityDescription,
        product: TelenetProduct,
    ) -> None:
        """Set entity ID."""
        super().__init__(coordinator, description, product)
        self.entity_id = (
            f"sensor.{DOMAIN}_{format_entity_name(self.product.product_key)}"
        )

    @property
    def native_value(self) -> str:
        """Return the status of the sensor."""
        state = self.product.product_state

        if self.entity_description.value_fn:
            return self.entity_description.value_fn(state)

        return state

    @property
    def extra_state_attributes(self):
        """Return attributes for sensor."""
        if not self.coordinator.data:
            return {}
        attributes = {
            "last_synced": self.last_synced,
        }
        address = self.product.product_address
        if len(address) > 0:
            attributes |= {
                "address": f"{address.get('street')} {address.get('houseNumber')}, {address.get('postalCode')} {address.get('municipality')}, {address.get('country')}"
            }
        if len(self.product.product_extra_attributes) > 0:
            for attr in self.product.product_extra_attributes:
                attributes[attr] = self.product.product_extra_attributes[attr]
        return attributes
