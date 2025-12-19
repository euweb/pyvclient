=========
pyvclient
=========

A Python module providing a Home Assistant MQTT Discovery interface to communicate with Viessmann heaters via vcontrold.

Features
========

* **Home Assistant Integration**: Automatic device and entity discovery via MQTT
* **vcontrold Backend**: Communicates with Viessmann heating systems through vcontrold
* **Real-time Updates**: Periodic polling and state updates
* **Bidirectional Control**: Read sensor values and control settable parameters
* **Single Device**: All entities are grouped under one Home Assistant device

Usage
=====

Create a virtual environment::

    python -m venv .venv
    . .venv/bin/activate
    # fish users: . .venv/bin/activate.fish

Install package (plus dependencies) in the virtual environment::

    pip install .

Run as a console script::

    pyvclient --log src/conf/logging.yaml src/conf/config.yaml

Configuration
=============

Edit ``src/conf/config.yaml`` to configure:

* MQTT broker settings
* vcontrold connection (host, port)
* Properties to monitor (with update intervals)
* Precision for value parsing

The application will automatically:

1. Connect to MQTT broker
2. Publish Home Assistant discovery configurations
3. Start periodic updates for all configured properties
4. Subscribe to command topics for settable entities

Home Assistant Integration
===========================

Once running, the Viessmann heating system will appear in Home Assistant as a single device with multiple entities:

* **Sensors**: Temperature readings, counters, system time
* **Numbers**: Settable values like heating curves, target temperatures
* **Selects**: Operation modes and enum values

All entities support:

* Automatic discovery (no YAML configuration needed)
* Availability tracking (online/offline status)
* Proper units and device classes
* State updates based on configured intervals

Links
=====

* vcontrold: https://github.com/openv/openv/wiki/vcontrold
* Home Assistant MQTT Discovery: https://www.home-assistant.io/integrations/mqtt/#mqtt-discovery

Note
====

This project has been set up using PyScaffold 3.2.3. For details and usage
information on PyScaffold see https://pyscaffold.org/.
