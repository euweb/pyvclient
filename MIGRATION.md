# Migration from Homie 4 to Home Assistant MQTT Discovery

This document describes the changes made when migrating from Homie 4 to Home Assistant MQTT Discovery.

## Overview

The application has been completely refactored to use Home Assistant's native MQTT Discovery protocol instead of the Homie IoT convention. This provides better integration with Home Assistant and eliminates the need for additional bridge software.

## What Changed

### Removed

- **Homie4 dependency** - Replaced with paho-mqtt
- **homie/** directory - All Homie-specific classes and properties
- Homie topic structure (`homie/<device>/<node>/<property>`)
- Homie metadata topics (`$properties`, `$datatype`, `$settable`, etc.)

### Added

- **Home Assistant MQTT Discovery** support
  - `ha/ha_mqtt_discovery.py` - MQTT client and discovery publishing
  - `ha/ha_entities.py` - Entity definitions (Sensor, Number, Select, etc.)
  - `ha/ha_viessmann_device.py` - Main device class
- **Simplified topic structure** - `viessmann/<property>` and `viessmann/<property>/set`
- **Repeating timer** utility - `utils/repeating_timer.py`
- **Comprehensive documentation** - MQTT topics and entity mapping

### Modified

- **pyvclient.py** - Refactored to use ViessmannDevice instead of DeviceViessmannHeater
- **requirements.txt** - Updated dependencies
- **setup.cfg** - Updated install_requires
- **README.rst** - Updated documentation
- **logging.yaml** - Replaced homie logger with paho logger

## Topic Structure Comparison

### Old (Homie 4)

```
homie/viessmann/$homie           → "4.0.0"
homie/viessmann/$name            → "Viessmann Heizung"
homie/viessmann/$state           → "ready"
homie/viessmann/$nodes           → "generic"
homie/viessmann/generic/$name    → "Generic"
homie/viessmann/generic/$type    → "generic"
homie/viessmann/generic/$properties → "tempa,tempwwist,..."
homie/viessmann/generic/tempa    → "5.2"
homie/viessmann/generic/tempa/$name → "TempA"
homie/viessmann/generic/tempa/$datatype → "float"
homie/viessmann/generic/tempa/$unit → "°C"
homie/viessmann/generic/tempa/$settable → "false"
```

### New (Home Assistant)

```
homeassistant/sensor/tempa/config → {JSON discovery config}
viessmann/tempa                   → "5.2"
viessmann/status                  → "online"
```

## Entity Mapping

### Homie Properties → HA Entities

| vcontrold Type | Homie Property | HA Entity Type | Example |
|----------------|----------------|----------------|---------|
| short (readonly) | Property_Temperature | Sensor | TempA, TempWWist |
| short (settable) | Property_Temperature | Number | TempWWSoll |
| int/uint (readonly) | Property_Integer | Sensor | BrennerStarts, BrennerStunden |
| int/uint (settable) | Property_Integer | Number | SetpointValue |
| enum (readonly) | Property_Enum | Sensor | Status display |
| enum (settable) | Property_Enum | Select | BetriebArtM1 |
| systime | Property_String | Sensor | SystemTime |

### Entity Features

**Sensors** (readonly):
- Automatic device class detection (temperature, etc.)
- State class (measurement, total_increasing)
- Units of measurement
- Diagnostic category for counters

**Numbers** (settable):
- Min/max ranges
- Step size
- Slider or box mode
- Command topic subscription

**Selects** (settable enums):
- Predefined options from vcontrold
- Command topic subscription

## Configuration Changes

### config.yaml

No structural changes - properties are defined the same way:

```yaml
Properties:
  TempA:
    readonly: true
    interval: 300
```

Optional new settings:

```yaml
MQTT_SETTINGS:
  MQTT_CLIENT_ID: viessmann_vcontrold  # Optional
  MQTT_USERNAME: user                   # Optional
  MQTT_PASSWORD: pass                   # Optional
```

## Migration Steps

### 1. Update Dependencies

```bash
pip install paho-mqtt
pip uninstall Homie4
```

Or reinstall from requirements:

```bash
pip install -r requirements.txt
```

### 2. Remove Old Data (Optional)

If you were using Homie with retained messages, clean up old topics:

```bash
# Connect to MQTT broker and remove old homie topics
mosquitto_pub -t 'homie/viessmann' -n -r -d
# Repeat for all homie subtopics or use MQTT Explorer
```

### 3. Restart Application

```bash
pyvclient --log src/conf/logging.yaml src/conf/config.yaml
```

### 4. Verify in Home Assistant

1. Go to Settings → Devices & Services → MQTT
2. Look for "Viessmann Heating" device
3. Check that all entities appear correctly
4. Verify values are updating
5. Test settable entities (if any)

## Benefits of Migration

### Advantages

1. **Native Integration** - No additional bridges or custom components
2. **Single Device** - All entities grouped under one device
3. **Better Entity Types** - Proper number, select, and sensor entities
4. **Simpler Topics** - Flat structure without Homie metadata
5. **Auto-Discovery** - No YAML configuration needed
6. **Better Control** - Native HA controls for settable values
7. **Cleaner Code** - Removed dependency on external Homie library

### What You Lose

- **Homie Convention** - If you were using other Homie-compatible tools
- **Homie Metadata** - Self-describing topics (but HA discovery provides similar info)

## Troubleshooting

### Entities Not Appearing

1. Check MQTT connection:
   ```bash
   mosquitto_sub -v -t 'homeassistant/#'
   ```

2. Verify discovery messages are published

3. Check Home Assistant MQTT integration is enabled

4. Look for errors in pyvclient logs

### Values Not Updating

1. Check vcontrold connection
2. Verify property intervals in config.yaml
3. Check MQTT broker logs
4. Review pyvclient debug logs

### Commands Not Working

1. Verify entity is marked as settable in config
2. Check command topic subscription in logs
3. Test vcontrold set command manually
4. Review error logs

## Rollback (if needed)

If you need to revert to Homie 4:

```bash
git checkout <previous-commit>
pip install Homie4
pip uninstall paho-mqtt
```

## Code Architecture

### Old Structure

```
pyvclient/
  homie/
    device_viesmann_heater.py    (Homie device class)
    property_*.py                 (Homie property types)
```

### New Structure

```
pyvclient/
  ha/
    ha_mqtt_discovery.py         (MQTT client)
    ha_entities.py               (HA entity definitions)
    ha_viessmann_device.py       (Main device class)
  utils/
    repeating_timer.py           (Timer utility)
```

## Further Information

- [Home Assistant MQTT Discovery](https://www.home-assistant.io/integrations/mqtt/#mqtt-discovery)
- [MQTT Topics Documentation](MQTT_TOPICS.md)
- [vcontrold Wiki](https://github.com/openv/openv/wiki/vcontrold)
