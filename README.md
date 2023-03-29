<!-- [START BADGES] -->
<!-- Please keep comment here to allow auto update -->

[![MIT License](https://img.shields.io/github/license/geertmeersman/telenet)](https://github.com/geertmeersman/telenet/blob/master/LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/geertmeersman/telenet)](https://github.com/geertmeersman/telenet/issues)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen.svg)](https://github.com/geertmeersman/telenet/pulls)
[![build](https://img.shields.io/github/actions/workflow/status/geertmeersman/telenet/hacs.yml?branch=main&logo=github)](https://github.com/geertmeersman/telenet/actions/workflows/hacs.yml)
[![manifest version](https://img.shields.io/github/manifest-json/v/geertmeersman/telenet/master?filename=custom_components%2Ftelenet%2Fmanifest.json)](https://github.com/geertmeersman/telenet)
[![github release](https://img.shields.io/github/v/release/geertmeersman/telenet?logo=github)](https://github.com/geertmeersman/telenet/releases)
[![github release date](https://img.shields.io/github/release-date/geertmeersman/telenet)](https://github.com/geertmeersman/telenet/releases)
[![github last-commit](https://img.shields.io/github/last-commit/geertmeersman/telenet)](https://github.com/geertmeersman/telenet/commits)
[![github contributors](https://img.shields.io/github/contributors/geertmeersman/telenet)](https://github.com/geertmeersman/telenet/graphs/contributors)
[![Python](https://img.shields.io/badge/Python-FFD43B?logo=python)](https://github.com/geertmeersman/telenet/search?l=python)

<!-- [END BADGES] -->

<img src="https://github.com/geertmeersman/telenet/raw/main/images/brand/logo.png"
     alt="Telenet"
     align="right"
     style="width: 200px;margin-right: 10px;" />

# Telenet for Home Assistant

Telenet custom component for Home Assistant, allowing to monitor your mobile, internet and dtv usage

## Installation

- [HACS](https://hacs.xyz/): search for Telenet in HACS integrations and download it
- Restart Home Assistant
- Add the 'Telenet' integration via HA Settings > 'Devices and Services' > 'Integrations'
- Provide your Telenet BE username and password

## Screenshots

| Description                                | Screenshot                                                                                                                       |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| Config flow                                | ![Config flow](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/config_flow.png)                             |
| All-Internet & Usage Based Pricing sensors | ![All-Internet & Usage Based Pricing](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/all_internet_pvv.png) |
| Internet sensors                           | ![Internet sensors](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/internet_sensors.png)                   |
| Internet sensor                            | ![Internet sensor](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/internet_sensor.png)                     |
| Plan sensor                                | ![Plan sensor](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/plan_sensor.png)                             |
| ONE for 2 bundle sensors                   | ![ONE for 2 bundle sensors](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/bundle_sensors.png)             |

## Lovelace examples

### Network & Wifi info

![Network Markdown](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/network_markdown.png)

<details><summary>Show markdown code</summary>

**Replace &lt;identifier&gt; by your Telenet identifier**

```
type: markdown
content: >
  ## <img
  src="https://github.com/geertmeersman/telenet/blob/main/images/brand/icon.png?raw=true"
  width="25"/>&nbsp;&nbsp;Telenet <identifier>

  ## Modem info

  |||

  |----:|----:|

  |**Type**|{{state_attr("sensor.telenet_internet_<identifier>_network","modemType")}}|

  |**Model**|{{state_attr("sensor.telenet_internet_<identifier>_network","model")}}|

  |**Last
  seen**|{{state_attr("sensor.telenet_internet_<identifier>_network","lastSeen")}}|

  |**Last seen
  light**|{{state_attr("sensor.telenet_internet_<identifier>_network","lastSeenLight")}}|


  ## Network clients

  |Name|IP|Interface|Vendor

  |----:|----:|----:|----:|{% for item in
  state_attr("sensor.telenet_internet_<identifier>_network","clients") %}

  {%if "name" in item %}{{item["name"]}}{% else %}|{%-endif %}|{%for ip in
  item["ipAddressInfos"] %}{%if ip["ipType"] == "IPv4"
  %}{{ip["ipAddress"]}}{%-endif %}

  {%-endfor %}|{{item["connectedInterface"]}}|{{item["vendor"]}}{%-endfor %}


  ## Wifi Settings

  |||

  |----:|----:|

  |**Wireless
  enabled**|{{state_attr("sensor.telenet_internet_<identifier>_wifi","wirelessEnabled")}}|

  |**HomeSpot
  enabled**|{{state_attr("sensor.telenet_internet_<identifier>_wifi","homeSpotEnabled")}}|

  |**Wps
  enabled**|{{state_attr("sensor.telenet_internet_<identifier>_wifi","wifiWpsEnabled")}}|
```

</details>

## Sensors logic

The integration creates for each subscription linked to your account the following sensors

Interact with the sensors flow [here](https://github.com/geertmeersman/telenet/blob/main/documentation/SENSORS_LOGIC.md)

![Sensors flow](https://github.com/geertmeersman/telenet/raw/main/images/documentation/sensor_logic.png)
