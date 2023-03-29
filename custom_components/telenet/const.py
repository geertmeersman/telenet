from datetime import timedelta
import json
import logging
from pathlib import Path

from homeassistant.const import Platform

DOMAIN = "telenet_telemeter"
PLATFORMS = [Platform.SENSOR]
_LOGGER = logging.getLogger(__name__)
DATETIME_FORMAT = '%Y-%m-%d'
UPDATE_INTERVAL = timedelta(minutes=15)
CONNECTION_RETRY = 2
REQUEST_TIMEOUT = 20
DEFAULT_LANGUAGE = "nl"
LANGUAGE_CHOICES = ["nl", "fr", "en"]
WEBSITE = "https://mijn.telenet.be/mijntelenet/"

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
