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
[![Open your Home Assistant instance and open the repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg?style=for-the-badge)](https://my.home-assistant.io/redirect/hacs_repository/?owner=geertmeersman&repository=telenet&category=integration)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![maintainer](https://img.shields.io/badge/maintainer-Geert%20Meersman-green?style=for-the-badge&logo=github)](https://github.com/geertmeersman)
[![buyme_coffee](https://img.shields.io/badge/Buy%20me%20a%20Duvel-donate-yellow?style=for-the-badge&logo=buymeacoffee)](https://www.buymeacoffee.com/geertmeersman)
[![discord](https://img.shields.io/discord/1094193683332612116?style=for-the-badge&logo=discord)](https://discord.gg/jPHKexJ3ad)

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

2. If you receive this exception in the logs:

```
No products found. Either the API is currently down or you are not migrated to the new Telenet IT system yet.
```

This might mean that your account is not migrated yet to the new Telenet IT platform. I only support the newest API, which is rolling out since beginning of 2023. So you'll need to be patient and hope Telenet migrates your account soon.

3. If none of the above helped, you can always create an issue on Github or reach out on [Discord](https://discord.gg/jPHKexJ3ad)

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

**Replace &lt;identifier&gt; by your Telenet identifier**

(Only at 2 places)

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

## Code origin

The code of this Home Assistant integration has been written by analysing the calls made by the Telenet website and by contributing to the integration made by [@myTselection](https://github.com/myTselection). It made me curious on how to build an integration from scratch, using the recommendations here https://developers.home-assistant.io/docs/creating_component_index/. I tried to pull out of the website as much information as possible.

I have no link with Telenet Group N.V.
