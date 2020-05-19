import logging
import re

from homie.support.repeating_timer import Repeating_Timer
from pyvclient.homie.device_viesmann_heater import DeviceViessmannHeater

logger = logging.getLogger(__name__)

rx_dict = {
    'type': re.compile(r'Type:(?P<type>.*)'),
    'enum_value': re.compile(r'Enum Bytes: (?P<value>\d+) Text: (?P<text>.*)'),
    'unit': re.compile(r'Einheit: (?P<unit>.*)'),
}


class ObjectView(object):

    def __init__(self, d):
        self.__dict__ = d


class CallBack:

    def __init__(self, heater):
        self.properties = []
        self.heater = heater
        pass

    def __call__(self):
        self.heater.update_properties(self.properties)

    def add_property(self, command):
        self.properties.append(command)


def parse_item(command, props, detail, raw_value):
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

    data = ObjectView(data)

    data.raw_value = raw_value
    data.value = parse_value(raw_value, data)

    return data


class PyVClient:

    def __init__(self, vcomm, config):
        self.vcomm = vcomm
        self.config = ObjectView(config)
        self.properties = self.config.Properties
        self.items = self._get_items()
        self.heater = DeviceViessmannHeater(self.items.values(),
                                            mqtt_settings=self.config.MQTT_SETTINGS)

    def _get_items(self):
        items = []
        detail_commands = {cmd: 'detail get' + cmd for cmd in self.properties}
        details = self.vcomm.process_commands(detail_commands.values())

        commands = {cmd: 'get' + cmd for cmd in self.properties}
        values = self.vcomm.process_commands(commands.values())

        for cmd in self.properties:
            items.append(parse_item(cmd,
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
                parse_value(value_raw[0], self.items.get(prop)))

    def setup_timers(self):
        logger.info("setting up cron")
        callbacks = {}
        for prop in self.properties:
            interval = self.properties[prop]['interval']
            if interval not in callbacks:
                callbacks[interval] = CallBack(self)
            callbacks[interval].add_property(prop)

        for cb in callbacks:
            repeating_timer = Repeating_Timer(
                cb
            )
            repeating_timer.add_callback(callbacks[cb])


def _parse_line(line):
    for key, rx in rx_dict.items():
        match = rx.search(line)
        if match:
            return key, match
        # if there are no matches
    return None, None


def parse_value(value, item):
    value = str(value).replace(item.unit, '').strip()
    if item.type == 'short':
        value = float(value)
    elif item.type == 'int' or item.type == 'uint':
        value = int(float(value))
    return value
