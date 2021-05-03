from homie.node.property.property_base import Property_Base


class Property_String(Property_Base):
    def __init__(
        self,
        node,
        id,
        name,
        settable=False,
        retained=True,
        qos=1,
        unit=None,
        data_type="string",
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
            "string",
            data_format,
            value,
            set_value,
            tags,
            meta,
        )


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

