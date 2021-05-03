import logging
from homie.node.property.property_base import Property_Base

logger = logging.getLogger(__name__)


class Property_Enum(Property_Base):
    def __init__(
        self,
        node,
        id,
        name,
        settable=True,
        retained=True,
        qos=1,
        unit=None,
        data_type="enum",
        data_format=None,
        value=None,
        set_value=None,
        tags=[],
        meta={},
    ):
        assert data_format
        super().__init__(
            node,
            id,
            name,
            settable,
            retained,
            qos,
            unit,
            data_type,
            data_format,
            value,
            set_value,
            tags,
            meta,
        )

        self.enum_list = data_format.split(",")

    def validate_value(self, value):
        return value in self.enum_list

    def process_set_message(self, topic, payload):  # override as needed
        value = self.get_value_from_payload(payload)

        if value is not None:
            if self.validate_value(value):
                self.value = value
                self.set_value(value, topic)  # call function to actually change the value
            else:
                logger.warning(
                    "Payload value not valid for property for topic {}, payload is {}".format(
                        topic, payload
                    )
                )
        else:
            logger.warning(
                "Unable to convert payload for property topic {}, payload is {}".format(
                    topic, payload
                )
            )

