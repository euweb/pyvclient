from homie.node.property.property_float import Property_Float

class Property_Temperature(Property_Float):
    def __init__(
        self,
        node,
        id="temperature",
        name="Temperature",
        settable=False,
        retained=True,
        qos=1,
        unit=None,
        data_type=None,
        data_format=None,
        value=None,
        set_value=None,
        tags=[],
        meta={},
    ):

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

    def process_set_message(self, topic, payload):
        value = self.get_value_from_payload(payload)

        if value is not None:
            if self.validate_value(value):
                self.value = value
                self.set_value(value, self.name)  # call function to actually change the value
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