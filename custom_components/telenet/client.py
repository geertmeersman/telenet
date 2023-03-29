"""Telenet API Client."""
from __future__ import annotations

import logging
from random import randint
import time
from types import TracebackType
from typing import Any
import urllib.parse

from requests import (
    ConnectionError,
    ConnectTimeout,
    HTTPError,
    ReadTimeout,
    Session,
    Timeout,
)

from .const import (
    BASE_HEADERS,
    DEFAULT_LANGUAGE,
    DEFAULT_TELENET_ENVIRONMENT,
    REQUEST_TIMEOUT,
)
from .exceptions import (
    BadCredentialsException,
    TelenetException,
    TelenetServiceException,
)
from .models import TelenetEnvironment, TelenetProduct

_LOGGER = logging.getLogger(__package__)

class TelenetClient:

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
        self.environment = environment
        self.session.headers = headers

    def request(
        self,
        url,
        caller = "Not set",
        data = None,
        expected = "200",
        log = False
    ) -> dict:
        if data == None:
            _LOGGER.debug(f"{caller} Calling GET {url}")
            response = self.session.get(url,timeout=REQUEST_TIMEOUT)
        else:
            _LOGGER.debug(f"{caller} Calling POST {url}")
            response = self.session.post(url,data,timeout=REQUEST_TIMEOUT)
        _LOGGER.debug(f"{caller} http status code = {response.status_code} (expecting {expected})")
        if log:
            _LOGGER.debug(f"{caller} Response:\n{response.text}")
        if expected != None and response.status_code != expected:
            raise TelenetServiceException(
                f"Expecting HTTP {expected} | Response HTTP {response.status_code}, Response: {response.text}"
            )
        return response

    def login(self) -> dict:
        """Start a new Telenet session with an user & password."""

        _LOGGER.critical(f"[TelenetClient|login|start]")
        response = self.request(f"{self.environment.ocapi}/oauth/userdetails","login", None, None)
        if response.status_code == 200:
            # Return if already authenticated
            return response.json()
        if response.status_code != 401:
            raise TelenetServiceException(
                f"HTTP {response.status_code} error while authenticating"
            )
        """Fetch state & nonce"""
        state, nonce = response.text.split(",", maxsplit=2)
        """Login process"""
        response = self.request(f'{self.environment.openid}/oauth/authorize?client_id=ocapi&response_type=code&claims={{"id_token":{{"http://telenet.be/claims/roles":null,"http://telenet.be/claims/licenses":null}}}}&lang=nl&state={state}&nonce={nonce}&prompt=login',"[TelenetClient|login|authorize]", None, None)
        if response.status_code != 200 or "openid/login" not in str(response.url):
            raise TelenetServiceException(response.text())
        response = self.request(f"{self.environment.openid}/login.do","[TelenetClient|login|login.do]",{"j_username": self.username,"j_password": self.password,"rememberme": True}, 200)
        if "authentication_error" in response.url:
            raise BadCredentialsException(response.text)
        self.session.headers["X-TOKEN-XSRF"] = self.session.cookies.get("TOKEN-XSRF")
        response = self.request("https://api.prd.telenet.be/ocapi/oauth/userdetails","[TelenetClient|login|user_details]", None, 200)
        user_details = response.json()
        if "customer_number" not in user_details:
            raise BadCredentialsException(
                f"HTTP {response.status_code} Missing customer number"
            )
        return response.json()

    def products(self) -> list:
        """ List all Telenet products"""
        products = []
        response = self.request("https://api.prd.telenet.be/ocapi/public/api/product-service/v1/products?status=ACTIVE","[TelenetClient|products]", None, 200)
        for a_product in response.json():
            for product in a_product.get("children"):
                products.append(TelenetProduct(
                    product_identifier= product.get('identifier'),
                    product_type= product.get('productType'),
                    product_info= {},
                    product_plan_identifier= a_product.get('identifier'),
                    product_subscription_info= {},
                    product_name= f"{product.get('identifier')} {product.get('productType')}",
                    product_state= product.get('status'),
                    product_description=product.get('label'),
                    product_specurl=product.get('specurl')
                ))
                if "options" in product and len(product.get("options")):
                    for option in product.get("options"):
                        if "identifier" in option:
                            products.append(TelenetProduct(
                                product_identifier= option.get('identifier'),
                                product_type= option.get('productType'),
                                product_info= {},
                                product_plan_identifier= a_product.get('identifier'),
                                product_subscription_info= {},
                                product_name= f"{option.get('identifier')} {option.get('productType')}",
                                product_state= option.get('status'),
                                product_description=option.get('label'),
                                product_specurl=option.get('specurl')
                            ))
            products.append(TelenetProduct(
                product_identifier= a_product.get('identifier'),
                product_type= a_product.get('productType'),
                product_info= {},
                product_plan_identifier= a_product.get('identifier'),
                product_subscription_info= {},
                product_name= f"{a_product.get('identifier')} {a_product.get('productType')}",
                product_state= a_product.get('status'),
                product_description=a_product.get('label'),
                product_specurl=a_product.get('specurl')
            ))

        return products


    def plan_info(self):
        response = self.request("https://api.prd.telenet.be/ocapi/public/api/product-service/v1/product-subscriptions?producttypes=PLAN","[TelenetClient|planInfo]", None, 200)
        return response.json()

    def bill_cycles(self, product_type, product_identifier, count = 3):
        response = self.request(f"https://api.prd.telenet.be/ocapi/public/api/billing-service/v1/account/products/{product_identifier}/billcycle-details?producttype={product_type}&count={count}","[TelenetClient|bill_cycles]", None, 200)
        return response.json()

    def product_usage(self, product_type, product_identifier,startDate, endDate):
        response = self.request(f"https://api.prd.telenet.be/ocapi/public/api/product-service/v1/products/{product_type}/{product_identifier}/usage?fromDate={startDate}&toDate={endDate}","[TelenetClient|product_usage]", None, 200)
        return response.json()

    def product_daily_usage(self, product_type, product_identifier,fromDate, toDate):
        response = self.request(f"https://api.prd.telenet.be/ocapi/public/api/product-service/v1/products/{product_type}/{product_identifier}/dailyusage?billcycle=CURRENT&fromDate={fromDate}&toDate={toDate}","[TelenetClient|product_daily_usage]", None, 200)
        return response.json()

    def product_subscriptions(self, product_type):
        response = self.request(f"https://api.prd.telenet.be/ocapi/public/api/product-service/v1/product-subscriptions?producttypes={product_type}","[TelenetClient|product_subscriptions]", None, 200)
        return response.json()

    def mobile_usage(self, product_identifier):
        response = self.request(f"https://api.prd.telenet.be/ocapi/public/api/mobile-service/v3/mobilesubscriptions/{product_identifier}/usages","[TelenetClient|mobile_usage]", None, 200)
        return response.json()

    def mobile_bundle_usage(self, bundle_identifier, line_identifier = None):
        if line_identifier != None:
            response = self.request(f"https://api.prd.telenet.be/ocapi/public/api/mobile-service/v3/mobilesubscriptions/{bundle_identifier}/usages?type=bundle&lineIdentifier={line_identifier}","[TelenetClient|mobile_bundle_usage line_identifier]", None, 200)
        else:
            response = self.request(f"https://api.prd.telenet.be/ocapi/public/api/mobile-service/v3/mobilesubscriptions/{bundle_identifier}/usages?type=bundle","[TelenetClient|mobile_bundle_usage bundle]", None, 200)
        return response.json()

    def modems(self, product_identifier):
        response = self.request(f"https://api.prd.telenet.be/ocapi/public/api/resource-service/v1/modems?productIdentifier={product_identifier}","[TelenetClient|modems]", None, 200)
        return response.json()

    def network_topology(self, mac):
        response = self.request(f"https://api.prd.telenet.be/ocapi/public/api/resource-service/v1/network-topology/{mac}?withClients=true","[TelenetClient|network_topology]", None, 200)
        return response.json()

    def wireless_settings(self, mac, product_identifier):
        response = self.request(f"https://api.prd.telenet.be/ocapi/public/api/resource-service/v1/modems/{mac}/wireless-settings?withmetadata=true&withwirelessservice=true&productidentifier={product_identifier}","[TelenetClient|wireless_settings]", None, 200)
        return response.json()

    def device_details(self, product_type, product_identifier):
        response = self.request(f"https://api.prd.telenet.be/ocapi/public/api/product-service/v1/products/{product_type}/{product_identifier}/devicedetails","[TelenetClient|device_details]", None, 200)
        return response.json()
