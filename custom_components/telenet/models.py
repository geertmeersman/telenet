"""Models used by Telenet."""
from __future__ import annotations

from dataclasses import dataclass, field
import datetime
from typing import Any


@dataclass
class TelenetEnvironment:
    """Class to describe a Telenet environment."""

    ocapi: str
    openid: str
    referer: str
    x_alt_referer: str


@dataclass
class TelenetProduct:
    """Telenet product model."""

    product_name: str = ""
    product_suffix: str = ""
    product_state: str = "Inactive"
    product_identifier: str = "",
    product_type: str = ""
    product_description: str = ""
    product_specurl: str = ""
    product_info: list = field(default_factory=list)
    product_plan_identifier: str = ""
    product_subscription_info: list = field(default_factory=list)
