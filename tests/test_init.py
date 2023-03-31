"""Test component setup."""
from custom_components.telenet.const import DOMAIN
from homeassistant.setup import async_setup_component


async def test_async_setup(hass):
    """Test the component gets setup."""
    assert await async_setup_component(hass, DOMAIN, {}) is True
