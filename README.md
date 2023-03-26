<!-- [START BADGES] -->
<!-- [END BADGES] -->
<img src="https://github.com/geertmeersman/telenet/raw/main/images/brand/logo.png"
     alt="Telenet"
     align="right" 
     style="width: 200px;margin-right: 10px;" />
# Telenet for Home Assistant

Telenet custom component for Home Assistant, allowing to monitor your mobile and internet usage

## Installation
- [HACS](https://hacs.xyz/): search for Telenet in HACS integrations and download it
- Restart Home Assistant
- Add the 'Telenet' integration via HA Settings > 'Devices and Services' > 'Integrations'
- Provide your Telenet BE username and password

## Screenshots
|Description|Screenshot
|-|-
Config flow|![Config flow](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/config_flow.png)
All-Internet & Usage Based Pricing sensors|![All-Internet & Usage Based Pricing](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/all_internet_pvv.png)
Internet sensors|![Internet sensors](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/internet_sensors.png)
Internet sensor|![Internet sensor](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/internet_sensor.png)
Plan sensor|![Plan sensor](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/plan_sensor.png)
ONE for 2 bundle sensors|![ONE for 2 bundle sensors](https://github.com/geertmeersman/telenet/raw/main/images/screenshots/bundle_sensors.png)

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

The following flowchart is rendered using mermaid. If you see code instead, you can always see the flowchart [here](https://github.com/geertmeersman/telenet).
```mermaid
flowchart LR
    planInfo(planInfo)
    productUsage(productUsage)
    productDailyUsage(productDailyUsage)
    productSubscriptions{productSubscriptions}
    productDetails(productDetails)
    mobileBundleUsage(mobileBundleUsage)
    mobileUsage(mobileUsage)
    Mobile
    Internet
    login --> planInfo
    login --> productSubscriptions
    productSubscriptions --> |INTERNET| Internet
    productSubscriptions --> |MOBILE| Mobile
    billCycles(billCycles)
    billCycles -.-> Internet
    billCycles -.-> Mobile
    productUsage -.-> Internet
    productDailyUsage -.-> Internet
    productDetails -.-> Internet
    mobileBundleUsage -.-> |if bundle| Mobile
    mobileUsage -.-> |if not bundle| Mobile
    planInfo --> |if bundle| Mobile
    Internet --> InternetSensor{{InternetSensor internet}}
    Internet --> InternetSensorDU{{InternetSensor daily usages}}
    Internet --> InternetSensorModem{{InternetSensor modem}}
    Internet --> InternetSensorNetwork{{InternetSensor network}}
    Internet --> InternetSensorWifi{{InternetSensor wifi}}
    planInfo --> PlanInfoSensor{{Plan InfoSensor}}
    Mobile --> MobileInfoSensor_outOfBundle{{Mobile InfoSensor outOfBundle}}
    Mobile --> MobileInfoSensor_DataUsage{{Mobile InfoSensor data usage}}
    Mobile --> MobileInfoSensor_DataUsage{{Mobile InfoSensor data usage}}
    Mobile --> MobileInfoSensor_sms{{Mobile InfoSensor sms usage}}
    Mobile --> MobileInfoSensor_voice{{Mobile InfoSensor voice usage}}
    Mobile --> MobileInfoSensor_outOfBundle{{Mobile InfoSensor outOfBundle}}
```

