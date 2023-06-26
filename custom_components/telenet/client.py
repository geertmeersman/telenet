"""Telenet API Client."""
from __future__ import annotations

from datetime import datetime
import logging

from requests import Session

from .const import (
    BASE_HEADERS,
    CONNECTION_RETRY,
    DATE_FORMAT,
    DATETIME_FORMAT,
    DEFAULT_LANGUAGE,
    DEFAULT_TELENET_ENVIRONMENT,
    REQUEST_TIMEOUT,
)
from .exceptions import BadCredentialsException, TelenetServiceException
from .models import (
    TelenetBundleProductExtraAttributes,
    TelenetDtvProductExtraAttributes,
    TelenetEnvironment,
    TelenetInternetProductExtraAttributes,
    TelenetMobileProductExtraAttributes,
    TelenetProduct,
    TelenetTelephoneProductExtraAttributes,
)
from .utils import (
    clean_ipv6,
    float_to_timestring,
    format_entity_name,
    get_json_dict_path,
    get_localized,
    str_to_float,
)

_LOGGER = logging.getLogger(__name__)


class TelenetClient:
    """Telenet client."""

    session: Session
    environment: TelenetEnvironment

    def __init__(
        self,
        session: Session | None = None,
        username: str | None = None,
        password: str | None = None,
        headers: dict | None = BASE_HEADERS,
        language: str | None = DEFAULT_LANGUAGE,
        environment: TelenetEnvironment = DEFAULT_TELENET_ENVIRONMENT,
    ) -> None:
        """Initialize TelenetClient."""
        self.session = session if session else Session()
        self.username = username
        self.password = password
        self.language = language
        self.environment = environment
        self.session.headers = headers
        self.all_products = {}
        self.product_types = []
        self.all_products_by_type = {}
        self.user_details = {}
        self.plan_products = {}
        self.addresses = {}
        self.request_error = {}
        self.total_cost = 0
        self._simdetails = []

    def request(
        self,
        url,
        caller="Not set",
        data=None,
        expected="200",
        log=False,
        retrying=False,
        connection_retry_left=CONNECTION_RETRY,
        return_false=True,
    ) -> dict:
        """Send a request to Telenet."""
        if data is None:
            _LOGGER.debug(f"{caller} Calling GET {url}")
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
        else:
            _LOGGER.debug(f"{caller} Calling POST {url}")
            response = self.session.post(url, data, timeout=REQUEST_TIMEOUT)
        _LOGGER.debug(
            f"{caller} http status code = {response.status_code} (expecting {expected})"
        )
        if log:
            _LOGGER.debug(f"{caller} Response:\n{response.text}")
        if expected is not None and response.status_code != expected:
            if response.status_code == 404:
                self.request_error = response.json()
                return False
            if (
                response.status_code != 403
                and response.status_code != 401
                and response.status_code != 500
                and connection_retry_left > 0
                and not retrying
            ):
                raise TelenetServiceException(
                    f"[{caller}] Expecting HTTP {expected} | Response HTTP {response.status_code}, Response: {response.text}, Url: {response.url}"
                )
            if response.status_code == 403:
                r = response.text
                if r.find("code") != -1:
                    if response.json().get("code") not in ["OCAPI-ERR-667"]:
                        _LOGGER.debug(
                            f"[{caller}] Telenet Service Access Forbidden for {self.username}: {response.status_code} => {response.json()}",
                        )
                        self.request_error = response.json()
                        return False
                    raise TelenetServiceException(
                        f"{response.json().get('cause')} for {self.username}"
                    )

            _LOGGER.debug(
                f"[TelenetClient|request] Received a HTTP {response.status_code}, nothing to worry about! We give it another try :-)"
            )
            self.login()
            response = self.request(
                url, caller, data, expected, log, True, connection_retry_left - 1
            )
        self.session.headers["X-TOKEN-XSRF"] = self.session.cookies.get("TOKEN-XSRF")
        if response.status_code > 404 and return_false is True:
            return False
        return response

    def login(self) -> dict:
        """Start a new Telenet session with a user & password."""

        _LOGGER.debug("[TelenetClient|login|start]")
        tokens = []
        token_fetch_count = 0
        while len(tokens) != 2:
            response = self.request(
                f"{self.environment.ocapi_oauth}/userdetails",
                "[TelenetClient|login]",
                None,
                None,
                return_false=False,
            )
            if response.status_code > 404:
                raise TelenetServiceException(
                    f"HTTP {response.status_code} {response.text}"
                )
            if response.status_code == 200:
                # Return if already authenticated
                return response.json()
            if response.status_code != 401 and response.status_code != 403:
                raise TelenetServiceException(
                    f"HTTP {response.status_code} error while authenticating {response.url}"
                )
            """Fetch state & nonce"""
            tokens = response.text.split(",", maxsplit=2)
            if token_fetch_count > CONNECTION_RETRY:
                raise TelenetServiceException(
                    f"HTTP 401 not returning the tokens for {response.url}"
                )
            token_fetch_count += 1
        state, nonce = response.text.split(",", maxsplit=2)
        """Login process"""
        response = self.request(
            f'{self.environment.openid}/oauth/authorize?client_id=ocapi&response_type=code&claims={{"id_token":{{"http://telenet.be/claims/roles":null,"http://telenet.be/claims/licenses":null}}}}&lang=nl&state={state}&nonce={nonce}&prompt=login',
            "[TelenetClient|login|authorize]",
            None,
            None,
        )
        if response.status_code != 200 or "openid/login" not in str(response.url):
            raise TelenetServiceException(response.text())
        response = self.request(
            f"{self.environment.openid}/login.do",
            "[TelenetClient|login|login.do]",
            {
                "j_username": self.username,
                "j_password": self.password,
                "rememberme": True,
            },
            200,
        )
        if "authentication_error" in response.url:
            raise BadCredentialsException(response.text)
        self.session.headers["X-TOKEN-XSRF"] = self.session.cookies.get("TOKEN-XSRF")
        response = self.request(
            f"{self.environment.ocapi_oauth}/userdetails",
            "[TelenetClient|login|user_details]",
            None,
            200,
        )
        user_details = response.json()
        if "customer_number" not in user_details:
            raise BadCredentialsException(
                f"HTTP {response.status_code} Missing customer number"
            )
        self.user_details = user_details
        del self.user_details["scopes"]
        return response.json()

    def add_product_type(self, product_type):
        """Add a discovered product type."""
        if product_type not in self.product_types:
            _LOGGER.debug(f"[TelenetClient|add_product_type] {product_type}")
            self.product_types.append(product_type)

    def add_product(
        self, product: dict, plan_identifier: str, state_prop: str, plan_label: str
    ) -> bool:
        """Add a discovered product."""
        identifier = product.get("identifier")
        if identifier in self.all_products:
            return False
        type = product.get("productType")
        _LOGGER.debug(
            f"[TelenetClient|add_product] {identifier}, productType: {type}, plan_label: {plan_label}"
        )
        product_price = None
        if product.get("specurl") is not None:
            product_info = self.product_details(product.get("specurl")).get("product")
            try:
                salespricevatincl = product_info.get("characteristics").get(
                    "salespricevatincl"
                )
                price = str_to_float(salespricevatincl.get("value"))
                if price > 0:
                    _LOGGER.debug(
                        f"[TelenetClient|add_product] Sales Price found for {identifier} {type}: {salespricevatincl}"
                    )
                    product_price = salespricevatincl
            except Exception:
                pass
        else:
            product_info = {}
        try:
            state = get_localized(
                self.language, product_info.get("localizedcontent")
            ).get("name")
        except Exception:
            state = product.get("label")

        product_extra_attributes = {}
        if type == "mobile":
            product_extra_attributes = self.get_simdetail(identifier)

        self.all_products[identifier] = TelenetProduct(
            product_identifier=identifier,
            product_type=type,
            product_description_key=type,
            product_plan_identifier=plan_identifier,
            product_plan_label=plan_label,
            product_name=identifier,
            product_key=format_entity_name(f"{identifier} {type} product"),
            product_state=state,
            product_specurl=product.get("specurl"),
            product_info=product_info,
            product_address=self.address(product.get("addressId")),
            product_price=product_price,
            product_extra_attributes=product_extra_attributes,
        )
        self.add_product_type(type)
        return True

    def products_refreshed(self):
        """Return Telenet products and force the refresh."""
        return self.products(force_refresh=True)

    def products(self, force_refresh=False) -> list:
        """List all Telenet products."""
        if len(self.all_products) > 0 and force_refresh is False:
            """Return the Telenet products present in the Client session"""
            _LOGGER.debug("[TelenetClient|products] Returning cached products")
            return [self.all_products.get(product) for product in self.all_products]
        self.login()
        self.total_cost = 0
        _LOGGER.debug("[TelenetClient|products] Fetching active products from Telenet")
        """ Refresh products """
        self.all_products = {}
        self.product_types = []
        response = self.request(
            f"{self.environment.ocapi_public_api}/product-service/v1/products?status=ACTIVE",
            "[TelenetClient|products]",
            None,
            200,
        )
        if response is False:
            api_v1_call = self.api_v1_call()
            if api_v1_call and len(api_v1_call.get("customerproductholding")):
                self.buildv1(api_v1_call)
                return [self.all_products.get(product) for product in self.all_products]
            else:
                raise TelenetServiceException(
                    "No products found. Either the API is currently down or you are not migrated to the new Telenet IT system yet."
                )
        for a_product in response.json():
            plan_identifier = a_product.get("identifier")
            plan_label = a_product.get("label")
            self.add_product(
                plan_identifier=plan_identifier,
                product=a_product,
                state_prop="label",
                plan_label=plan_label,
            )
            dtv_found = False
            _LOGGER.debug(
                f"[TelenetClient|products] Parent product {a_product.get('identifier')} {a_product.get('productType')}"
            )
            if a_product.get("children"):
                for product in a_product.get("children"):
                    _LOGGER.debug(
                        f"[TelenetClient|products] Child product {product.get('identifier')} {product.get('productType')}"
                    )
                    if product.get("productType") == "dtv":
                        dtv_found = True
                    if "options" in product and len(product.get("options")):
                        for option in product.get("options"):
                            if "identifier" in option:
                                self.add_product(
                                    product=option,
                                    plan_identifier=plan_identifier,
                                    state_prop="label",
                                    plan_label=plan_label,
                                )

                    self.add_product(
                        product=product,
                        plan_identifier=plan_identifier,
                        state_prop="label",
                        plan_label=plan_label,
                    )
            if dtv_found and a_product.get("productType") == "dtv":
                _LOGGER.debug("[TelenetClient|products] DTV child found & ignoring")
                self.all_products.get(
                    plan_identifier
                ).product_ignore_extra_sensor = True
        self.product_subscriptions()
        self.plan_info()
        self.create_extra_sensors()
        self.set_extra_attributes()
        return [self.all_products.get(product) for product in self.all_products]

    def construct_extra_sensor(
        self,
        product,
        suffix,
        product_description_key,
        product_state,
        product_extra_attributes={},
        use_plan_identifier=False,
        native_unit_of_measurement=None,
    ) -> list:
        """For each found product add extra product sensors."""
        type = product.product_type
        identifier = product.product_identifier
        plan_identifier = product.product_plan_identifier
        if use_plan_identifier:
            identifier = plan_identifier
        product_key = format_entity_name(f"{identifier} {type} {suffix}")
        return {
            product_key: TelenetProduct(
                product_identifier=f"{identifier} {suffix}",
                product_type=type,
                product_description_key=product_description_key,
                product_plan_identifier=plan_identifier,
                product_plan_label=product.product_plan_label,
                product_name=f"{identifier} {suffix}",
                product_key=product_key,
                product_state=product_state,
                product_extra_sensor=True,
                product_extra_attributes=product_extra_attributes,
                native_unit_of_measurement=native_unit_of_measurement,
            )
        }

    def create_extra_sensors(self) -> bool:
        """Create extra sensors."""
        new_products = {}
        for product in self.all_products:
            product = self.all_products[product]
            type = product.product_type
            identifier = product.product_identifier
            plan_identifier = product.product_plan_identifier
            product_specs = self.product_details(product.product_specurl).get("product")
            product_type_attr = {
                "product type": get_localized(
                    self.language, product_specs.get("localizedcontent")
                ).get("name")
            }
            _LOGGER.debug(f"[TelenetClient|create_extra_sensors] {identifier} {type}")
            if product.product_price is not None:
                product_without_specurl = product
                product_without_specurl.specurl = None
                self.total_cost += str_to_float(product.product_price.get("value"))
                new_products.update(
                    self.construct_extra_sensor(
                        product_without_specurl,
                        "price",
                        "euro",
                        str_to_float(product.product_price.get("value")),
                        product.product_price | product_type_attr,
                    )
                )

            if type == "internet":
                """------------------------"""
                """| EXTRA INTERNET SENSORS |"""
                """ ------------------------ """
                billcycle = self.bill_cycles(type, identifier, 2)
                product_usage = self.product_usage(
                    type,
                    identifier,
                    billcycle.get("start_date"),
                    billcycle.get("end_date"),
                )
                if product_usage is False:
                    _LOGGER.debug(
                        "[create_extra_sensors|internet|product_usage] Failed to fetch, skipping"
                    )
                    continue
                usage = product_usage.get(type)
                category = usage.get("category")
                daily_peak = []
                daily_off_peak = []
                daily_total = []
                daily_date = []
                product_daily_usage = {}

                for cycle in billcycle.get("cycles"):
                    daily_usage = self.product_daily_usage(
                        type,
                        identifier,
                        cycle.get("billCycle"),
                        cycle.get("startDate"),
                        cycle.get("endDate"),
                    )
                    if not daily_usage or len(daily_usage) == 0:
                        continue
                    product_daily_usage |= {cycle.get("billCycle"): daily_usage}
                    for day in (
                        product_daily_usage.get(cycle.get("billCycle"))
                        .get("internetUsage")[0]
                        .get("dailyUsages")
                    ):
                        if category == "CAP":
                            daily_total.append(day.get("bucketUsage"))
                        else:
                            daily_peak.append(day.get("peak"))
                            daily_off_peak.append(day.get("offPeak"))
                            daily_total.append(day.get("total"))
                        daily_date.append(day.get("date"))

                usage_pct = (
                    100
                    * usage.get("totalUsage").get("units")
                    / (
                        usage.get("allocatedUsage").get("units")
                        + usage.get("extendedUsage").get("volume")
                    )
                )
                period_length = datetime.strptime(
                    billcycle.get("end_date"), DATE_FORMAT
                ) - datetime.strptime(billcycle.get("start_date"), DATE_FORMAT)
                period_length_days = period_length.days
                period_length_seconds = period_length.total_seconds()
                period_used = datetime.now() - datetime.strptime(
                    billcycle.get("start_date"), DATE_FORMAT
                )
                period_used_seconds = period_used.total_seconds()
                period_used_percentage = round(
                    100 * period_used_seconds / period_length_seconds, 1
                )

                attributes = {
                    "identifier": identifier,
                    "last_update": f"{usage.get('totalUsage').get('lastUsageDate')}+0200",
                    "start_date": billcycle.get("start_date"),
                    "end_date": billcycle.get("end_date"),
                    "days_until": usage.get("daysUntil"),
                    "total_usage": f"{usage.get('totalUsage').get('units')} {usage.get('totalUsage').get('unitType')}",
                    "wifree_usage": f"{usage.get('wifreeUsage').get('usedUnits')} {usage.get('wifreeUsage').get('unitType')}",
                    "allocated_usage": f"{usage.get('allocatedUsage').get('units')} {usage.get('allocatedUsage').get('unitType')}",
                    "extended_usage": f"{usage.get('extendedUsage').get('volume')} {usage.get('extendedUsage').get('unit')}",
                    "extended_usage_price": f"{usage.get('extendedUsage').get('price')} {usage.get('extendedUsage').get('currency')}",
                    "peak_usage": usage.get("peakUsage").get("usedUnits"),
                    "used_percentage": round(usage_pct, 2),
                    "period_used_percentage": period_used_percentage,
                    "period_remaining_percentage": (100 - period_used_percentage),
                    "squeezed": usage_pct >= 100,
                    "period_length": period_length_days,
                    "product_label": get_localized(
                        self.language, product_specs.get("localizedcontent")
                    ).get("name"),
                    "sales_price": f"{product_specs.get('characteristics').get('salespricevatincl').get('value')} {product_specs.get('characteristics').get('salespricevatincl').get('unit')}",
                }

                product_daily_usage = product_daily_usage.get("CURRENT")
                if product_daily_usage is False:
                    _LOGGER.debug(
                        "[create_extra_sensors|internet|product_daily_usage] Failed to fetch, skipping"
                    )
                else:
                    attributes |= {
                        "offpeak_usage": round(
                            get_json_dict_path(
                                product_daily_usage,
                                "$.internetUsage[0].totalUsage.offPeak",
                            ),
                            1,
                        ),
                        "total_usage_with_offpeak": usage.get("peakUsage").get(
                            "usedUnits"
                        )
                        + round(
                            get_json_dict_path(
                                product_daily_usage,
                                "$.internetUsage[0].totalUsage.offPeak",
                            ),
                            1,
                        ),
                    }

                modem = self.modems(identifier)
                if modem is False:
                    _LOGGER.debug(
                        "[create_extra_sensors|internet|modem] Failed to fetch, skipping"
                    )

                service = ""
                for services in product_specs.get("services"):
                    for specification in services.get("specifications"):
                        if (
                            specification.get("labelkey")
                            == "spec.fixedinternet.speed.download"
                        ):
                            attributes[
                                "download_speed"
                            ] = f"{specification.get('value')} {specification.get('unit')}"
                        elif (
                            specification.get("labelkey")
                            == "spec.fixedinternet.speed.upload"
                        ):
                            attributes[
                                "upload_speed"
                            ] = f"{specification.get('value')} {specification.get('unit')}"
                        if specification.get("visible"):
                            service += f"{get_localized(self.language, specification.get('localizedcontent')).get('name')}"
                            if specification.get("value") is not None:
                                service += f" {specification.get('value')}"
                            if specification.get("unit") is not None:
                                service += f" {specification.get('unit')}"
                            service += "\n"
                if usage_pct >= 100:
                    attributes["download_speed"] = "1 Mbps"
                    attributes["upload_speed"] = "256 Kbps"
                attributes["service"] = service

                new_products.update(
                    self.construct_extra_sensor(
                        product,
                        "usage",
                        "usage_percentage",
                        usage_pct,
                        attributes,
                    )
                )
                if product_daily_usage is not False:
                    if category == "CAP":
                        new_products.update(
                            self.construct_extra_sensor(
                                product,
                                "daily usage",
                                "data_usage",
                                round(
                                    get_json_dict_path(
                                        product_daily_usage,
                                        "$.internetUsage[0].totalUsage.totalNonThrottle",
                                    ),
                                    1,
                                ),
                                self.create_extra_attributes_list(
                                    get_json_dict_path(
                                        product_daily_usage,
                                        "$.internetUsage[0].totalUsage",
                                    )
                                )
                                | {
                                    "daily_total": daily_total,
                                    "daily_date": daily_date,
                                },
                            )
                        )
                    else:
                        new_products.update(
                            self.construct_extra_sensor(
                                product,
                                "daily usage",
                                "data_usage",
                                round(
                                    get_json_dict_path(
                                        product_daily_usage,
                                        "$.internetUsage[0].totalUsage.total",
                                    ),
                                    1,
                                ),
                                self.create_extra_attributes_list(
                                    get_json_dict_path(
                                        product_daily_usage,
                                        "$.internetUsage[0].totalUsage",
                                    )
                                )
                                | {
                                    "daily_peak": daily_peak,
                                    "daily_off_peak": daily_off_peak,
                                    "daily_total": daily_total,
                                    "daily_date": daily_date,
                                },
                            )
                        )
                if modem is not False:
                    modem_settings = self.modem_settings(modem.get("mac"))
                    if modem_settings is not False:
                        new_products.update(
                            self.construct_extra_sensor(
                                product,
                                "modem",
                                "modem",
                                modem.get("name"),
                                self.create_extra_attributes_list(modem)
                                | modem_settings,
                            )
                        )
                    network_topology = clean_ipv6(
                        self.network_topology(modem.get("mac"))
                    )
                    new_products.update(
                        self.construct_extra_sensor(
                            product,
                            "network",
                            "network",
                            network_topology.get("model"),
                            self.create_extra_attributes_list(network_topology),
                        )
                    )
                    wireless_settings = self.wireless_settings(
                        modem.get("mac"), identifier
                    )
                    if wireless_settings is not False:
                        wifi_qr = None
                        new_products.update(
                            self.construct_extra_sensor(
                                product,
                                "wi-fi",
                                "wifi",
                                wireless_settings.get("wirelessEnabled"),
                                self.create_extra_attributes_list(wireless_settings),
                            )
                        )
                        if "networkKey" in wireless_settings.get(
                            "singleSSIDRoamingSettings"
                        ):
                            network_key = (
                                wireless_settings.get("singleSSIDRoamingSettings")
                                .get("networkKey")
                                .replace(":", r"\:")
                            )
                            wifi_qr = f"WIFI:S:{wireless_settings.get('singleSSIDRoamingSettings').get('name')};T:WPA;P:{network_key};;"
                            new_products.update(
                                self.construct_extra_sensor(
                                    product, "wi-fi qr", "qr", wifi_qr
                                )
                            )
            elif type == "dtv":
                """-------------------"""
                """| EXTRA DTV SENSORS |"""
                """ ------------------- """
                if not product.product_ignore_extra_sensor:
                    billcycle = self.bill_cycles(type, identifier, 1)
                    if billcycle is False:
                        _LOGGER.debug(
                            "[create_extra_sensors|dtv|billcycle] Failed to fetch, skipping"
                        )
                        continue
                    product_usage = self.product_usage(
                        type,
                        identifier,
                        billcycle.get("start_date"),
                        billcycle.get("end_date"),
                    )
                    if product_usage is False:
                        _LOGGER.debug(
                            "[create_extra_sensors|dtv|product_usage] Failed to fetch, skipping"
                        )
                        continue
                    devices = self.device_details(type, identifier)
                    if devices is False:
                        _LOGGER.debug(
                            "[create_extra_sensors|dtv|devices] Failed to fetch, skipping"
                        )
                        continue

                    self.total_cost += str_to_float(
                        get_json_dict_path(
                            product_usage, "$.dtv.totalUsage.currentUsage"
                        )
                    )

                    new_products.update(
                        self.construct_extra_sensor(
                            product,
                            "usage",
                            "euro",
                            str_to_float(
                                get_json_dict_path(
                                    product_usage, "$.dtv.totalUsage.currentUsage"
                                )
                            ),
                            self.create_extra_attributes_list(
                                get_json_dict_path(product_usage, "$.dtv")
                            )
                            | product_type_attr,
                        )
                    )
                    for idx, _data in enumerate(devices.get("dtv")):
                        new_products.update(
                            self.construct_extra_sensor(
                                product,
                                "dtv device",
                                "dtv",
                                get_json_dict_path(devices, f"$.dtv[{idx}].boxName"),
                                self.create_extra_attributes_list(
                                    get_json_dict_path(devices, f"$.dtv[{idx}]")
                                ),
                            )
                        )
            elif type == "mobile":
                """----------------------"""
                """| EXTRA MOBILE SENSORS |"""
                """ ---------------------- """
                if plan_identifier != identifier:
                    bundle_key = format_entity_name(
                        f"{self.user_details.get('identity_id')} {plan_identifier} {type} bundle"
                    )
                    usage = self.mobile_bundle_usage(plan_identifier, identifier)
                    if usage is False:
                        _LOGGER.debug(
                            "[create_extra_sensors|mobile|usage] Failed to fetch, skipping"
                        )
                        continue
                    next_billing_date = usage.get("nextBillingDate")
                    if next_billing_date is False:
                        _LOGGER.debug(
                            "[create_extra_sensors|mobile|next_billing_date] Failed to fetch, skipping"
                        )
                        continue
                    next_billing_date_time = datetime.strptime(
                        usage.get("nextBillingDate"), DATETIME_FORMAT
                    ).replace(tzinfo=None)
                    days_until = (next_billing_date_time - datetime.now()).days
                    attr_to_merge = {
                        "days_until": days_until,
                        "next_billing_date": next_billing_date,
                    }
                    bundleusage = self.mobile_bundle_usage(plan_identifier)
                    if bundleusage is False:
                        _LOGGER.debug(
                            "[create_extra_sensors|mobile|bundleusage] Failed to fetch, skipping"
                        )
                        continue
                    if self.all_products.get(bundle_key) is None:
                        """Bundle mobile sensors"""
                        _LOGGER.debug(
                            f"[TelenetClient|create_extra_sensors] Create Bundle Sensor BundleId: {plan_identifier}"
                        )
                        self.total_cost += str_to_float(
                            get_json_dict_path(bundleusage, "$.outOfBundle.usedUnits")
                        )
                        new_products.update(
                            self.construct_extra_sensor(
                                product,
                                "out of bundle",
                                "euro",
                                str_to_float(
                                    get_json_dict_path(
                                        bundleusage, "$.outOfBundle.usedUnits"
                                    )
                                ),
                                self.create_extra_attributes_list(
                                    get_json_dict_path(bundleusage, "$.outOfBundle")
                                )
                                | attr_to_merge
                                | product_type_attr,
                                use_plan_identifier=True,
                            )
                        )
                        for data in bundleusage.get("shared").get("data"):
                            new_products.update(
                                self.construct_extra_sensor(
                                    product,
                                    data.get("bucketType"),
                                    "usage_percentage_mobile",
                                    data.get("usedPercentage"),
                                    {
                                        "usage": f"{data.get('usedUnits')}/{data.get('startUnits')} {data.get('unitType')}"
                                    }
                                    | data
                                    | attr_to_merge,
                                    use_plan_identifier=True,
                                )
                            )
                        for data in bundleusage.get("shared").get("text"):
                            new_products.update(
                                self.construct_extra_sensor(
                                    product,
                                    "sms",
                                    "mobile_sms",
                                    data.get("usedUnits"),
                                    {"usage": f"{data.get('usedUnits')} SMSes"} | data,
                                    use_plan_identifier=True,
                                )
                            )
                        for data in bundleusage.get("shared").get("voice"):
                            new_products.update(
                                self.construct_extra_sensor(
                                    product,
                                    "voice",
                                    "mobile_voice",
                                    float_to_timestring(
                                        data.get("usedUnits"), data.get("unitType")
                                    ),
                                    {
                                        "usage": float_to_timestring(
                                            data.get("usedUnits"), data.get("unitType")
                                        )
                                    }
                                    | data
                                    | attr_to_merge,
                                    use_plan_identifier=True,
                                )
                            )
                    """ Child mobile sensors """
                    self.total_cost += str_to_float(
                        get_json_dict_path(usage, "$.outOfBundle.usedUnits")
                    )
                    new_products.update(
                        self.construct_extra_sensor(
                            product,
                            "out of bundle",
                            "euro",
                            str_to_float(
                                get_json_dict_path(usage, "$.outOfBundle.usedUnits")
                            ),
                            self.create_extra_attributes_list(
                                get_json_dict_path(usage, "$.outOfBundle")
                            )
                            | attr_to_merge
                            | product_type_attr,
                        )
                    )
                    for data in usage.get("shared").get("data"):
                        new_products.update(
                            self.construct_extra_sensor(
                                product,
                                data.get("name").lower(),
                                "mobile_data",
                                str_to_float(data.get("usedUnits")),
                                {
                                    "usage": f"{data.get('usedUnits')} {data.get('unitType')}"
                                }
                                | data
                                | attr_to_merge,
                                False,
                                data.get("unitType"),
                            )
                        )
                    for data in usage.get("shared").get("text"):
                        new_products.update(
                            self.construct_extra_sensor(
                                product,
                                data.get("name").lower().replace("text", "sms"),
                                "mobile_sms",
                                data.get("usedUnits"),
                                {"usage": f"{data.get('usedUnits')} SMSes"}
                                | data
                                | attr_to_merge,
                            )
                        )
                    for data in usage.get("shared").get("voice"):
                        new_products.update(
                            self.construct_extra_sensor(
                                product,
                                data.get("name").lower(),
                                "mobile_voice",
                                float_to_timestring(
                                    data.get("usedUnits"), data.get("unitType")
                                ),
                                {
                                    "usage": float_to_timestring(
                                        data.get("usedUnits"), data.get("unitType")
                                    )
                                }
                                | data
                                | attr_to_merge,
                            )
                        )
                else:
                    _LOGGER.debug(
                        f"[TelenetClient|MOBILE] {type} BundleId: {plan_identifier}, id: {identifier}, {product.product_description_key}"
                    )
                    usage = self.mobile_usage(identifier)
                    if usage is False:
                        _LOGGER.debug(
                            "[create_extra_sensors|mobile|usage] Failed to fetch, skipping"
                        )
                        continue
                    next_billing_date = usage.get("nextBillingDate")
                    next_billing_date_time = datetime.strptime(
                        usage.get("nextBillingDate"), DATETIME_FORMAT
                    ).replace(tzinfo=None)
                    days_until = (next_billing_date_time - datetime.now()).days
                    attr_to_merge = {
                        "days_until": days_until,
                        "next_billing_date": next_billing_date,
                    }
                    """ Non bundle mobile sensors """
                    self.total_cost += str_to_float(
                        get_json_dict_path(usage, "$.outOfBundle.usedUnits")
                    )
                    new_products.update(
                        self.construct_extra_sensor(
                            product,
                            "out of bundle",
                            "euro",
                            str_to_float(
                                get_json_dict_path(usage, "$.outOfBundle.usedUnits")
                            ),
                            self.create_extra_attributes_list(
                                get_json_dict_path(usage, "$.outOfBundle")
                            )
                            | attr_to_merge
                            | product_type_attr,
                            use_plan_identifier=True,
                        )
                    )
                    data = usage.get("total").get("data")
                    if (
                        int(data.get("startUnits")) > 0
                        or int(data.get("remainingUnits")) > 0
                        or int(data.get("usedUnits")) > 0
                    ):
                        new_products.update(
                            self.construct_extra_sensor(
                                product,
                                "data",
                                "mobile_data",
                                str_to_float(data.get("usedUnits")),
                                {
                                    "usage": f"{data.get('usedUnits')} {data.get('unitType')}"
                                }
                                | data
                                | attr_to_merge,
                                False,
                                data.get("unitType"),
                            )
                        )
                    data = usage.get("total").get("text")
                    if (
                        int(data.get("startUnits")) > 0
                        or int(data.get("remainingUnits")) > 0
                        or int(data.get("usedUnits")) > 0
                    ):
                        new_products.update(
                            self.construct_extra_sensor(
                                product,
                                "sms",
                                "mobile_sms",
                                data.get("usedUnits"),
                                {
                                    "usage": f"{data.get('usedUnits')} / {data.get('startUnits')} SMSes"
                                }
                                | data
                                | attr_to_merge,
                            )
                        )
                    data = usage.get("total").get("voice")
                    if (
                        int(data.get("startUnits")) > 0
                        or int(data.get("remainingUnits")) > 0
                        or int(data.get("usedUnits")) > 0
                    ):
                        new_products.update(
                            self.construct_extra_sensor(
                                product,
                                "sms",
                                "mobile_voice",
                                float_to_timestring(
                                    data.get("usedUnits"), data.get("unitType")
                                ),
                                {
                                    "usage": f"{data.get('usedUnits')} / {data.get('startUnits')} {data.get('unitType').lower()}"
                                }
                                | data
                                | attr_to_merge,
                            )
                        )

        product_name = "current invoice"
        product_key = format_entity_name(
            f"{self.user_details.get('customer_number')} {product_name}"
        )
        new_products.update(
            {
                product_key: TelenetProduct(
                    product_identifier=f"{self.user_details.get('customer_number')} {product_name}",
                    product_type="invoice",
                    product_description_key="euro",
                    product_name=f"{product_name}",
                    product_key=product_key,
                    product_plan_identifier=self.user_details.get("customer_number"),
                    product_plan_label="Customer",
                    product_state=self.total_cost,
                    product_extra_sensor=True,
                )
            }
        )
        product_name = "user details"
        product_key = format_entity_name(
            f"{self.user_details.get('customer_number')} {product_name}"
        )
        new_products.update(
            {
                product_key: TelenetProduct(
                    product_identifier=f"{product_name}",
                    product_type="user",
                    product_description_key="user",
                    product_name=f"{product_name}",
                    product_key=product_key,
                    product_plan_identifier=self.user_details.get("customer_number"),
                    product_plan_label="Customer",
                    product_state=self.user_details.get("first_name"),
                    product_extra_attributes=self.user_details,
                    product_extra_sensor=True,
                )
            }
        )

        product_name = "customer"
        product_key = format_entity_name(
            f"{self.user_details.get('customer_number')} {product_name}"
        )
        customer = self.customer()
        new_products.update(
            {
                product_key: TelenetProduct(
                    product_identifier=f"{product_name}",
                    product_type="customer",
                    product_description_key="customer",
                    product_name=f"{product_name}",
                    product_key=product_key,
                    product_plan_identifier=self.user_details.get("customer_number"),
                    product_plan_label="Customer",
                    product_state=customer.get("accountNumber"),
                    product_extra_attributes=customer,
                    product_extra_sensor=True,
                )
            }
        )

        mailboxes = self.mailboxesandaliases()
        for mailbox in mailboxes.get("mailboxes"):
            if "aliases" in mailbox and len(mailbox.get("aliases")):
                for alias in mailbox.get("aliases"):
                    product_name = f"Alias {alias.get('mailboxAliasId')}"
                    product_key = format_entity_name(product_name)
                    new_products.update(
                        {
                            product_key: TelenetProduct(
                                product_identifier=product_name,
                                product_type="mailbox",
                                product_description_key="mailbox",
                                product_name=alias.get("mailboxAliasId"),
                                product_key=product_key,
                                product_plan_identifier=self.user_details.get(
                                    "customer_number"
                                ),
                                product_plan_label="Customer",
                                product_state=mailbox.get("virus"),
                                product_extra_attributes=mailbox,
                                product_extra_sensor=True,
                            )
                        }
                    )
            else:
                product_name = mailbox.get("mailboxUUID")
                product_key = format_entity_name(
                    f"{self.user_details.get('customer_number')} {product_name}"
                )
                new_products.update(
                    {
                        product_key: TelenetProduct(
                            product_identifier=f"{product_name}",
                            product_type="mailbox",
                            product_description_key="mailbox",
                            product_name=f"{product_name}",
                            product_key=product_key,
                            product_plan_identifier=self.user_details.get(
                                "customer_number"
                            ),
                            product_plan_label="Customer",
                            product_state=mailbox.get("virus"),
                            product_extra_attributes=mailbox,
                            product_extra_sensor=True,
                        )
                    }
                )

        self.all_products.update(new_products)
        return True

    def create_extra_attributes_list(self, attr_list):
        """Create extra attributes for a sensor."""
        attributes = {}
        for key in attr_list:
            attributes[key] = attr_list[key]
        return attributes

    def set_extra_attributes(self) -> bool:
        """Set extra attributes per product."""
        for product in self.all_products:
            product = self.all_products[product]
            if not product.product_extra_sensor:
                if (
                    product.product_subscription_info
                    and len(product.product_subscription_info) > 0
                ):
                    info = product.product_subscription_info
                else:
                    info = self.plan_products.get(product.product_identifier)
                _LOGGER.debug(
                    f"[TelenetClient|set_extra_attributes] Setting extra attributes for {product.product_identifier}"
                )
                if info and len(info):
                    extra_attributes = {}
                    if product.product_type == "internet":
                        attributes = TelenetInternetProductExtraAttributes()
                    elif product.product_type == "mobile":
                        attributes = TelenetMobileProductExtraAttributes()
                    elif product.product_type == "dtv":
                        attributes = TelenetDtvProductExtraAttributes()
                    elif product.product_type == "telephone":
                        attributes = TelenetTelephoneProductExtraAttributes()
                    elif product.product_type == "bundle":
                        attributes = TelenetBundleProductExtraAttributes()
                    for key in dir(attributes):
                        if key[0:2] != "__":
                            if key in info:
                                extra_attributes[key] = info.get(key)
                    product.product_extra_attributes |= extra_attributes
        return True

    def product_details(self, url):
        """Fetch product_details."""
        response = self.request(url, "product_details", None, 200)
        if response is False:
            return False
        return response.json()

    def plan_info(self):
        """Fetch PLAN product subscriptions."""
        self.plan_products = {}
        _LOGGER.debug("[TelenetClient|plan_info] Fetching plan info from Telenet")
        response = self.request(
            f"{self.environment.ocapi_public_api}/product-service/v1/product-subscriptions?producttypes=PLAN",
            "[TelenetClient|planInfo]",
            None,
            None,
        )
        if response is False:
            return False
        for plan in response.json():
            self.plan_products[plan.get("identifier")] = plan
        return False

    def bill_cycles(self, product_type, product_identifier, count=1):
        """Fetch bill cycles."""
        _LOGGER.debug(
            f"[TelenetClient|bill_cycle] Fetching bill_cycles info from Telenet for {product_identifier} ({product_type})"
        )
        response = self.request(
            f"{self.environment.ocapi_public_api}/billing-service/v1/account/products/{product_identifier}/billcycle-details?producttype={product_type}&count={count}",
            "[TelenetClient|bill_cycles]",
            None,
            None,
        )
        if response is False:
            return False
        cycle = response.json().get("billCycles")[0]
        if product_type == "internet":
            return {
                "start_date": cycle.get("startDate"),
                "end_date": cycle.get("endDate"),
                "cycles": response.json().get("billCycles"),
            }
        else:
            return {
                "start_date": cycle.get("startDate"),
                "end_date": cycle.get("endDate"),
            }

    def product_usage(self, product_type, product_identifier, startDate, endDate):
        """Fetch product_usage."""
        response = self.request(
            f"{self.environment.ocapi_public_api}/product-service/v1/products/{product_type}/{product_identifier}/usage?fromDate={startDate}&toDate={endDate}",
            "[TelenetClient|product_usage]",
            None,
            None,
        )
        if response is False:
            return False
        return response.json()

    def product_daily_usage(
        self, product_type, product_identifier, bill_cycle, from_date, to_date
    ):
        """Fetch daily usage."""
        response = self.request(
            f"{self.environment.ocapi_public_api}/product-service/v1/products/{product_type}/{product_identifier}/dailyusage?billcycle={bill_cycle}&fromDate={from_date}&toDate={to_date}",
            "[TelenetClient|product_daily_usage]",
            None,
            None,
        )
        if response is False:
            return False
        if response.status_code != 200:
            return {}
        return response.json()

    def product_subscriptions(self):
        """Fetch product subscriptions for all product types."""
        for product_type in self.product_types:
            _LOGGER.debug(
                f"[TelenetClient|product_subscriptions] Fetching product plan infos from Telenet for {product_type}"
            )
            response = self.request(
                f"{self.environment.ocapi_public_api}/product-service/v1/product-subscriptions?producttypes={product_type.upper()}",
                "[TelenetClient|product_subscriptions]",
                None,
                None,
            )
            if response is False:
                continue
            for product in response.json():
                self.all_products[
                    product.get("identifier")
                ].product_subscription_info = product

    def get_simdetail(self, mobile):
        """Fetch sim details."""
        if len(self._simdetails) == 0:
            self._simdetails = self.simdetails()
        for simdetail in self._simdetails:
            if simdetail.get("mobile") == mobile:
                return simdetail
        return None

    def simdetails(self):
        """Fetch mobile usage."""
        response = self.request(
            f"{self.environment.ocapi_public_api}/mobile-service/v2/simdetails?status=ACTIVATION_IN_PROGRESS",
            "[TelenetClient|simdetails]",
            None,
            200,
        )
        if response is False:
            return False
        return response.json()

    def mobile_usage(self, product_identifier):
        """Fetch mobile usage."""
        response = self.request(
            f"{self.environment.ocapi_public_api}/mobile-service/v3/mobilesubscriptions/{product_identifier}/usages",
            "[TelenetClient|mobile_usage]",
            None,
            200,
        )
        if response is False:
            return False
        return response.json()

    def mobile_bundle_usage(self, bundle_identifier, line_identifier=None):
        """Fetch mobile bundle usage."""
        if line_identifier is not None:
            response = self.request(
                f"{self.environment.ocapi_public_api}/mobile-service/v3/mobilesubscriptions/{bundle_identifier}/usages?type=bundle&lineIdentifier={line_identifier}",
                "[TelenetClient|mobile_bundle_usage line_identifier]",
                None,
                200,
            )
        else:
            response = self.request(
                f"{self.environment.ocapi_public_api}/mobile-service/v3/mobilesubscriptions/{bundle_identifier}/usages?type=bundle",
                "[TelenetClient|mobile_bundle_usage bundle]",
                None,
                200,
            )
        if response is False:
            return False
        return response.json()

    def mailboxesandaliases(self):
        """Fetch mailboxesandaliases info."""
        response = self.request(
            f"{self.environment.ocapi_public_api}/mailbox-mgmt-service/v1/mailboxesandaliases",
            "[TelenetClient|mailboxesandaliases]",
            None,
            200,
        )
        if response is False:
            return False
        return response.json()

    def modems(self, product_identifier):
        """Fetch modem info."""
        response = self.request(
            f"{self.environment.ocapi_public_api}/resource-service/v1/modems?productIdentifier={product_identifier}",
            "[TelenetClient|modems]",
            None,
            200,
        )
        if response is False:
            return False
        return response.json()

    def modem_settings(self, mac):
        """Fetch modem advanced settings info."""
        response = self.request(
            f"{self.environment.ocapi_public_api}/resource-service/v1/modems/{mac}/advance-settings",
            "[TelenetClient|modems]",
            None,
            None,
        )
        if response is False or response.status_code > 404:
            return False
        return response.json()

    def network_topology(self, mac):
        """Fetch network topology."""
        response = self.request(
            f"{self.environment.ocapi_public_api}/resource-service/v1/network-topology/{mac}?withClients=true",
            "[TelenetClient|network_topology]",
            None,
            200,
        )
        if response is False:
            return False
        return response.json()

    def wireless_settings(self, mac, product_identifier):
        """Fetch wireless settings."""
        response = self.request(
            f"{self.environment.ocapi_public_api}/resource-service/v1/modems/{mac}/wireless-settings?withmetadata=true&withwirelessservice=true&productidentifier={product_identifier}",
            "[TelenetClient|wireless_settings]",
            None,
            None,
        )
        if response is False or response.status_code == 500:
            return False
        return response.json()

    def device_details(self, product_type, product_identifier):
        """Fetch device details."""
        response = self.request(
            f"{self.environment.ocapi_public_api}/product-service/v1/products/{product_type}/{product_identifier}/devicedetails",
            "[TelenetClient|device_details]",
            None,
            200,
        )
        if response is False:
            return False
        return response.json()

    def address(self, address_id):
        """Fetch address."""
        _LOGGER.debug(f"[TelenetClient|address] Fetching address {address_id}")
        if address_id is None or len(address_id) == 0:
            return {}
        if self.addresses.get(address_id) is not None:
            return self.addresses.get(address_id)
        response = self.request(
            f"{self.environment.ocapi_public_api}/contact-service/v1/contact/addresses/{address_id}",
            "[TelenetClient|address]",
            None,
            200,
        )
        if response is False:
            return False
        self.addresses |= {address_id: response.json()}
        return response.json()

    def customer(self):
        """Fetch customer info."""
        response = self.request(
            f"{self.environment.ocapi_public_api}/customer-service/v1/customers",
            "[TelenetClient|customer]",
            None,
            200,
        )
        if response is False:
            return False
        return response.json()

    # https://api.prd.telenet.be/ocapi/public/?p=customerproductholding,eligibleproducts
    # V1 API calls
    def api_v1_call(self):
        """Fetch all details for V1."""
        response = self.request(
            f"{self.environment.ocapi_public}/?p=accounts,bills,customerproductholding,eligibleproducts,contactdetails,modems,modemdetails,internetusage,internetusagereminder,digitaltvdetails,digitaltvlimits,digitaltvbilledusage,digitaltvunbilledusage,mobilesubscriptions",
            "[TelenetClient|customerproductholding]",
            None,
            200,
        )
        if response is False:
            return False
        return response.json()

    def buildv1(self, api_v1_call):
        """Build V1 Sensors."""
        new_products = {}
        if "accounts" in api_v1_call and len(api_v1_call.get("accounts")):
            for account in api_v1_call.get("accounts"):
                product_name = "customer"
                product_key = format_entity_name(
                    f"{self.user_details.get('customer_number')} {product_name}"
                )
                new_products.update(
                    {
                        product_key: TelenetProduct(
                            product_identifier=f"{product_name}",
                            product_type="customer",
                            product_description_key="customer",
                            product_name=f"{product_name}",
                            product_key=product_key,
                            product_plan_identifier=self.user_details.get(
                                "customer_number"
                            ),
                            product_plan_label="Customer",
                            product_state=account.get("accountnumber"),
                            product_extra_attributes=account,
                            product_extra_sensor=True,
                        )
                    }
                )
        product_name = "user details"
        product_key = format_entity_name(
            f"{self.user_details.get('customer_number')} {product_name}"
        )
        new_products.update(
            {
                product_key: TelenetProduct(
                    product_identifier=f"{product_name}",
                    product_type="user",
                    product_description_key="user",
                    product_name=f"{product_name}",
                    product_key=product_key,
                    product_plan_identifier=self.user_details.get("customer_number"),
                    product_plan_label="Customer",
                    product_state=self.user_details.get("first_name"),
                    product_extra_attributes=self.user_details,
                    product_extra_sensor=True,
                )
            }
        )

        if "internetusage" in api_v1_call and len(api_v1_call.get("internetusage")):
            for internetusage in api_v1_call.get("internetusage"):
                usage = internetusage.get("availableperiods")[0].get("usages")[0]
                specurl = usage.get("specurl")
                details = self.product_details(specurl)
                total_volume = usage.get("extendedvolume").get("volume")
                if (
                    type(
                        details.get("product")
                        .get("characteristics")
                        .get("service_category_limit")
                    )
                    == dict
                ):
                    total_volume += (
                        int(
                            details.get("product")
                            .get("characteristics")
                            .get("service_category_limit")
                            .get("value")
                        )
                        * 1048576
                    )
                elif (
                    type(
                        details.get("product")
                        .get("characteristics")
                        .get("elementarycharacteristics")
                    )
                    == list
                ):
                    for elem in (
                        details.get("product")
                        .get("characteristics")
                        .get("elementarycharacteristics")
                    ):
                        if elem.get("key") == "internet_usage_limit":
                            total_volume += int(elem.get("value")) * 1048576
                            break
                else:
                    total_volume += usage.get("includedvolume")
                total_usage = 0
                if "wifree" in usage.get("totalusage"):
                    total_usage += usage.get("totalusage").get("wifree")
                if "peak" in usage.get("totalusage"):
                    total_usage += usage.get("totalusage").get("peak")
                    usage_pct = 100 * total_usage / total_volume
                    total_usage_with_offpeak = round((total_usage+usage.get('totalusage').get('offpeak'))/1048576)
                    peak_usage = round(usage.get('totalusage').get('peak')/1048576)
                    offpeak_usage = round(usage.get('totalusage').get('peak')/1048576)
                else:
                    usage_pct =  usage.get("usedpercentage")
                    total_usage = usage.get("totalusage").get("includedvolume") + usage.get("totalusage").get("includedvolume")
                    total_usage_with_offpeak = total_usage/1048576
                    peak_usage = 0
                    offpeak_usage = 0
                period_start = datetime.strptime(
                    usage.get("periodstart"), "%Y-%m-%dT%H:%M:%S.0%z"
                )
                period_end = datetime.strptime(
                    usage.get("periodend"), "%Y-%m-%dT%H:%M:%S.0%z"
                )
                period_length = period_end - period_start
                period_length_days = period_length.days
                period_length_seconds = period_length.total_seconds()
                period_used = datetime.now(period_start.tzinfo) - period_start
                period_used_seconds = period_used.total_seconds()
                period_used_percentage = round(
                    100 * period_used_seconds / period_length_seconds, 1
                )
                if period_used_percentage > 100:
                    period_used_percentage = 100
                identifier = internetusage.get("businessidentifier")
                product_name = "internet usage"
                product_key = format_entity_name(
                    f"{internetusage.get('businessidentifier')} {product_name}"
                )
                new_products.update(
                    {
                        product_key: TelenetProduct(
                            product_identifier=f"{product_name}",
                            product_type="usage",
                            product_description_key="usage_percentage",
                            product_name=f"{product_name}",
                            product_key=product_key,
                            product_plan_identifier=self.user_details.get(
                                "customer_number"
                            ),
                            product_plan_label="Customer",
                            product_state=round(usage_pct, 2),
                            product_extra_attributes={
                                "last_update": internetusage.get("lastupdated"),
                                "identifier": identifier,
                                "start_date": usage.get("periodstart"),
                                "end_date": usage.get("periodend"),
                                "days_until": period_length_days,
                                "total_volume": f"{total_volume/1048576} GB",
                                "wifree_usage": f"{round(usage.get('totalusage').get('wifree')/1048576)} GB",
                                "total_usage": f"{round(total_usage/1048576)} GB",
                                "total_usage_with_offpeak": f"{total_usage_with_offpeak} GB",
                                "peak_usage": f"{peak_usage} GB",
                                "offpeak_usage": f"{offpeak_usage} GB",
                                "used_percentage": round(usage_pct, 2),
                                "period_used_percentage": period_used_percentage,
                                "period_remaining_percentage": (
                                    100 - period_used_percentage
                                ),
                                "squeezed": usage_pct >= 100,
                                "period_length": period_length_days,
                            },
                            product_extra_sensor=True,
                        )
                    }
                )

                daily_peak = []
                daily_off_peak = []
                daily_date = []

                dailyusages = usage.get("totalusage").get("dailyusages")
                if len(dailyusages) != 0:
                    for day in dailyusages:
                        if "peak" in day:
                            daily_peak.append(day.get("peak") / 1048576)
                            daily_off_peak.append(day.get("offpeak") / 1048576)
                        daily_date.append(day.get("date"))

                product_name = "internet daily usage"
                product_key = format_entity_name(
                    f"{internetusage.get('businessidentifier')} {product_name}"
                )
                new_products.update(
                    {
                        product_key: TelenetProduct(
                            product_identifier=f"{product_name}",
                            product_type="usage",
                            product_description_key="data_usage",
                            product_name=f"{product_name}",
                            product_key=product_key,
                            product_plan_identifier=self.user_details.get(
                                "customer_number"
                            ),
                            product_plan_label="Customer",
                            product_state=usage.get("totalusage").get("peak") / 1048576,
                            product_extra_attributes={
                                "daily_peak": daily_peak,
                                "daily_off_peak": daily_off_peak,
                                "daily_date": daily_date,
                            },
                            product_extra_sensor=True,
                        )
                    }
                )

        if "modems" in api_v1_call and len(api_v1_call.get("modems")):
            for modem in api_v1_call.get("modems"):
                product_name = "modem"
                product_key = format_entity_name(
                    f"{modem.get('internetlineidentifier')} {product_name}"
                )
                new_products.update(
                    {
                        product_key: TelenetProduct(
                            product_identifier=f"{product_name}",
                            product_type="modem",
                            product_description_key="modem",
                            product_name=f"{product_name}",
                            product_key=product_key,
                            product_plan_identifier=self.user_details.get(
                                "customer_number"
                            ),
                            product_plan_label="Customer",
                            product_state=modem.get("hardware"),
                            product_extra_attributes=modem,
                            product_extra_sensor=True,
                        )
                    }
                )
        if "digitaltvdetails" in api_v1_call and len(
            api_v1_call.get("digitaltvdetails")
        ):
            for dtv in api_v1_call.get("digitaltvdetails"):
                for device in dtv.get("devices"):
                    product_name = (
                        f"{dtv.get('identifier')} {device.get('serialnumber')}"
                    )
                    product_key = format_entity_name(
                        f"{internetusage.get('businessidentifier')} {product_name}"
                    )
                    new_products.update(
                        {
                            product_key: TelenetProduct(
                                product_identifier=f"{product_name}",
                                product_type="dtv",
                                product_description_key="dtv",
                                product_name=f"{product_name}",
                                product_key=product_key,
                                product_plan_identifier=self.user_details.get(
                                    "customer_number"
                                ),
                                product_plan_label="Customer",
                                product_state=device.get("type"),
                                product_extra_attributes=dtv,
                                product_extra_sensor=True,
                            )
                        }
                    )
        if "digitaltvunbilledusage" in api_v1_call and len(
            api_v1_call.get("digitaltvunbilledusage")
        ):
            for dtv in api_v1_call.get("digitaltvunbilledusage"):
                product_name = f"{dtv.get('identifier')} usage"
                product_key = format_entity_name(
                    f"{internetusage.get('businessidentifier')} {product_name}"
                )
                cost = 0
                if "dtvusage" in dtv:
                    cost += str_to_float(dtv.get("dtvusage").get("total"))
                if "tvodusage" in dtv:
                    cost += str_to_float(dtv.get("tvodusage").get("total"))
                new_products.update(
                    {
                        product_key: TelenetProduct(
                            product_identifier=f"{product_name}",
                            product_type="dtv",
                            product_description_key="euro",
                            product_name=f"{product_name}",
                            product_key=product_key,
                            product_plan_identifier=self.user_details.get(
                                "customer_number"
                            ),
                            product_plan_label="Customer",
                            product_state=cost,
                            product_extra_attributes=dtv,
                            product_extra_sensor=True,
                        )
                    }
                )
        if "bills" in api_v1_call and len(api_v1_call.get("bills")):
            amount = 0
            bills = {}
            for bills_array in api_v1_call.get("bills"):
                for bill in bills_array.get("bills"):
                    if not bill.get("paid"):
                        amount += str_to_float(bill.get("billamount").get("amount"))
            product_name = "open invoices"
            product_key = format_entity_name(
                f"{internetusage.get('businessidentifier')} {product_name}"
            )
            new_products.update(
                {
                    product_key: TelenetProduct(
                        product_identifier=f"{product_name}",
                        product_type="invoice",
                        product_description_key="euro",
                        product_name=f"{product_name}",
                        product_key=product_key,
                        product_plan_identifier=self.user_details.get(
                            "customer_number"
                        ),
                        product_plan_label="Customer",
                        product_state=amount,
                        product_extra_attributes=bills,
                        product_extra_sensor=True,
                    )
                }
            )

        if len(new_products):
            self.all_products.update(new_products)
