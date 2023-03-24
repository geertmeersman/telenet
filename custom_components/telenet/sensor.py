import asyncio
from datetime import date, datetime, time, timedelta, timezone, tzinfo
import itertools
import time as t

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    CURRENCY_EURO,
    DATA_GIGABYTES,
    PERCENTAGE,
    TIME_MINUTES,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
import voluptuous as vol

from .const import (
    _LOGGER,
    CONNECTION_RETRY,
    DATETIME_FORMAT,
    DOMAIN,
    NAME,
    UPDATE_INTERVAL,
    VERSION,
    WEBSITE,
)
from .utils import *

EUR_ICON = "mdi:currency-eur"
DATA_ICON = "mdi:web"
SMS_ICON = "mdi:message-processing"
VOICE_ICON = "mdi:phone"

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Setup sensor platform for the ui"""
    _LOGGER.info("[async_setup_entry] " + NAME)

    session = TelenetSession(entry.data.get("username"),entry.data.get("password"))
    language = entry.data.get("language")
    data = {
        "user_details": {},
        "plan_info": {},
        "internet_subscriptions": {},
        "mobile_subscriptions": {}
    }

    def data_update():
        """Fetch Telenet data."""
        try:
            #_LOGGER.debug(f"[async_setup_entry|update start]")
            data["user_details"] = session.login()
            data["plan_info"] = session.planInfo()
            data["last_sync"] = datetime.now()
            subscriptions = session.productSubscriptions("INTERNET")
            for subscription in subscriptions:
                identifier = subscription.get("identifier")
                billcycle = session.billCycles("internet",identifier, 1)
                start_date = billcycle.get('billCycles')[0].get("startDate")
                end_date = billcycle.get('billCycles')[0].get("endDate")
                data["internet_subscriptions"][identifier] = {
                    "identifier": identifier, 
                    "subscription_info": subscription, 
                    "usage": session.productUsage("internet",identifier,start_date,end_date), 
                    "start_date": start_date, 
                    "end_date": end_date, 
                    "product_details":session.telemeter_product_details(subscription.get("specurl")),
                    "product_daily_usage":session.productDailyUsage("internet",identifier,start_date,end_date)
                }
            subscriptions = session.productSubscriptions("MOBILE")
            for subscription in subscriptions:
                identifier = subscription.get("identifier")
                bundleusage = None
                if subscription.get('productType') == 'bundle':
                    usage = session.mobileBundleUsage(subscription.get('bundleIdentifier'),identifier)
                    bundleusage = session.mobileBundleUsage(subscription.get('bundleIdentifier'))
                else:
                    usage = session.mobileUsage(identifier)
                data["mobile_subscriptions"][identifier] =  {
                    "identifier": identifier, 
                    "subscription_info": subscription, 
                    "usage": usage, 
                    "bundleusage":bundleusage
                 }
            for plan in data["plan_info"]:
                if plan['productType'] == "bundle":
                    identifier = plan.get("identifier")
                    bundleusage = session.mobileBundleUsage(subscription.get('bundleIdentifier'))
                    data["mobile_subscriptions"][identifier] =  {
                        "identifier": identifier, 
                        "subscription_info": plan, 
                        "usage": None, 
                        "bundleusage":bundleusage
                     }
        except AssertionError:
            _LOGGER.error("[async_setup_entry|data_update] AssertionError, expecting another http return code")
            return False
        except Exception as ex:
            _LOGGER.error(f"[async_setup_entry|data_update] Failure {ex}")
            return False
        _LOGGER.debug(f"[async_setup_entry|data_update] New data fetched")

    async def async_data_update():
        """Schedule fetch Telenet data."""
        await hass.async_add_executor_job(data_update)

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=NAME,
        update_method=async_data_update,
        update_interval=UPDATE_INTERVAL,
    )

    for i in itertools.count():
        await hass.async_add_executor_job(lambda: data_update())
        if len(data["user_details"]) > 0:
            break
        if i > CONNECTION_RETRY:
            _LOGGER.error(f"[async_setup_entry|connect] Unable to connect to Telenet after trying {i} times, you will need to reload the integration")
            return False
        await asyncio.sleep(10)

    sensors = []
    infosensor_data = []

    for s_idx, subscription in enumerate(data["internet_subscriptions"]):
        sensor = InternetSensor(
            coordinator, 
            language,
            data,
            f"$.internet_subscriptions.{subscription}.identifier",
            "internet", 
            None, 
            None, 
            "", 
            None,
            [f"$.internet_subscriptions.{subscription}.subscription_info"],
            f"$.internet_subscriptions.{subscription}"
        )
        await sensor.update()
        sensors.append(sensor)
        infosensor_data.append([
            f"$.internet_subscriptions.{subscription}.identifier",
            "internet", 
            "daily usage", 
            "mdi:summit", 
            DATA_GIGABYTES, 
            f"$.internet_subscriptions.{subscription}.product_daily_usage.internetUsage[0].totalUsage.peak",
            [
                f"$.internet_subscriptions.{subscription}.product_daily_usage.internetUsage[0].totalUsage", 
                f"$.internet_subscriptions.{subscription}.product_daily_usage.internetUsage[0]"
            ],
            f"$.internet_subscriptions.{subscription}"
        ])
    for p_idx, plan in enumerate(data["plan_info"]):
        _LOGGER.debug(f"[Construct] Plan InfoSensor {plan['identifier']}")
        infosensor_data.append([
            f"$.plan_info[{p_idx}].identifier",
            "plan", 
            None, 
            "mdi:file-eye", 
            "", 
            f"$.plan_info[{p_idx}].label",
            [f"$.plan_info[{p_idx}]"],
        ])
    for s_idx, subscription in enumerate(data["mobile_subscriptions"]):
        info = data['mobile_subscriptions'][subscription]['subscription_info']
        bundleusage = data['mobile_subscriptions'][subscription]['bundleusage']
        usage = data['mobile_subscriptions'][subscription]['usage']
        if usage is None:
            type = "bundle"
            _LOGGER.debug(f"[Construct] MobileSensor Bundleusage {data['mobile_subscriptions'][subscription]['identifier']}")
            infosensor_data.append([
                f"$.mobile_subscriptions.{subscription}.identifier",
                type, 
                "Out of bundle", 
                EUR_ICON, 
                CURRENCY_EURO, 
                f"$.mobile_subscriptions.{subscription}.bundleusage.outOfBundle.usedUnits",
                [f"$.mobile_subscriptions.{subscription}.bundleusage.outOfBundle"],
            ])
            for idx, shared_data in enumerate(bundleusage.get("shared").get("data")):
                infosensor_data.append([
                    f"$.mobile_subscriptions.{subscription}.identifier",
                    type, 
                    shared_data.get("bucketType"), 
                    DATA_ICON, 
                    PERCENTAGE,
                    f"$.mobile_subscriptions.{subscription}.bundleusage.shared.data[{idx}].usedPercentage",
                    [f"$.mobile_subscriptions.{subscription}.bundleusage.shared.data[{idx}]"],
                ])
            for idx, shared_data in enumerate(bundleusage.get("shared").get("text")):
                infosensor_data.append([
                    f"$.mobile_subscriptions.{subscription}.identifier",
                    type, 
                    "sms", 
                    SMS_ICON, 
                    "",
                    f"$.mobile_subscriptions.{subscription}.bundleusage.shared.text[{idx}].usedUnits",
                    [f"$.mobile_subscriptions.{subscription}.bundleusage.shared.text[{idx}]"],
                ])
            for idx, shared_data in enumerate(bundleusage.get("shared").get("voice")):
                infosensor_data.append([
                    f"$.mobile_subscriptions.{subscription}.identifier",
                    type, 
                    "voice", 
                    VOICE_ICON, 
                    TIME_MINUTES,
                    f"$.mobile_subscriptions.{subscription}.bundleusage.shared.voice[{idx}].usedUnits",
                    [f"$.mobile_subscriptions.{subscription}.bundleusage.shared.voice[{idx}]"],
                ])
        else:
            if "isDataOnlyPlan" in info and info["isDataOnlyPlan"]:
                type = "mobile data"
            else:
                type = "mobile"

            infosensor_data.append([
                    f"$.mobile_subscriptions.{subscription}.identifier",
                    type, 
                    "Out of bundle", 
                    EUR_ICON, 
                    CURRENCY_EURO, 
                    f"$.mobile_subscriptions.{subscription}.usage.outOfBundle.usedUnits",
                    [f"$.mobile_subscriptions.{subscription}.usage.outOfBundle"]
                ])
            if bundleusage is None:
                infosensor_data += [
                    [
                        f"$.mobile_subscriptions.{subscription}.identifier",
                        type, 
                        "Data", 
                        DATA_ICON, 
                        f"$.mobile_subscriptions.{subscription}.usage.total.data.unitType",
                        f"$.mobile_subscriptions.{subscription}.usage.total.data.usedUnits",
                        [f"$.mobile_subscriptions.{subscription}.usage.total.data"],
                    ],
                    [
                        f"$.mobile_subscriptions.{subscription}.identifier",
                        type, 
                        "sms", 
                        SMS_ICON, 
                        "",
                        f"$.mobile_subscriptions.{subscription}.usage.total.text.usedUnits",
                        [f"$.mobile_subscriptions.{subscription}.usage.total.text"],
                    ],
                    [
                        f"$.mobile_subscriptions.{subscription}.identifier",
                        type, 
                        "voice", 
                        VOICE_ICON, 
                        f"$.mobile_subscriptions.{subscription}.usage.total.voice.unitType",
                        f"$.mobile_subscriptions.{subscription}.usage.total.voice.usedUnits",
                        [f"$.mobile_subscriptions.{subscription}.usage.total.voice"],
                    ],
                ]
            else:
                for idx,shared_data in enumerate(usage.get("shared").get("data")):
                    infosensor_data+= [
                            [
                                f"$.mobile_subscriptions.{subscription}.identifier",
                                type,
                                "Data National", 
                                DATA_ICON, 
                                f"$.mobile_subscriptions.{subscription}.usage.shared.data[{idx}].unitType",
                                f"$.mobile_subscriptions.{subscription}.usage.shared.data[{idx}].usedUnits",
                                [f"$.mobile_subscriptions.{subscription}.usage.shared.data[{idx}]"]
                            ],
                            [
                                f"$.mobile_subscriptions.{subscription}.identifier",
                                type,
                                "Data EU", 
                                DATA_ICON, 
                                f"$.mobile_subscriptions.{subscription}.usage.shared.data[{idx}].unitType",
                                f"$.mobile_subscriptions.{subscription}.usage.shared.data[{idx}].usedEuUnits",
                                [f"$.mobile_subscriptions.{subscription}.usage.shared.data[{idx}]"]
                            ],
                        ]
                for idx,shared_data in enumerate(usage.get("shared").get("text")):
                    infosensor_data.append([
                            f"$.mobile_subscriptions.{subscription}.identifier",
                                type,
                                "sms", 
                                SMS_ICON, 
                                "",
                                f"$.mobile_subscriptions.{subscription}.usage.shared.text[{idx}].usedUnits",
                                [f"$.mobile_subscriptions.{subscription}.usage.shared.text[{idx}]"]
                        ])
                for idx,shared_data in enumerate(usage.get("shared").get("voice")):
                    infosensor_data.append([
                            f"$.mobile_subscriptions.{subscription}.identifier",
                                type,
                                "voice", 
                                VOICE_ICON, 
                                TIME_MINUTES,
                                f"$.mobile_subscriptions.{subscription}.usage.shared.voice[{idx}].usedUnits",
                                [f"$.mobile_subscriptions.{subscription}.usage.shared.voice[{idx}]"]
                        ])
    for sd in infosensor_data:
        sensor = InfoSensor(coordinator,language,data,sd[0],sd[1],sd[2],sd[3],sd[4],sd[5],sd[6])
        await sensor.update()
        sensors.append(sensor)

    if len(sensors):
        async_add_entities(sensors)

class GlobalSensor(CoordinatorEntity, SensorEntity):
    """Representation of the Global Sensor."""
    def __init__(
        self, 
        coordinator: DataUpdateCoordinator,
        language,
        data,
        id_path,
        type,
        suffix = None,
        icon = None,
        unit_of_measurement = None,
        state_path = None,
        attributes_path = None,
        subscription_path = None
    ) -> None:
        """Initialize a Global sensor."""
        super().__init__(coordinator)
        self._language = language
        self._data = data
        self._type = type
        self._customer_number = get_json_dict_path(data, "$.user_details.customer_number")
        self._id = get_json_dict_path(data, id_path)
        self._suffix = suffix
        self._icon = icon
        self._unit_of_measurement = unit_of_measurement
        self._state_path = state_path
        self._attributes_path = attributes_path
        self._subscription_path = subscription_path

    async def update(self) -> None:
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        return

    @property
    def available(self):
        """Return True if entity is available."""
        return self.state is not None

    @property
    def state_class(self) -> SensorStateClass | str | None:
        """Return the class of this sensor."""
        return SensorStateClass.MEASUREMENT

    @property
    def name(self) -> str:
        return self.friendly_name

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, f"{NAME} {self._customer_number}")},
            "name": f"{NAME} {self._customer_number}",
            "sw_version": VERSION,
            "manufacturer": NAME,
            "configuration_url": WEBSITE
        }

    @property
    def unit(self) -> str:
        """Unit"""
        return str

    @property
    def type_id_suffix(self) -> str:
        if self._suffix is None:
            suffix = ""
        else:
            suffix = f" {self._suffix}"
        return (
            f"{self._type} {self._id}{suffix}"
        )

    @property
    def friendly_name(self) -> str:
        return (
            f"{NAME} {self.type_id_suffix}"
        )

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._data["label"]

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        attributes = {
            ATTR_ATTRIBUTION: NAME,
        }
        for v in self._data:
            attributes[v] = self._data[v]
        return attributes

    @property
    def unique_id(self) -> str:
        """Return the name of the sensor."""
        return (
            f"{NAME} {self._customer_number} {self.type_id_suffix}"
        )

    @property
    def icon(self) -> str:
        """Shows the correct icon this sensor."""
        if self._icon is None:
            return "mdi:information"
        return self._icon

class InternetSensor(GlobalSensor):
    @property
    def icon(self) -> str:
        """Shows the correct icon this sensor."""
        return DATA_ICON
    
    @property
    def subscription(self):
        if self._subscription_path is not None:
            return get_json_dict_path(self._data, self._subscription_path)
        return 

    @property
    def state(self):
        """Return the state of the sensor."""
        usage = self.subscription.get("usage").get("internet")
        return round(100*usage.get('totalUsage').get('units')/(usage.get('allocatedUsage').get('units')+usage.get('extendedUsage').get('volume')),2)

    @property
    def unit(self) -> int:
        """Unit"""
        return int

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement this sensor expresses itself in."""
        return PERCENTAGE

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        subscription = self.subscription
        usage = subscription.get("usage").get("internet")
        product = subscription.get("product_details").get("product")
        period_length = datetime.strptime(subscription.get("end_date"), DATETIME_FORMAT) - datetime.strptime(subscription.get("start_date"), DATETIME_FORMAT)
        period_length_days = period_length.days
        period_length_seconds = period_length.total_seconds()
        period_used = datetime.now() - datetime.strptime(subscription.get("start_date"), DATETIME_FORMAT)
        period_used_seconds = period_used.total_seconds()
        period_used_percentage = round(100*period_used_seconds/period_length_seconds,1)

        attributes = {
            ATTR_ATTRIBUTION:               NAME,
            "last_sync":                    self._data.get("last_sync"),
            "identifier":                   subscription.get("identifier"),
            "last_update":                  usage.get('totalUsage').get('lastUsageDate'),
            "start_date":                   subscription.get("start_date"),
            "end_date":                     subscription.get("end_date"),
            "days_until":                   usage.get('daysUntil'),
            "total_usage":                  f"{usage.get('totalUsage').get('units')} {usage.get('totalUsage').get('unitType')}",
            "wifree_usage":                 f"{usage.get('wifreeUsage').get('usedUnits')} {usage.get('wifreeUsage').get('unitType')}",
            "allocated_usage":              f"{usage.get('allocatedUsage').get('units')} {usage.get('allocatedUsage').get('unitType')}",
            "extended_usage":               f"{usage.get('extendedUsage').get('volume')} {usage.get('extendedUsage').get('unit')}",
            "extended_usage_price":         f"{usage.get('extendedUsage').get('price')} {usage.get('extendedUsage').get('currency')}",
            "peak_usage":                   usage.get('peakUsage').get('usedUnits'),
            "offpeak_usage":                round(get_json_dict_path(subscription, "$.product_daily_usage.internetUsage[0].totalUsage.offPeak"), 1),
            "total_usage_with_offpeak":     usage.get('peakUsage').get('usedUnits')+round(get_json_dict_path(subscription, "$.product_daily_usage.internetUsage[0].totalUsage.offPeak"), 1),
            "used_percentage":              self.state,
            "period_used_percentage":       period_used_percentage,
            "period_remaining_percentage":  (100-period_used_percentage),
            "squeezed":                     self.state>=100,
            "period_length":                period_length_days,
            "product_label":                f"{get_localized(self._language, product.get('localizedcontent')).get('name')}",
            "sales_price":                  f"{product.get('characteristics').get('salespricevatincl').get('value')} {product.get('characteristics').get('salespricevatincl').get('unit')}",
        }
        service = ""
        for services in product.get("services"):
            for specification in services.get("specifications"):
                if specification.get('labelkey') == "spec.fixedinternet.speed.download":
                    attributes["download_speed"] = f"{specification.get('value')} {specification.get('unit')}"
                elif specification.get('labelkey') == "spec.fixedinternet.speed.upload":
                    attributes["upload_speed"] = f"{specification.get('value')} {specification.get('unit')}"
                if specification.get('visible'):
                    service += f"{get_localized(self._language, specification.get('localizedcontent')).get('name')}"
                    if specification.get('value') is not None:
                        service += f" {specification.get('value')}"
                    if specification.get('unit') is not None:
                        service += f" {specification.get('unit')}"
                    service += "\n"
        if self.state >= 100:
            attributes["download_speed"] = "1 Mbps"
            attributes["upload_speed"]   = "256 Kbps"
        attributes["service"] = service
        return attributes

class InfoSensor(GlobalSensor):
    @property
    def icon(self) -> str:
        """Shows the correct icon this sensor."""
        return self._icon

    @property
    def unit(self) -> int:
        """Unit"""
        return int

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement this sensor expresses itself in."""
        if self._unit_of_measurement is None:
            return "string"
        if self._unit_of_measurement[0:2] == "$.":
            return get_json_dict_path(self._data, self._unit_of_measurement)
        return self._unit_of_measurement

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._state_path is not None:
            return get_json_dict_path(self._data, self._state_path)
        return "EMPTY"

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        attributes = {
            ATTR_ATTRIBUTION: NAME,
            "last_sync": self._data.get("last_sync")
        }
        if self._attributes_path is not None:
            for path in self._attributes_path:
                attrs = get_json_dict_path(self._data, path)
                for v in attrs:
                    attributes[v] = attrs[v]
        return attributes
