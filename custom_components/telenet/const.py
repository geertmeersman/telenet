"""Constants used by Telenet."""
from datetime import timedelta
import json
import logging
from pathlib import Path
from typing import Final

from homeassistant.const import Platform

from .models import TelenetEnvironment

PLATFORMS: Final = [Platform.SENSOR]
_LOGGER = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"

ATTRIBUTION: Final = "Data provided by Telenet"

DEFAULT_TELENET_ENVIRONMENT = TelenetEnvironment(
    ocapi="https://api.prd.telenet.be/ocapi",
    openid="https://login.prd.telenet.be/openid",
    referer="https://www2.telenet.be/residential/nl/mijn-telenet",
    x_alt_referer="https://www2.telenet.be/"
)

BASE_HEADERS = {
    "User-Agent": USER_AGENT,
    "Referer": DEFAULT_TELENET_ENVIRONMENT.referer,
    "x-alt-referer": DEFAULT_TELENET_ENVIRONMENT.x_alt_referer
}

DATETIME_FORMAT = '%Y-%m-%d'
COORDINATOR_UPDATE_INTERVAL = timedelta(minutes=15)
CONNECTION_RETRY = 2
REQUEST_TIMEOUT = 20
DEFAULT_LANGUAGE = "nl"
LANGUAGE_CHOICES = ["nl", "fr", "en"]
WEBSITE = "https://mijn.telenet.be/mijntelenet/"

SENSOR_ICONS = {
    "mobile": "mdi:cellphone",
    "internet": "mdi:web",
    "dtv": "mdi:television-box",
    "telephone": "mdi:phone-classic",
    "bundle": "mdi:database-cog"
}
EUR_ICON = "mdi:currency-eur"
DATA_ICON = "mdi:signal-4g"
WEB_ICON = "mdi:web"
SMS_ICON = "mdi:message-processing"
VOICE_ICON = "mdi:phone"
PEAK_ICON = "mdi:summit"
PLAN_ICON = "mdi:file-eye"
PHONE_ICON = "mdi:phone-classic"
TV_ICON = "mdi:television-box"
MODEM_ICON = "mdi:lan-connect"
NETWORK_ICON = "mdi:lan"
WIFI_ICON = "mdi:wifi"
SEARCH_OUTLINE = "mdi:text-box-search-outline"

manifestfile = Path(__file__).parent / 'manifest.json'
with open(manifestfile) as json_file:
    manifest_data = json.load(json_file)

DOMAIN = manifest_data.get("domain")
NAME = manifest_data.get("name")
VERSION = manifest_data.get("version")
ISSUEURL = manifest_data.get("issue_tracker")
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
