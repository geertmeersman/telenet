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
WEBSITE = "https://mijn.telenet.be/mijntelenet/"

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
