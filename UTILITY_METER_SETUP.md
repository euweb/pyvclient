# Utility Meter Setup for Solar Power

## Overview

To display solar power similar to gas consumption (daily totals that reset at midnight), use the [Utility Meter Integration](https://www.home-assistant.io/integrations/utility_meter/) in Home Assistant.

## Prerequisites

- pyvclient sends `SolarLeistung` as cumulative total energy in Wh (Watt-hours)
- Home Assistant receives the values via MQTT as `sensor.viessmann_heating_solarleistung`
- The value is cumulative and continuously increases (e.g., 51274 Wh = total yield since commissioning)

## Configuration in Home Assistant

**Important:** There are two scenarios depending on what `SolarLeistung` provides:

### Scenario A: SolarLeistung = Instantaneous Value (e.g., 2500 W, rises/falls)
If `SolarLeistung` represents the **current power** in Watt/kW, see below (starting at "Scenario A: When SolarLeistung = Current Power").

### ✅ Scenario B: SolarLeistung = Cumulative Value (Your Case!)
`SolarLeistung` is already the **total energy** in **Wh** (Watt-hours) - cumulative count since commissioning.

**Example:** `sensor.viessmann_heating_solarleistung` = 51274 Wh (= 51.3 kWh total yield)

**Skip the Integration Sensor** and use directly:

```yaml
# configuration.yaml

# Template Sensor for Energy Dashboard (converts Wh → kWh)
template:
  - sensor:
      - name: "Solar Thermal Energy Total"
        unique_id: solar_thermal_energy_total
        unit_of_measurement: "kWh"
        device_class: energy
        state_class: total_increasing
        state: "{{ states('sensor.viessmann_heating_solarleistung') | float(0) / 1000 }}"
        availability: "{{ states('sensor.viessmann_heating_solarleistung') not in ['unavailable', 'unknown'] }}"

# Utility Meter for daily statistics
utility_meter:
  solar_energy_daily:
    source: sensor.solar_thermal_energy_total
    name: "Solar Thermal Today"
    cycle: daily
    
  solar_energy_weekly:
    source: sensor.solar_thermal_energy_total
    name: "Solar Thermal Week"
    cycle: weekly
    
  solar_energy_monthly:
    source: sensor.solar_thermal_energy_total
    name: "Solar Thermal Month"
    cycle: monthly
```

**→ Skip to Step 3 (Reload Home Assistant)**

---

### Scenario A: When SolarLeistung = Current Power (Watt/kW)

Add the following configuration to your Home Assistant `configuration.yaml`:

### 1. Sensor for Daily Solar Energy (Integration Helper)

First, create a sensor that integrates power over time (Wh/kWh):

```yaml
# configuration.yaml

sensor:
  - platform: integration
    source: sensor.solarleistung
    name: "Solar Energy Total"
    unique_id: solar_energy_total
    unit_prefix: k
    unit_time: h
    method: left

# Template Sensor for Energy Dashboard (modern syntax, converts Wh → kWh)
template:
  - sensor:
      - name: "Solar Thermal Energy Total"
        unique_id: solar_thermal_energy_total
        unit_of_measurement: "kWh"
        device_class: energy
        state_class: total_increasing
        state: "{{ states('sensor.viessmann_heating_solarleistung') | float(0) / 1000 }}"
        availability: "{{ states('sensor.viessmann_heating_solarleistung') not in ['unavailable', 'unknown'] }}"
```

**Important:** 
- The sensor name is `sensor.viessmann_heating_solarleistung` (from pyvclient via MQTT)
- Division by 1000 converts Wh → kWh (51274 Wh → 51.274 kWh)

**Parameters:**
- `source`: The sensor with current solar power (from pyvclient)
- `name`: Name of the new sensor
- `unit_prefix`: `k` for kWh (Kilo), empty for Wh
- `unit_time`: `h` for hours
- `method`: `left` (default) or `trapezoidal` for more accurate calculation

**Template Sensor for Energy Dashboard:**
- The template sensor `sensor.solar_thermal_energy_total` has the correct attributes for the Energy Dashboard
- `device_class: energy` and `state_class: total_increasing` are required
- This sensor can be selected in the Energy Dashboard

### 2. Utility Meter for Daily Statistics

Then create utility meters for different time periods:

```yaml
# configuration.yaml

utility_meter:
  solar_energy_daily:
    source: sensor.solar_energy_total
    name: "Solar Energy Today"
    cycle: daily
    
  solar_energy_weekly:
    source: sensor.solar_energy_total
    name: "Solar Energy Week"
    cycle: weekly
    
  solar_energy_monthly:
    source: sensor.solar_energy_total
    name: "Solar Energy Month"
    cycle: monthly
    
  solar_energy_yearly:
    source: sensor.solar_energy_total
    name: "Solar Energy Year"
    cycle: yearly
```

**Cycles:**
- `daily`: Reset at midnight
- `weekly`: Reset on Monday
- `monthly`: Reset on the 1st of the month
- `yearly`: Reset on January 1st
- `hourly`, `quarter-hourly`, `bimonthly` are also possible

### 3. Reload Home Assistant

After adding to `configuration.yaml`:

1. **Check Configuration**: 
   - Settings → System → Check Configuration

2. **Reload**:
   - Developer Tools → YAML → Reload
   - Select "Manually configured YAML entities"

Or restart Home Assistant completely.

## Alternative: UI-based Configuration

For newer Home Assistant versions, you can also use the UI:

### Integration Helper (Riemann Sum Integral)

**Note:** For Viessmann SolarLeistung **NOT required**, as the value is already cumulative!

If you still need an Integration Helper (for other sensors):

1. Settings → Devices & Services → Helpers
2. "Add Helper" → "Riemann Sum Integral"
3. **Input Sensor**: (Your power sensor in W/kW)
4. **Name**: Solar Energy Total
5. **Precision**: 2
6. **Method**: Left
7. **Unit Prefix**: kilo (k)
8. **Time Unit**: hours (h)

### Utility Meter Helper

1. Settings → Devices & Services → Helpers
2. "Add Helper" → "Utility Meter"
3. **Input Sensor**: sensor.solar_energy_total
4. **Name**: Solar Energy Today
5. **Cycle**: Daily
6. Optional: Enable **Tariff Mode** for different tariffs

## Usage in Dashboards

### Energy Dashboard

Add the sensors to the Energy Dashboard:

1. Settings → Dashboards → Energy
2. Under "Solar Production" → "Add Solar Panels"
3. Select `sensor.solar_thermal_energy_total` (the template sensor with correct attributes)

**Note:** The Energy Dashboard only shows sensors with `device_class: energy` and `state_class: total_increasing`. The normal integration sensor may not appear there. Therefore, use the template sensor `sensor.solar_thermal_energy_total`.

### Lovelace Cards

```yaml
type: entities
entities:
  - entity: sensor.solarleistung
    name: Current Power
  - entity: sensor.solar_energy_daily
    name: Produced Today
  - entity: sensor.solar_energy_weekly
    name: This Week
  - entity: sensor.solar_energy_monthly
    name: This Month
```

Or as Statistics Graph Card:

```yaml
type: statistics-graph
entities:
  - sensor.solar_energy_daily
stat_types:
  - sum
period:
  calendar:
    period: month
```

## Example: Gas Consumption Analog

For gas consumption, you would proceed similarly:

```yaml
sensor:
  - platform: integration
    source: sensor.gas_power  # If available
    name: "Gas Consumption Total"
    unique_id: gas_consumption_total
    unit_prefix: k
    unit_time: h

utility_meter:
  gas_consumption_daily:
    source: sensor.gas_consumption_total
    name: "Gas Consumption Today"
    cycle: daily
```

## Important Notes

### Units
- **Solar Power**: Watt (W) or Kilowatt (kW)
- **Integration**: Watt-hours (Wh) or Kilowatt-hours (kWh)
- Ensure units are correctly configured in pyvclient

### Data Continuity
- The integration sensor continuously calculates energy
- State is preserved when Home Assistant restarts
- Restarts of the source sensor can cause jumps

### Negative Values
- Integration sensor cannot process negative values
- Use separate sensors for bidirectional energy flows

## Troubleshooting

### Sensor shows "unknown" or "unavailable"
- Check if `sensor.viessmann_heating_solarleistung` delivers values
- Verify MQTT connection from pyvclient
- Test: `mosquitto_sub -h [IP] -u [USER] -P [PASS] -t "viessmann/solarleistung"`

### Values too high/low
- Viessmann `SolarLeistung` is in **Wh** (Watt-hours)
- Division by 1000 gives kWh: `51274 / 1000 = 51.274 kWh`
- If your value is already in kWh, remove `/ 1000`

### Utility Meter doesn't reset
- Check system time in Home Assistant
- Verify timezone settings

### Utility Meter shows 0, even though sensor has values
- **Normal for initial setup!** The utility meter was set up today
- It compares: Current value - Value at midnight
- If both are equal (e.g., 51.274 - 51.274) = 0
- **Solution:** Wait until tomorrow (after midnight), then it will count correctly
- From tomorrow on, it will show the daily increase

### Integration sensor jumps on restart
- Use `method: trapezoidal` for more accurate calculation
- For cumulative sensors (like SolarLeistung), no integration sensor is needed

## Further Information

- [Home Assistant Integration Sensor](https://www.home-assistant.io/integrations/integration/)
- [Home Assistant Utility Meter](https://www.home-assistant.io/integrations/utility_meter/)
- [Home Assistant Energy Dashboard](https://www.home-assistant.io/docs/energy/)
