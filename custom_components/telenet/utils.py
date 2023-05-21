"""Telenet utils."""
from __future__ import annotations

import logging
import re

from jsonpath import jsonpath

_LOGGER = logging.getLogger(__name__)


def str_to_float(input) -> float:
    """Transform float to string."""
    if isinstance(input, str):
        return float(input.replace(",", "."))
    return input


def float_to_timestring(float_time, unit_type) -> str:
    """Transform float to timestring."""
    float_time = str_to_float(float_time)
    if unit_type.lower() == "seconds":
        float_time = float_time * 60 * 60
    elif unit_type.lower() == "minutes":
        float_time = float_time * 60
    # _LOGGER.debug(f"[float_to_timestring] Float Time {float_time}")
    hours, seconds = divmod(float_time, 3600)  # split to hours and seconds
    minutes, seconds = divmod(seconds, 60)  # split the seconds to minutes and seconds
    result = ""
    if hours:
        result += f" {hours:02.0f}" + "u"
    if minutes:
        result += f" {minutes:02.0f}" + " min"
    if seconds:
        result += f" {seconds:02.0f}" + " sec"
    if len(result) == 0:
        result = "0 sec"
    return result.strip()


def format_entity_name(string: str) -> str:
    """Format entity name."""
    string = string.strip()
    string = re.sub(r"\s+", "_", string)
    string = re.sub(r"\W+", "", string).lower()
    return string


def sizeof_fmt(num, suffix="b"):
    """Convert unit to human readable."""
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def get_json_dict_path(dictionary, path):
    """Fetch info based on jsonpath from dict."""
    # _LOGGER.debug(f"[get_json_dict_path] Path: {path}, Dict: {dictionary}")
    json_dict = jsonpath(dictionary, path)
    if isinstance(json_dict, list):
        json_dict = json_dict[0]
    return json_dict


def get_localized(language, localizedcontent):
    """Fetch localized content."""
    # _LOGGER.debug(f"[get_localized] {language} {localizedcontent}")
    for lang in localizedcontent:
        if language == lang.get("locale"):
            return lang
    return localizedcontent[0]


def clean_ipv6(data):
    """Clean ipv6 addresses from  the list."""
    # _LOGGER.debug("[clean_ipv6] " + str(data))
    if isinstance(data, list):
        for idx, item in enumerate(data):
            if "ipType" in item and "ipAddress" in item:
                if item["ipType"] == "IPv6":
                    _LOGGER.debug(f"[utils|clean_ipv6] IPv6 address removed: {item}")
                    del data[idx]
            else:
                data[idx] = clean_ipv6(data[idx])
    else:
        for property in data:
            if isinstance(data.get(property), bool | str):
                data[property] = data.get(property)
            else:
                if isinstance(data.get(property), list):
                    if len(data[property]) == 0:
                        data[property] = []
                    else:
                        data[property] = clean_ipv6(data.get(property))
                else:
                    data[property] = clean_ipv6(data.get(property))
    return data
