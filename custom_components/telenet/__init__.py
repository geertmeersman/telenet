import logging
import json
from pathlib import Path
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from .utils import *
from homeassistant.const import (
    Platform,
    CONF_PASSWORD,
    CONF_USERNAME
)

PLATFORMS = [Platform.SENSOR]
_LOGGER = logging.getLogger(__name__)
DATETIME_FORMAT = '%Y-%m-%d'
UPDATE_INTERVAL = timedelta(minutes=15)
CONNECTION_RETRY = 2

manifestfile = Path(__file__).parent / 'manifest.json'
with open(manifestfile, 'r') as json_file:
    manifest_data = json.load(json_file)
    
DOMAIN = manifest_data.get("domain")
NAME = manifest_data.get("name")
VERSION = manifest_data.get("version")
ISSUEURL = manifest_data.get("issue_tracker")
WEBSITE = manifest_data.get("website")

STARTUP = """
-------------------------------------------------------------------
{name}
Version: {version}
This is a custom component
If you have any issues with this you need to open an issue here:
{issueurl}
-------------------------------------------------------------------
""".format(
    name=NAME, version=VERSION, issueurl=ISSUEURL
)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Telenet from a config entry."""
    _LOGGER.info(STARTUP)

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][entry.entry_id] = {}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        _LOGGER.debug(f"[async_unload_entry] hass.data[DOMAIN]: {hass.data[DOMAIN]}")
        del hass.data[DOMAIN][entry.entry_id]
    return unload_ok
