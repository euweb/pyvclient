import logging
import re

from pyvclient.utils.repeating_timer import RepeatingTimer
from pyvclient.ha.ha_viessmann_device import ViessmannDevice

logger = logging.getLogger(__name__)

rx_dict = {
    'type': re.compile(r'Type:(?P<type>.*)'),
    'enum_value': re.compile(r'Enum Bytes: (?P<value>\d+) Text: (?P<text>.*)'),
    'unit': re.compile(r'Einheit: (?P<unit>.*)'),
    'calc': re.compile(r'Get-Calc: (?P<calc>.*)')
}


class ObjectView(object):

    def __init__(self, d):
        self.__dict__ = d


class UpdateCallback:
    """Callback for periodic property updates."""

    def __init__(self, device):
        self.properties = []
        self.device = device

    def __call__(self):
        self.device.update_properties(self.properties)

    def add_property(self, command):
        self.properties.append(command)


def _parse_line(line):
    for key, rx in rx_dict.items():
        match = rx.search(line)
        if match:
            return key, match
        # if there are no matches
    return None, None


class PyVClient:

    def __init__(self, vcomm, config):
        self.vcomm = vcomm
        self.config = ObjectView(config)
        self.properties = self.config.Properties
        self.precision = self.config.Precision
        
        # Try to get items, but don't fail if vcontrold is not available
        try:
            self.items = self._get_items()
        except Exception as e:
            logger.error(f"Failed to initialize items from vcontrold: {e}")
            logger.info("Creating stub items from config - will update when vcontrold is available")
            self.items = self._create_stub_items()
        
        self.device = ViessmannDevice(
            list(self.items.values()),
            vcomm=vcomm,
            mqtt_settings=self.config.MQTT_SETTINGS
        )
        self.device.start()

    def _create_stub_items(self):
        """Create stub items when vcontrold is not available."""
        items = {}
        for cmd in self.properties:
            data = ObjectView({
                'name': cmd,
                'get_command': 'get' + cmd,
                'settable': not self.properties[cmd]['readonly'],
                'type': 'short',  # Default type
                'unit': '',
                'value': 0,
                'raw_value': '0'
            })
            items[cmd] = data
        return items

    def _get_items(self):
        items = []
        detail_commands = {cmd: 'detail get' + cmd for cmd in self.properties}
        details = self.vcomm.process_commands(detail_commands.values())

        commands = {cmd: 'get' + cmd for cmd in self.properties}
        values = self.vcomm.process_commands(commands.values())

        for cmd in self.properties:
            items.append(self.parse_item(cmd,
                                         self.properties.get(cmd),
                                         details.get(detail_commands[cmd]),
                                         values.get(commands[cmd])[0]))

        return {item.name: item for item in items}

    def update_properties(self, properties):
        logger.debug(properties)
        commands = {cmd: 'get' + cmd for cmd in properties}
        values = self.vcomm.process_commands(commands.values())
        for prop in properties:
            value_raw = values.get(commands[prop])
            self.heater.update_value(
                prop,
                self.parse_value(value_raw[0], self.items.get(prop)))

    def setup_timers(self):
        """Setup periodic update timers for properties."""
        logger.info("Setting up periodic update timers")
        callbacks = {}
        for prop in self.properties:
            interval = self.properties[prop]['interval']
            if interval not in callbacks:
                callbacks[interval] = UpdateCallback(self.device)
            callbacks[interval].add_property(prop)

        for interval, callback in callbacks.items():
            repeating_timer = RepeatingTimer(interval)
            repeating_timer.add_callback(callback)
        
        logger.info(f"Setup {len(callbacks)} timers")

    def parse_value(self, value, item):
        value = str(value).replace(item.unit, '').strip()
        if item.type == 'short':
            digits = self.precision.get(item.calc)
            logger.debug("Precision: %s", digits)
            if digits:
                value = round(float(value), digits)
            else:
                value = float(value)
        elif item.type == 'int' or item.type == 'uint':
            value = int(float(value))
        return value

    def parse_item(self, command, props, detail, raw_value):
        get_command = 'get' + command

        data = {
            'name': command,
            'get_command': get_command,
            'settable': not props['readonly'] or False
        }

        for line in detail:
            key, match = _parse_line(line)

            if key == 'type':
                data[key] = (match.group('type').strip())

            if key == 'unit':
                data[key] = (match.group('unit').strip())

            if key == 'enum_value':
                if 'enum' in data:
                    data['enum'].append(match.group('text').strip())
                else:
                    data['enum'] = [match.group('text').strip()]
            if key == 'calc':
                data['calc'] = (match.group('calc').strip())

        data = ObjectView(data)

        data.raw_value = raw_value
        data.value = self.parse_value(raw_value, data)

        return data
