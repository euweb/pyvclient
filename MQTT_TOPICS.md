# Home Assistant MQTT Topics

This document describes the MQTT topic structure used by pyvclient for Home Assistant integration.

## Device Information

All entities belong to a single Home Assistant device:

- **Device ID**: `viessmann_vcontrold`
- **Manufacturer**: Viessmann
- **Model**: via vcontrold
- **Name**: Viessmann Heating

## Topic Structure

### Discovery Topics

Discovery configurations are published to:
```
homeassistant/<domain>/<object_id>/config
```

Examples:
- `homeassistant/sensor/tempa/config` - Outside temperature sensor
- `homeassistant/number/betriebartm1/config` - Operating mode (settable)
- `homeassistant/sensor/brennerstarts/config` - Burner starts counter

### State Topics

State values are published to:
```
viessmann/<property_name>
```

Examples:
- `viessmann/tempa` - Outside temperature value
- `viessmann/tempwwist` - Hot water temperature
- `viessmann/brennerstarts` - Number of burner starts
- `viessmann/systemtime` - System time

### Command Topics

For settable entities, commands are received on:
```
viessmann/<property_name>/set
```

Examples:
- `viessmann/betriebartm1/set` - Set operating mode
- `viessmann/tempwwsoll/set` - Set hot water target temperature

### Availability Topic

Device availability (online/offline status):
```
viessmann/status
```

Payloads:
- `online` - Device is connected and operational
- `offline` - Device is disconnected (Last Will and Testament)

## Entity Types

### Sensors (Read-only)

Sensors publish measurements and diagnostic data:

**Temperature Sensors**:
- `tempa` - Outside temperature (°C)
- `tempwwist` - Hot water actual temperature (°C)
- `tempkol` - Collector temperature (°C)

**Counters**:
- `solarstunden` - Solar operation hours
- `brennerstarts` - Burner start count
- `brennerstunden1` - Burner operating hours

**Other**:
- `solarleistung` - Solar power
- `systemtime` - System time

### Numbers (Settable)

Numbers allow setting numeric values with min/max ranges:

Examples:
- Target temperatures
- Heating curve parameters
- Time settings

### Selects (Settable Enums)

Select entities for choosing from predefined options:

**Operating Modes** (BetriebArtM1):
- Options depend on vcontrold configuration
- Typically: Off, Hot Water, Heating, Heating+HW, etc.

## Discovery Configuration Examples

### Temperature Sensor

```json
{
  "name": "TempA",
  "unique_id": "viessmann_tempa",
  "state_topic": "viessmann/tempa",
  "unit_of_measurement": "°C",
  "device_class": "temperature",
  "state_class": "measurement",
  "availability_topic": "viessmann/status",
  "payload_available": "online",
  "payload_not_available": "offline",
  "device": {
    "identifiers": ["viessmann_vcontrold"],
    "manufacturer": "Viessmann",
    "model": "via vcontrold",
    "name": "Viessmann Heating"
  }
}
```

### Counter Sensor

```json
{
  "name": "BrennerStarts",
  "unique_id": "viessmann_brennerstarts",
  "state_topic": "viessmann/brennerstarts",
  "state_class": "total_increasing",
  "entity_category": "diagnostic",
  "icon": "mdi:counter",
  "availability_topic": "viessmann/status",
  "device": { ... }
}
```

### Settable Number

```json
{
  "name": "TempWWSoll",
  "unique_id": "viessmann_tempwwsoll",
  "state_topic": "viessmann/tempwwsoll",
  "command_topic": "viessmann/tempwwsoll/set",
  "unit_of_measurement": "°C",
  "min": 10,
  "max": 60,
  "step": 1,
  "mode": "slider",
  "availability_topic": "viessmann/status",
  "device": { ... }
}
```

### Select (Operating Mode)

```json
{
  "name": "BetriebArtM1",
  "unique_id": "viessmann_betriebartm1",
  "state_topic": "viessmann/betriebartm1",
  "command_topic": "viessmann/betriebartm1/set",
  "options": ["WW", "H+WW", "NORM", "RED", "OFF"],
  "icon": "mdi:cog",
  "availability_topic": "viessmann/status",
  "device": { ... }
}
```

## Message Flow

### Startup Sequence

1. Application connects to MQTT broker
2. Publishes `online` to `viessmann/status`
3. Publishes discovery configs for all entities
4. Subscribes to all `*/set` topics for settable entities
5. Starts periodic update timers

### Periodic Updates

For each configured property at its specified interval:

1. Application calls vcontrold via `vclient`
2. Parses the response
3. Publishes value to state topic

### Command Handling

When Home Assistant sends a command:

1. Application receives message on `*/set` topic
2. Validates the value
3. Executes `vclient` set command
4. Publishes updated state on success

### Shutdown

1. Application publishes `offline` to `viessmann/status`
2. Disconnects from MQTT broker
3. All entities become unavailable in Home Assistant

## Retained Messages

The following messages are retained (`retain=True`):

- All discovery configurations
- Availability status (`viessmann/status`)

State values are typically not retained to reflect real-time data.

## Quality of Service (QoS)

- Discovery messages: QoS 1
- State updates: QoS 1
- Command messages: QoS 1
- Availability: QoS 1

This ensures reliable delivery of important messages.
