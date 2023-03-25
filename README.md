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

## Sensors logic
The integration creates for each subscription linked to your account the following sensors
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
    planInfo --> PlanInfoSensor{{Plan InfoSensor}}
    Mobile --> MobileInfoSensor_outOfBundle{{Mobile InfoSensor outOfBundle}}
    Mobile --> MobileInfoSensor_DataUsage{{Mobile InfoSensor data usage}}
    Mobile --> MobileInfoSensor_DataUsage{{Mobile InfoSensor data usage}}
    Mobile --> MobileInfoSensor_sms{{Mobile InfoSensor sms usage}}
    Mobile --> MobileInfoSensor_voice{{Mobile InfoSensor voice usage}}
    Mobile --> MobileInfoSensor_outOfBundle{{Mobile InfoSensor outOfBundle}}
```
