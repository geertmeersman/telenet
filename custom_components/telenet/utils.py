from datetime import date, datetime, timedelta
import json
import re

from jsonpath import jsonpath
import requests

from .const import _LOGGER, REQUEST_TIMEOUT


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
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.s = requests.Session()
        self.s.headers["User-Agent"] = "TelemeterPython/3"
        self.s.headers["x-alt-referer"] = "https://www2.telenet.be/nl/klantenservice/#/pages=1/menu=selfservice"

    def callTelenet(self, url, caller = "Not set", data = None, expectedStatusCode = "200", printResponse = False):
        if data == None:
            _LOGGER.debug(f"[{caller}] Calling GET {url}")
            response = self.s.get(url,timeout=REQUEST_TIMEOUT)
        else:
            _LOGGER.debug(f"[{caller}] Calling POST {url}")
            response = self.s.post(url,data,timeout=REQUEST_TIMEOUT)
        _LOGGER.debug(f"[{caller}] http status code = {response.status_code} (expecting {expectedStatusCode})")
        if printResponse:
            _LOGGER.debug(f"[{caller}] Response:\n{response.text}")
        if expectedStatusCode != None:
            assert response.status_code == expectedStatusCode
        
        return response

    def login(self):
        response = self.callTelenet("https://api.prd.telenet.be/ocapi/oauth/userdetails","login", None, None)
        if response.status_code == 200:
            # Return if already authenticated
            return response.json()
        assert response.status_code == 401
        # Fetch state & nonce
        state, nonce = response.text.split(",", maxsplit=2)
        # Log in
        self.callTelenet(f'https://login.prd.telenet.be/openid/oauth/authorize?client_id=ocapi&response_type=code&claims={{"id_token":{{"http://telenet.be/claims/roles":null,"http://telenet.be/claims/licenses":null}}}}&lang=nl&state={state}&nonce={nonce}&prompt=login',"login", None, None)
        self.callTelenet("https://login.prd.telenet.be/openid/login.do","login",{"j_username": self.username,"j_password": self.password,"rememberme": True}, 200)
        self.s.headers["X-TOKEN-XSRF"] = self.s.cookies.get("TOKEN-XSRF")
        response = self.callTelenet("https://api.prd.telenet.be/ocapi/oauth/userdetails","login", None, 200)
        return response.json()

    def userdetails(self):
        response = self.callTelenet("https://api.prd.telenet.be/ocapi/oauth/userdetails","userdetails", None, 200)
        return response.json()

    def product_details(self, url):
        response = self.callTelenet(url,"product_details",None, 200)
        return response.json()
        
    def planInfo(self):
        response = self.callTelenet("https://api.prd.telenet.be/ocapi/public/api/product-service/v1/product-subscriptions?producttypes=PLAN","planInfo", None, 200)
        return response.json()
    
    def billCycles(self, productType, productIdentifier, count = 3):
        response = self.callTelenet(f"https://api.prd.telenet.be/ocapi/public/api/billing-service/v1/account/products/{productIdentifier}/billcycle-details?producttype={productType}&count={count}","billCycles", None, 200)
        return response.json()
    
    def productUsage(self, productType, productIdentifier,startDate, endDate):
        response = self.callTelenet(f"https://api.prd.telenet.be/ocapi/public/api/product-service/v1/products/{productType}/{productIdentifier}/usage?fromDate={startDate}&toDate={endDate}","productUsage", None, 200)
        return response.json()

    def productDailyUsage(self, productType, productIdentifier,fromDate, toDate):
        response = self.callTelenet(f"https://api.prd.telenet.be/ocapi/public/api/product-service/v1/products/{productType}/{productIdentifier}/dailyusage?billcycle=CURRENT&fromDate={fromDate}&toDate={toDate}","productDailyUsage", None, 200)
        return response.json()

    def productSubscriptions(self, productType):
        response = self.callTelenet(f"https://api.prd.telenet.be/ocapi/public/api/product-service/v1/product-subscriptions?producttypes={productType}","productSubscriptions", None, 200)
        return response.json()

    def mobileUsage(self, productIdentifier):
        response = self.callTelenet(f"https://api.prd.telenet.be/ocapi/public/api/mobile-service/v3/mobilesubscriptions/{productIdentifier}/usages","mobileUsage", None, 200)
        return response.json()

    def mobileBundleUsage(self, bundleIdentifier, lineIdentifier = None):
        if lineIdentifier != None:
            response = self.callTelenet(f"https://api.prd.telenet.be/ocapi/public/api/mobile-service/v3/mobilesubscriptions/{bundleIdentifier}/usages?type=bundle&lineIdentifier={lineIdentifier}","mobileBundleUsage lineIdentifier", None, 200)
        else:
            response = self.callTelenet(f"https://api.prd.telenet.be/ocapi/public/api/mobile-service/v3/mobilesubscriptions/{bundleIdentifier}/usages?type=bundle","mobileBundleUsage bundle", None, 200)
        return response.json()

    def modems(self, productIdentifier):
        response = self.callTelenet(f"https://api.prd.telenet.be/ocapi/public/api/resource-service/v1/modems?productIdentifier={productIdentifier}","modems", None, 200)
        return response.json()

    def network_topology(self, mac):
        response = self.callTelenet(f"https://api.prd.telenet.be/ocapi/public/api/resource-service/v1/network-topology/{mac}?withClients=true","modems", None, 200)
        return response.json()

    def wireless_settings(self, mac, productIdentifier):
        response = self.callTelenet(f"https://api.prd.telenet.be/ocapi/public/api/resource-service/v1/modems/{mac}/wireless-settings?withmetadata=true&withwirelessservice=true&productidentifier={productIdentifier}","modems", None, 200)
        return response.json()
