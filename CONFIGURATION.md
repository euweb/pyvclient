# Configuration

## Initial Setup

To configure pyvclient for your environment:

1. Copy the template file:
   ```bash
   cd src/conf
   cp config.yaml.template config.yaml
   ```

2. Edit `config.yaml` and replace the placeholder values:
   - `YOUR_MQTT_BROKER_IP` - Your MQTT broker IP address or hostname
   - `YOUR_MQTT_USERNAME` - Your MQTT username
   - `YOUR_MQTT_PASSWORD` - Your MQTT password
   - `YOUR_VCONTROLD_HOST` - Your vcontrold server IP or hostname

3. Adjust the `Properties` section based on your Viessmann heating system's available commands

## Important Notes

- `config.yaml` is excluded from version control via `.gitignore` to protect your credentials
- Always use `config.yaml.template` as the reference for structure and available options
- Never commit `config.yaml` with real credentials to the repository

## Configuration Structure

### MQTT_SETTINGS
Connection settings for your MQTT broker. Required for Home Assistant integration.

**Parameters:**
- `MQTT_BROKER` - IP address or hostname of your MQTT broker
- `MQTT_PORT` - MQTT port (default: 1883)
- `MQTT_USERNAME` - Username for MQTT authentication
- `MQTT_PASSWORD` - Password for MQTT authentication
- `MQTT_KEEPALIVE` - Keepalive interval in seconds (default: 60)
- `MQTT_CLIENT_ID` - Optional client ID (default: auto-generated)
- `MQTT_SHARE_CLIENT` - Optional shared client name

### VControld
Connection settings for your vcontrold server that interfaces with your Viessmann heating system.

**Parameters:**
- `host` - IP address or hostname of vcontrold server
- `port` - vcontrold port (default: 3002)

### Properties
Define which Viessmann heating system properties to monitor:

**Parameters:**
- `readonly: true` - Read-only sensor (cannot be changed via MQTT)
- `readonly: false` - Controllable/settable value (can be changed via MQTT)
- `interval` - Update interval in seconds

**Example Properties:**
```yaml
Properties:
  TempA:              # Außentemperatur
    readonly: true
    interval: 300
  
  SolarLeistung:      # Solar Gesamtleistung (kumulativ)
    readonly: true
    interval: 3600
  
  BetriebArtM1:       # Betriebsart Heizkreis 1 (settable)
    readonly: false
    interval: 3600
```

**Interval Guidelines:**
- Fast-changing values (temperatures, pump status): 60-300 seconds
- Slow-changing values (counters, hours): 3600 seconds (1 hour)
- Rarely changing values (system settings): 3600 seconds or more

Adjust intervals based on how frequently values change and your system's load.

### Precision
Defines decimal precision for different vcontrold calculation formats.

**Format Mapping:**
- `"V"` - Raw value, 0 decimals
- `"V/2"` - Value divided by 2, 0 decimals
- `"V/10"` - Value divided by 10, 1 decimal (e.g., temperatures)
- `"V/1000"` - Value divided by 1000, 0 decimals
- `"V/3600"` - Value divided by 3600, 2 decimals (hours conversion)

## Available Properties

Refer to your Viessmann heating system's documentation or `vcontrold_data/vito.xml` for available properties.

**Common Properties:**
- **Temperature sensors:** TempA, TempWWist, TempKist, TempKol, TempVListM1
- **Solar:** SolarLeistung, SolarStunden, TempSpu
- **Burner:** BrennerStarts, BrennerStunden1, BrennerStatus
- **Pumps:** PumpeStatusM1, PumpeDrehzahlM1, PumpeStatusIntern
- **Heating circuit:** NeigungM1, NiveauM1, TempRaumNorSollM1
- **System:** SystemTime, BetriebArtM1

## Example Configuration

See [config.yaml.template](src/conf/config.yaml.template) for a complete example configuration.

## Related Documentation

- [MQTT Topics](MQTT_TOPICS.md) - MQTT topic structure and payloads
- [Utility Meter Setup](UTILITY_METER_SETUP.md) - Setting up Home Assistant with pyvclient
- [Migration Guide](MIGRATION.md) - Migrating from Homie 4 to HA MQTT Discovery
