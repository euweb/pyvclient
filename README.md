# pyvclient

A Python module providing a Home Assistant MQTT Discovery interface to communicate with Viessmann heaters via vcontrold.

## Features

* **Home Assistant Integration**: Automatic device and entity discovery via MQTT
* **vcontrold Backend**: Communicates with Viessmann heating systems through vcontrold
* **Real-time Updates**: Periodic polling and state updates
* **Bidirectional Control**: Read sensor values and control settable parameters
* **Single Device**: All entities are grouped under one Home Assistant device

## Usage

Create a virtual environment:

```bash
python -m venv .venv
. .venv/bin/activate
# fish users: . .venv/bin/activate.fish
```

Install package (plus dependencies) in the virtual environment:

```bash
pip install .
```

Run as a console script:

```bash
pyvclient --log src/conf/logging.yaml src/conf/config.yaml
```

## Configuration

**Quick Start:**

1. Copy the configuration template:

   ```bash
   cd src/conf
   cp config.yaml.template config.yaml
   ```

2. Edit `config.yaml` with your settings (MQTT broker, vcontrold host, credentials)

**Important:** `config.yaml` is excluded from version control to protect your credentials.

For detailed configuration instructions, see [CONFIGURATION.md](CONFIGURATION.md).

The application will automatically:

1. Connect to MQTT broker
2. Publish Home Assistant discovery configurations
3. Start periodic updates for all configured properties
4. Subscribe to command topics for settable entities

## Documentation

* [Configuration Guide](CONFIGURATION.md) - Detailed setup instructions
* [MQTT Topics](MQTT_TOPICS.md) - MQTT topic structure and payloads
* [Utility Meter Setup](UTILITY_METER_SETUP.md) - Home Assistant Energy Dashboard integration
* [Migration Guide](MIGRATION.md) - Migrating from Homie 4 to HA MQTT Discovery

## Home Assistant Integration

Once running, the Viessmann heating system will appear in Home Assistant as a single device with multiple entities:

* **Sensors**: Temperature readings, counters, system time
* **Numbers**: Settable values like heating curves, target temperatures
* **Selects**: Operation modes and enum values

All entities support:

* Automatic discovery (no YAML configuration needed)
* Availability tracking (online/offline status)
* Proper units and device classes
* State updates based on configured intervals

## Links

* vcontrold: https://github.com/openv/openv/wiki/vcontrold
* Home Assistant MQTT Discovery: https://www.home-assistant.io/integrations/mqtt/#mqtt-discovery

## Note

This project has been set up using PyScaffold 3.2.3. For details and usage information on PyScaffold see https://pyscaffold.org/.
