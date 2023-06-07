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

[![discord](https://img.shields.io/discord/1094193683332612116?style=for-the-badge&logo=discord&label=Reach%20out%20on%20DISCORD)](https://discord.gg/jPHKexJ3ad)

[![maintainer](https://img.shields.io/badge/maintainer-Geert%20Meersman-green?style=for-the-badge&logo=github)](https://github.com/geertmeersman)
[![buyme_coffee](https://img.shields.io/badge/Buy%20me%20a%20Duvel-donate-yellow?style=for-the-badge&logo=buymeacoffee)](https://www.buymeacoffee.com/geertmeersman)

[![MIT License](https://img.shields.io/github/license/geertmeersman/telenet?style=flat-square)](https://github.com/geertmeersman/telenet/blob/master/LICENSE)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=flat-square)](https://github.com/hacs/integration)

[![Open your Home Assistant instance and open the repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg?style=flat-square)](https://my.home-assistant.io/redirect/hacs_repository/?owner=geertmeersman&repository=telenet&category=integration)

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

## Table of Contents

- [Telenet for Home Assistant](#telenet-for-home-assistant)
  - [Features](#features)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
    - [Using HACS (recommended)](#using-hacs-recommended)
    - [Manual](#manual)
  - [Contributions are welcome!](#contributions-are-welcome)
  - [Troubleshooting](#troubleshooting)
    - [ENABLING DEBUG LOGGING](#enabling-debug-logging)
    - [DISABLE DEBUG LOGGING AND DOWNLOAD LOGS](#disable-debug-logging-and-download-logs)
  - [Lovelace examples](#lovelace-examples)
    - [Internet info and peak/off-peak usage Apex graph](#internet-info-and-peakoff-peak-usage-apex-graph)
    - [Auto entities for costs](#auto-entities-for-costs)
    - [Network \& Wifi info](#network--wifi-info)
  - [Sensors logic](#sensors-logic)
  - [Screenshots](#screenshots)
  - [Code origin](#code-origin)

## Installation

### Using [HACS](https://hacs.xyz/) (recommended)

**Click on this button:**

[![Open your Home Assistant instance and open the repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg?style=flat-square)](https://my.home-assistant.io/redirect/hacs_repository/?owner=geertmeersman&repository=telenet&category=integration)

**or follow these steps:**

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

### ENABLING DEBUG LOGGING

To enable debug logging, go to Settings -> Devices & Services and then click the triple dots for the Telenet integration and click Enable Debug Logging.

![enable-debug-logging](https://raw.githubusercontent.com/geertmeersman/telenet/main/images/screenshots/enable-debug-logging.gif)

### DISABLE DEBUG LOGGING AND DOWNLOAD LOGS

Once you enable debug logging, you ideally need to make the error happen. Run your automation, change up your device or whatever was giving you an error and then come back and disable Debug Logging. Disabling debug logging is the same as enabling, but now you will see Disable Debug Logging. After you disable debug logging, it will automatically prompt you to download your log file. Please provide this logfile.

![disable-debug-logging](https://raw.githubusercontent.com/geertmeersman/telenet/main/images/screenshots/disable-debug-logging.gif)

The below lovelace examples, are mostly made for the recent Telenet IT platform.

If your interface still has this kind of layout, you are on the V1 API Version

![API V1](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/api_v1.png)

3. If none of the above helped, you can always create an issue on Github or reach out on [Discord](https://discord.gg/jPHKexJ3ad)

## Lovelace examples

### Internet info and peak/off-peak usage Apex graph

![Internet peak off-peak](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/lovelace_peak_offpeak.png)

<details><summary>Show markdown code</summary>

**Replace &lt;identifier&gt; by your Telenet identifier**

(Only at 2 places)

You can find your Telenet identifier by going to "/developer-tools/state" and filter on internet_usage

Attention: this example uses the following HACS Lovelace cards (so you will need to install these§ if you are planning to you the examples):

- https://github.com/iantrich/config-template-card
- https://github.com/RomRider/apexcharts-card
- https://github.com/custom-cards/dual-gauge-card

```
type: vertical-stack
cards:
  - type: custom:config-template-card
    variables:
      internet:
        identifier: <identifier>
    entities:
      - ${"sensor.telenet_"+internet.identifier+"_internet_usage"}
    card:
      type: vertical-stack
      cards:
        - type: markdown
          content: >-
            {% set identifier = "<identifier>"%} {% set internet_usage =
            "sensor.telenet_"+identifier+"_internet_usage"%}

            ## <img src="https://brands.home-assistant.io/telenet/icon.png"
            width="20"/>&nbsp;&nbsp;Je Internet {{identifier}}

            #### Reeds **{{state_attr(internet_usage,'used_percentage')}}%**
            verbruikt tijdens de huidige periode

            |||

            |----:|----:|

            | Periode | **{{state_attr(internet_usage,'start_date')|
            as_timestamp | timestamp_custom("%d/%m")}} -
            {{state_attr(internet_usage,'end_date')| as_timestamp |
            timestamp_custom("%d/%m")}}**

            | Verbruikt:|**{{state_attr(internet_usage,'total_usage')}}**

            |Totaal
            toegekend:|**{{state_attr(internet_usage,'allocated_usage')}}**

            |Wi-Free verbruik:| *{{state_attr(internet_usage,'wifree_usage')}}*

            |Laatste update: |*{{state_attr(internet_usage,'last_update') |
            as_timestamp | timestamp_custom("%d-%m-%Y %H:%M")}}*


            Nog **{{state_attr(internet_usage,'days_until')}}** dag(en) tot
            nieuwe periode
        - type: custom:apexcharts-card
          apex_config:
            tooltip:
              enabled: true
              followCursor: true
              x:
                show: false
                format: dd MMMM yyyy
              'y':
                show: true
          span:
            end: day
            offset: >-
              ${'+'+states['sensor.telenet_'+internet.identifier+'_internet_usage'].attributes.days_until+'d'}
          stacked: true
          graph_span: 1month
          header:
            standard_format: false
            show: true
            show_states: false
            title: ${'Verbruik piek en daluren huidige periode '+internet.identifier}
          now:
            show: true
            label: Vandaag
          series:
            - entity: ${'sensor.telenet_'+internet.identifier+'_internet_daily_usage'}
              name: Daluren
              type: column
              color: 1A9AAA
              show:
                legend_value: false
              float_precision: 2
              data_generator: |
                return entity.attributes.daily_date.map((day, index) => {
                  return [new Date(day), entity.attributes.daily_off_peak[index]];
                });
            - entity: ${'sensor.telenet_'+internet.identifier+'_internet_daily_usage'}
              name: Piekuren
              type: column
              color: A6D9D9
              show:
                legend_value: false
              float_precision: 2
              data_generator: |
                return entity.attributes.daily_date.map((day, index) => {
                  return [new Date(day), entity.attributes.daily_peak[index]];
                });
        - type: horizontal-stack
          cards:
            - type: entity
              name: Totaal P+D
              attribute: total_usage_with_offpeak
              entity: ${'sensor.telenet_'+internet.identifier+'_internet_usage'}
              icon: mdi:sigma
              unit: GB
            - type: entity
              name: Piekuren
              attribute: peak_usage
              entity: ${'sensor.telenet_'+internet.identifier+'_internet_usage'}
              unit: GB
              icon: mdi:arrow-up-bold
            - type: entity
              name: Daluren
              attribute: offpeak_usage
              entity: ${'sensor.telenet_'+internet.identifier+'_internet_usage'}
              unit: GB
              icon: mdi:arrow-down-bold
        - type: custom:dual-gauge-card
          title: false
          min: 0
          max: 100
          shadeInner: true
          cardwidth: 350
          outer:
            entity: ${'sensor.telenet_'+internet.identifier+'_internet_usage'}
            label: used
            min: 0
            max: 100
            unit: '%'
            colors:
              - color: var(--label-badge-green)
                value: 0
              - color: var(--label-badge-yellow)
                value: 60
              - color: var(--label-badge-red)
                value: 80
          inner:
            entity: ${'sensor.telenet_'+internet.identifier+'_internet_usage'}
            label: period
            attribute: period_used_percentage
            min: 0
            max: 100
            unit: '%'


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

**Replace &lt;identifier&gt; by your Telenet identifier**

```
type: markdown
content: >
  ## <img
  src="https://github.com/geertmeersman/telenet/blob/main/images/brand/icon.png?raw=true"
  width="25"/>&nbsp;&nbsp;Telenet <identifier>

  ## Modem info

  {% set topology = states.sensor.telenet_<identifier>_internet_network.attributes %}

  |||

  |----:|----:|

  |**Type**|{{topology.modemType|default}}|

  |**Model**|{{topology.model|default}}|

  |**Last seen**|{{topology.lastSeen|default}}|

  |**Last seen light**|{{topology.lastSeenLight|default}}|

  |**Public IP Adress**|{{topology.ipAddressInfos[0].ipAddress|default}}|


  ## Network clients

  ### {{topology.modemType|default}} {{topology.deviceName|default}} ({{topology.model}})

  |Client|IP|Interface|Vendor

  |----:|----:|----:|----:|
  {% for item in topology.clients %}
  {{item["name"]|default("|")}}|{%for ip in item["ipAddressInfos"] %}{%if ip["ipType"] == "IPv4" %}{{ip["ipAddress"]}}{%-endif %}
  {%-endfor %}|{{item["connectedInterface"]}}|{%if "vendor" in item %}{{item["vendor"]}}{% else %}|
  {%-endif %}
  {%endfor %}

  {%- for child in topology.children %}

  ---

  ### {{child.type|default}} {{child.deviceName|default}} ({{topology.model}})

  |Client|IP|Interface|Vendor

  |----:|----:|----:|----:|
  {% for item in child.clients %}
  {{item["name"]|default("|")}}|{%for ip in item["ipAddressInfos"] %}{%if ip["ipType"] == "IPv4" %}{{ip["ipAddress"]}}{%-endif %}
  {%-endfor %}|{{item["connectedInterface"]}}|{%if "vendor" in item %}{{item["vendor"]}}{% else %}|
  {%-endif %}
  {%endfor %}
  {%-endfor %}

  ## Wifi Settings

  |||

  |----:|----:|

  |**Wireless enabled**|{{state_attr("sensor.telenet_<identifier>_internet_wifi","wirelessEnabled")}}|

  |**HomeSpot enabled**|{{state_attr("sensor.telenet_<identifier>_internet_wifi","homeSpotEnabled")}}|

  |**Wps enabled**|{{state_attr("sensor.telenet_<identifier>_internet_wifi","wifiWpsEnabled")}}|


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

## Code origin

The code of this Home Assistant integration has been written by analysing the calls made by the Telenet website and by contributing to the integration made by [@myTselection](https://github.com/myTselection). It made me curious on how to build an integration from scratch, using the recommendations here https://developers.home-assistant.io/docs/creating_component_index/. I tried to pull out of the website as much information as possible.

I have no link with Telenet Group N.V.
