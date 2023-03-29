"""Telenet utils."""
from __future__ import annotations

from datetime import date, datetime, timedelta
import json
import re
from types import TracebackType

from aiohttp import ClientSession, ClientTimeout, ContentTypeError, FormData
from jsonpath import jsonpath
import requests

from .const import _LOGGER, REQUEST_TIMEOUT


def format_entity_name(string: str) -> str:
    """Format entity name."""
    string = re.sub(r"\s+", "_", string)
    string = re.sub(r"\W+", "", string).lower()
    return string

def sizeof_fmt(num, suffix="b"):
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"

def get_json_dict_path(dictionary, path):
    #_LOGGER.debug(f"[get_json_dict_path] Path: {path}, Dict: {dictionary}")
    json_dict = jsonpath(dictionary, path)
    if isinstance(json_dict, list):
        json_dict = json_dict[0]
    return json_dict

def get_localized(language, localizedcontent):
    #_LOGGER.debug(f"[get_localized] {language} {localizedcontent}")
    for lang in localizedcontent:
        if language == lang.get("locale"):
            return lang
    return localizedcontent[0]

class TelenetSession:

    session: ClientSession

    def __init__(
        self,
        username,
        password
    ) -> None:

        self.session = session if session else ClientSession()

        self.username = username
        self.password = password
        self.s = requests.Session()
        self.s.headers["User-Agent"] = USER_AGENT
        self.s.headers["x-alt-referer"] = X_ALT_REFERER


    def call_telenet(self, url, caller = "Not set", data = None, expected_status_code = "200", print_response = False):
        if data == None:
            _LOGGER.debug(f"[{caller}] Calling GET {url}")
            response = self.s.get(url,timeout=REQUEST_TIMEOUT)
        else:
            _LOGGER.debug(f"[{caller}] Calling POST {url}")
            response = self.s.post(url,data,timeout=REQUEST_TIMEOUT)
        _LOGGER.debug(f"[{caller}] http status code = {response.status_code} (expecting {expected_status_code})")
        if print_response:
            _LOGGER.debug(f"[{caller}] Response:\n{response.text}")
        if expected_status_code != None:
            assert response.status_code == expected_status_code, f"Expecting HTTP {expected_status_code} | Response HTTP {response.status_code}, Response: {response.text}"

        return response

    def login(self):
        response = self.call_telenet("https://api.prd.telenet.be/ocapi/oauth/userdetails","login", None, None)
        if response.status_code == 200:
            # Return if already authenticated
            return response.json()
        assert response.status_code == 401
        # Fetch state & nonce
        state, nonce = response.text.split(",", maxsplit=2)
        # Log in
        self.call_telenet(f'https://login.prd.telenet.be/openid/oauth/authorize?client_id=ocapi&response_type=code&claims={{"id_token":{{"http://telenet.be/claims/roles":null,"http://telenet.be/claims/licenses":null}}}}&lang=nl&state={state}&nonce={nonce}&prompt=login',"login", None, None)
        self.call_telenet("https://login.prd.telenet.be/openid/login.do","login",{"j_username": self.username,"j_password": self.password,"rememberme": True}, 200)
        self.s.headers["X-TOKEN-XSRF"] = self.s.cookies.get("TOKEN-XSRF")
        response = self.call_telenet("https://api.prd.telenet.be/ocapi/oauth/userdetails","login", None, 200)
        return response.json()

    def userdetails(self):
        response = self.call_telenet("https://api.prd.telenet.be/ocapi/oauth/userdetails","userdetails", None, 200)
        return response.json()

    def product_details(self, url):
        response = self.call_telenet(url,"product_details",None, 200)
        return response.json()

    def plan_info(self):
        response = self.call_telenet("https://api.prd.telenet.be/ocapi/public/api/product-service/v1/product-subscriptions?producttypes=PLAN","planInfo", None, 200)
        return response.json()

    def bill_cycles(self, product_type, product_identifier, count = 3):
        response = self.call_telenet(f"https://api.prd.telenet.be/ocapi/public/api/billing-service/v1/account/products/{product_identifier}/billcycle-details?producttype={product_type}&count={count}","bill_cycles", None, 200)
        return response.json()

    def product_usage(self, product_type, product_identifier,startDate, endDate):
        response = self.call_telenet(f"https://api.prd.telenet.be/ocapi/public/api/product-service/v1/products/{product_type}/{product_identifier}/usage?fromDate={startDate}&toDate={endDate}","product_usage", None, 200)
        return response.json()

    def product_daily_usage(self, product_type, product_identifier,fromDate, toDate):
        response = self.call_telenet(f"https://api.prd.telenet.be/ocapi/public/api/product-service/v1/products/{product_type}/{product_identifier}/dailyusage?billcycle=CURRENT&fromDate={fromDate}&toDate={toDate}","product_daily_usage", None, 200)
        return response.json()

    def product_subscriptions(self, product_type):
        response = self.call_telenet(f"https://api.prd.telenet.be/ocapi/public/api/product-service/v1/product-subscriptions?producttypes={product_type}","product_subscriptions", None, 200)
        return response.json()

    def mobile_usage(self, product_identifier):
        response = self.call_telenet(f"https://api.prd.telenet.be/ocapi/public/api/mobile-service/v3/mobilesubscriptions/{product_identifier}/usages","mobile_usage", None, 200)
        return response.json()

    def mobile_bundle_usage(self, bundle_identifier, line_identifier = None):
        if line_identifier != None:
            response = self.call_telenet(f"https://api.prd.telenet.be/ocapi/public/api/mobile-service/v3/mobilesubscriptions/{bundle_identifier}/usages?type=bundle&lineIdentifier={line_identifier}","mobile_bundle_usage line_identifier", None, 200)
        else:
            response = self.call_telenet(f"https://api.prd.telenet.be/ocapi/public/api/mobile-service/v3/mobilesubscriptions/{bundle_identifier}/usages?type=bundle","mobile_bundle_usage bundle", None, 200)
        return response.json()

    def modems(self, product_identifier):
        response = self.call_telenet(f"https://api.prd.telenet.be/ocapi/public/api/resource-service/v1/modems?productIdentifier={product_identifier}","modems", None, 200)
        return response.json()

    def network_topology(self, mac):
        response = self.call_telenet(f"https://api.prd.telenet.be/ocapi/public/api/resource-service/v1/network-topology/{mac}?withClients=true","network_topology", None, 200)
        return response.json()

    def wireless_settings(self, mac, product_identifier):
        response = self.call_telenet(f"https://api.prd.telenet.be/ocapi/public/api/resource-service/v1/modems/{mac}/wireless-settings?withmetadata=true&withwirelessservice=true&productidentifier={product_identifier}","wireless_settings", None, 200)
        return response.json()

    def device_details(self, product_type, product_identifier):
        response = self.call_telenet(f"https://api.prd.telenet.be/ocapi/public/api/product-service/v1/products/{product_type}/{product_identifier}/devicedetails","device_details", None, 200)
        return response.json()

    def active_products(self):
        response = self.call_telenet("https://api.prd.telenet.be/ocapi/public/api/product-service/v1/products?status=ACTIVE","active_products", None, 200)
        return response.json()
