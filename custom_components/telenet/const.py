"""Constants used by Telenet."""
import json
from datetime import timedelta
from pathlib import Path
from typing import Final

from homeassistant.const import Platform

from .models import TelenetEnvironment

PLATFORMS: Final = [Platform.SENSOR]
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"

ATTRIBUTION: Final = "Data provided by Telenet"

DEFAULT_TELENET_ENVIRONMENT = TelenetEnvironment(
    ocapi="https://api.prd.telenet.be/ocapi",
    ocapi_public="https://api.prd.telenet.be/ocapi/public",
    ocapi_public_api="https://api.prd.telenet.be/ocapi/public/api",
    ocapi_oauth="https://api.prd.telenet.be/ocapi/oauth",
    openid="https://login.prd.telenet.be/openid",
    referer="https://www2.telenet.be/residential/nl/mijn-telenet",
    x_alt_referer="https://www2.telenet.be/",
)

BASE_HEADERS = {
    "User-Agent": USER_AGENT,
    "Referer": DEFAULT_TELENET_ENVIRONMENT.referer,
    "x-alt-referer": DEFAULT_TELENET_ENVIRONMENT.x_alt_referer,
}

MEGA = 1048576
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
COORDINATOR_UPDATE_INTERVAL = timedelta(minutes=15)
CONNECTION_RETRY = 5
REQUEST_TIMEOUT = 10
DEFAULT_LANGUAGE = "nl"
LANGUAGE_CHOICES = ["nl", "fr", "en"]
WEBSITE = "https://mijn.telenet.be/mijntelenet/"

DEFAULT_ICON = "mdi:help-circle-outline"

manifestfile = Path(__file__).parent / "manifest.json"
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
