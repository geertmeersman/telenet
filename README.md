<img src="https://github.com/geertmeersman/telenet/raw/main/images/brand/logo.png"
     alt="Telenet"
     align="right"
     style="width: 200px;margin-right: 10px;" />

# Telenet for Home Assistant

A Home Assistant integration allowing to monitor your mobile, internet, dtv and telephone usage

### Features

- 🌐 Internet sensors
- 📱 Mobile sensors
- 📺 DTV sensors
- 📞 Telephone sensors

---

<!-- [START BADGES] -->
<!-- Please keep comment here to allow auto update -->

[![MIT License](https://img.shields.io/github/license/geertmeersman/telenet?style=for-the-badge)](https://github.com/geertmeersman/telenet/blob/master/LICENSE)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![maintainer](https://img.shields.io/badge/maintainer-Geert%20Meersman-green?style=for-the-badge&logo=github)](https://github.com/geertmeersman)
[![buyme_coffee](https://img.shields.io/badge/Buy%20me%20a%20Duvel-donate-yellow?style=for-the-badge&logo=buymeacoffee)](https://www.buymeacoffee.com/geertmeersman)

[![GitHub issues](https://img.shields.io/github/issues/geertmeersman/telenet)](https://github.com/geertmeersman/telenet/issues)
[![Average time to resolve an issue](http://isitmaintained.com/badge/resolution/geertmeersman/telenet.svg)](http://isitmaintained.com/project/geertmeersman/telenet)
[![Percentage of issues still open](http://isitmaintained.com/badge/open/geertmeersman/telenet.svg)](http://isitmaintained.com/project/geertmeersman/telenet)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen.svg)](https://github.com/geertmeersman/telenet/pulls)

[![Hacs and Hassfest validation](https://github.com/geertmeersman/telenet/actions/workflows/validate.yml/badge.svg)](https://github.com/geertmeersman/telenet/actions/workflows/validate.yml)
[![Python](https://img.shields.io/badge/Python-FFD43B?logo=python)](https://github.com/geertmeersman/telenet/search?l=python)

[![manifest version](https://img.shields.io/github/manifest-json/v/geertmeersman/telenet/master?filename=custom_components%2Ftelenet%2Fmanifest.json)](https://github.com/geertmeersman/telenet)
[![github release](https://img.shields.io/github/v/release/geertmeersman/telenet?logo=github)](https://github.com/geertmeersman/telenet/releases)
[![github release date](https://img.shields.io/github/release-date/geertmeersman/telenet)](https://github.com/geertmeersman/telenet/releases)
[![github last-commit](https://img.shields.io/github/last-commit/geertmeersman/telenet)](https://github.com/geertmeersman/telenet/commits)
[![github contributors](https://img.shields.io/github/contributors/geertmeersman/telenet)](https://github.com/geertmeersman/telenet/graphs/contributors)
[![github commit activity](https://img.shields.io/github/commit-activity/y/geertmeersman/telenet?logo=github)](https://github.com/geertmeersman/telenet/commits/main)

<!-- [END BADGES] -->

## Installation

### Using [HACS](https://hacs.xyz/) (recommended)

1. Simply search for `Telenet` in HACS and install it easily.
2. Restart Home Assistant
3. Add the 'Telenet' integration via HA Settings > 'Devices and Services' > 'Integrations'
4. Provide your Telenet BE username and password

### Manual

1. Copy the `custom_components/telenet` directory of this repository as `config/custom_components/telenet` in your Home Assistant instalation.
2. Restart Home Assistant
3. Add the 'Telenet' integration via HA Settings > 'Devices and Services' > 'Integrations'
4. Provide your Telenet BE username and password

This integration will set up the following platforms.

| Platform  | Description                                      |
| --------- | ------------------------------------------------ |
| `telenet` | Home Assistant component for Telenet BE services |

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

## Troubleshooting

1. You can enable logging for this integration specifically and share your logs, so I can have a deep dive investigation. To enable logging, update your `configuration.yaml` like this, we can get more information in Configuration -> Logs page

```
logger:
  default: warning
  logs:
    custom_components.telenet: debug
```

## Configuration tip

You can exclude some sensors as they contain quite some information, like e.g.

```
recorder:
  exclude:
    entity_globs:
      - sensor.telenet_*_internet_daily_usage
      - sensor.telenet_*_internet_usage
      - sensor.telenet_*_internet_network
      - sensor.telenet_*_internet_wifi
```

## Lovelace examples

### Internet info and peak/off-peak usage Apex graph

![Internet peak off-peak](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/lovelace_peak_offpeak.png)

<details><summary>Show markdown code</summary>

**Replace &lt;identifier&gt; by your Telenet identifier and &lt;customer_id&gt; by your Telenet account ID**

```
type: vertical-stack
cards:
  - type: markdown
    content: >-
      ## <img src="https://brands.home-assistant.io/telenet/icon.png"
      width="20"/>&nbsp;&nbsp;Je Internet

      ###
      **{{state_attr('sensor.telenet_<identifier>_internet_usage','total_usage')}}**
      verbruikt tijdens de huidige periode


      ###
      **{{state_attr('sensor.telenet_<identifier>_internet_usage','used_percentage')}}**%
      :
      {{state_attr('sensor.telenet_<identifier>_internet_usage','total_usage')}}
      van de
      {{state_attr('sensor.telenet_<identifier>_internet_usage','allocated_usage')}}


      Nog
      **{{state_attr('sensor.telenet_<identifier>_internet_usage','days_until')}}**
      dag(en) tot nieuwe periode

      Periode:
      {{state_attr('sensor.telenet_<identifier>_internet_usage','start_date')}}
      -
      {{state_attr('sensor.telenet_<identifier>_internet_usage','end_date')}}

      Wi-Free verbruik:
      *{{state_attr('sensor.telenet_<identifier>_internet_usage','wifree_usage')}}*

      Laatste update:
      *{{state_attr('sensor.telenet_<identifier>_internet_usage','last_update')
      | as_timestamp | timestamp_custom("%d-%m-%Y %H:%M")}}*
  - type: custom:apexcharts-card
    graph_span: 20d
    span:
      start: hour
      offset: '-20d'
    stacked: true
    header:
      standard_format: false
      show: true
      show_states: false
      title: Verbruik piek en daluren
    now:
      show: true
    series:
      - entity: sensor.telenet_<identifier>_internet_daily_usage
        name: Piekuren
        type: column
        color: A6D9D9
        float_precision: 2
        data_generator: |
          return entity.attributes.daily_date.map((day, index) => {
            return [new Date(day), entity.attributes.daily_peak[index]];
          });
      - entity: sensor.telenet_<identifier>_internet_daily_usage
        name: Daluren
        type: column
        color: 1A9AAA
        float_precision: 2
        data_generator: |
          return entity.attributes.daily_date.map((day, index) => {
            return [new Date(day), entity.attributes.daily_off_peak[index]];
          });
  - type: horizontal-stack
    cards:
      - type: entity
        name: Totaal P+D
        attribute: total_usage_with_offpeak
        entity: sensor.telenet_<identifier>_internet_usage
        icon: mdi:sigma
        unit: GB
      - type: entity
        name: Piekuren
        attribute: peak_usage
        entity: sensor.telenet_<identifier>_internet_usage
        icon: mdi:arrow-up-bold
        unit: GB
      - type: entity
        name: Daluren
        attribute: offpeak_usage
        entity: sensor.telenet_<identifier>_internet_usage
        icon: mdi:arrow-down-bold
        unit: GB

```

</details>

### Auto entities for costs

![Auto entities Costs](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/auto_entities_costs.png)

<details><summary>Show markdown code</summary>

```
type: custom:auto-entities
card:
  type: entities
  title: Telenet kosten
filter:
  include:
    - entity_id: sensor.telenet*
      attributes:
        icon: mdi:currency-eur

```

</details>

### Network & Wifi info

![Network Markdown](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/network_markdown.png)

<details><summary>Show markdown code</summary>

**Replace &lt;identifier&gt; by your Telenet identifier and &lt;customer_id&gt; by your Telenet account ID**

```
type: markdown
content: >
  ## <img
  src="https://github.com/geertmeersman/telenet/blob/main/images/brand/icon.png?raw=true"
  width="25"/>&nbsp;&nbsp;Telenet <identifier>

  ## <img src="https://github.com/geertmeersman/telenet/blob/main/images/brand/icon.png?raw=true" width="25"/>&nbsp;&nbsp;Telenet <identifier>
  ## Modem info
  | | |
  |----:|----:|
  |**Type**|{{state_attr("sensor.telenet_<customer_id>_<identifier>_internet_network","modemType")}}|
  |**Model**|{{state_attr("sensor.telenet_<customer_id>_<identifier>_internet_network","model")}}|
  |**Last seen**|{{state_attr("sensor.telenet_<customer_id>_<identifier>_internet_network","lastSeen")}}|
  |**Last seen light**|{{state_attr("sensor.telenet_<customer_id>_<identifier>_internet_network","lastSeenLight")}}|
  |**Public IP Adress**|{{state_attr("sensor.telenet_<customer_id>_<identifier>_internet_network","ipAddressInfos")[0].ipAddress}}|

  ## Network clients
  |Name|IP|Interface|Vendor
  |----:|----:|----:|----:|{% for item in state_attr("sensor.telenet_<customer_id>_<identifier>_internet_network","clients") %}
  {%if "name" in item %}{{item["name"]}}{% else %}|{%-endif %}|{%for ip in item["ipAddressInfos"] %}{%if ip["ipType"] == "IPv4" %}{{ip["ipAddress"]}}{%-endif %}
  {%-endfor %}|{{item["connectedInterface"]}}|{{item["vendor"]}}{%-endfor %}

  ## Wifi Settings
  |||
  |----:|----:|
  |**Wireless enabled**|{{state_attr("sensor.telenet_<customer_id>_<identifier>_internet_wifi","wirelessEnabled")}}|
  |**HomeSpot enabled**|{{state_attr("sensor.telenet_<customer_id>_<identifier>_internet_wifi","homeSpotEnabled")}}|
  |**Wps enabled**|{{state_attr("sensor.telenet_<customer_id>_<identifier>_internet_wifi","wifiWpsEnabled")}}|
```

</details>

## Sensors logic

The integration creates for each subscription linked to your account the following sensors

Interact with the sensors flow [here](https://github.com/geertmeersman/telenet/blob/main/documentation/SENSORS_LOGIC.md)

![Sensors flow](https://github.com/geertmeersman/telenet/raw/main/images/documentation/sensor_logic.png)

## Screenshots

| Description                                | Screenshot                                                                                                                             |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| Config flow init                           | ![Config flow init](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/config_flow.png)                              |
| Config flow options                        | ![Config flow options](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/config_flow_options.png)                   |
| Config flow language update                | ![Config flow language update](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/config_flow_language.png)          |
| Config flow password update                | ![Config flow password update](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/config_flow_password.png)          |
| Config flow success                        | ![Config flow success](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/config_flow_success.png)                   |
| Config flow multi account setup            | ![Config flow multi account setup](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/config_flow_multi_account.png) |
| One for 2 sensors                          | ![One for 2 sensors](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/onefor2.png)                                 |
| All-Internet & Usage Based Pricing sensors | ![All-Internet & Usage Based Pricing](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/all_internet_pvv.png)       |
| Internet sensors                           | ![Internet sensors](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/internet_sensors.png)                         |
| Internet sensor                            | ![Internet sensor](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/internet_sensor.png)                           |
| Plan sensor                                | ![Plan sensor](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/plan_sensor.png)                                   |
| ONE for 2 bundle sensors                   | ![ONE for 2 bundle sensors](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/bundle_sensors.png)                   |
| DTV sensors                                | ![DTV sensors](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/dtv_sensors.png)                                   |
