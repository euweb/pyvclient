import logging

from homie.device_base import Device_Base
from homie.node.node_base import Node_Base
from .property_enum import Property_Enum
from .property_integer import Property_Integer
from .property_temperature import Property_Temperature
from .property_string import Property_String
from pyvclient.vcomm.vcomm import VComm
from pyvclient.vcomm.vcomm import VCommError

logger = logging.getLogger(__name__)

MQTT_DEFAULT_SETTINGS = {
    "MQTT_BROKER": "localhost",
    "MQTT_PORT": 1883,
}


class DeviceViessmannHeater(Device_Base):
    vcomm = None
    def __init__(self,
                 item_config,
                 device_id="viessmann",
                 name="Viessmann Heizung",
                 homie_settings=None,
                 mqtt_settings=MQTT_DEFAULT_SETTINGS,
                 vc=None
                 ):
        super().__init__(device_id, name, homie_settings, mqtt_settings)
        self.vcomm=vc
        node = Node_Base(self, "generic", "Generic", "generic")
        self.add_node(node)

        for item in item_config:

            if item.type == 'enum':
                enum_item = Property_Enum(
                    node,
                    id=item.name.lower(),
                    name=item.name,
                    settable=item.settable,
                    data_format=",".join(item.enum),
                    value=item.value,
                    set_value=self.set_value if item.settable else None
                )
                node.add_property(enum_item)
                item.property = enum_item
                # self.items[item.name] = item
            elif item.type == 'short':
                value = float(item.value)
                short_item = Property_Temperature(
                    node,
                    id=item.name.lower(),
                    name=item.name,
                    settable=item.settable,
                    data_format="-150:150",
                    value=value,
                    unit=item.unit,
                    set_value=self.set_value if item.settable else None
                )
                node.add_property(short_item)
                item.property = short_item
            elif item.type == 'int' or item.type == 'uint':
                value = int(float(item.value))
                int_value = Property_Integer(
                    node,
                    id=item.name.lower(),
                    name=item.name,
                    settable=item.settable,
                    value=value,
                    unit=item.unit,
                    set_value=self.set_value if item.settable else None
                )
                node.add_property(int_value)
                item.property = int_value
            elif item.type == 'systime':
                value = item.value
                string_value = Property_String(
                    node,
                    id=item.name.lower(),
                    name=item.name,
                    settable=item.settable,
                    value=value,
                    unit=item.unit,
                    set_value=self.set_value if item.settable else None
                )
                node.add_property(string_value)
                item.property = string_value
            else:
                logger.info("Unknown item: " + item.__dict__)

        logger.info('done')

        self.start()

    def set_value(self, value, name):     
        logger.debug("Set value: {} for {}".format(value, name))
        try:
            self.vcomm.set_command(name, value)
        except VCommError:
            logger.error("Failed to set " + name + " to " + value)

    def update_value(self, node_id, value):
        try:
            logger.debug("{}: update {}".format(node_id, value))
            # self.get_node('generic').get_property
            self.get_node('generic'). \
                get_property(node_id.lower()).value = value
        except Exception as e:
            logger.error(e)
