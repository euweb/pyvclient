"""
Home Assistant MQTT Discovery module.
Handles MQTT connection and discovery message publishing.
"""
import json
import logging
from typing import Dict, Any, Optional, Callable

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class HAMqttClient:
    """
    MQTT client for Home Assistant integration.
    Manages connection, publishing discovery configs, state updates, and command subscriptions.
    """

    def __init__(
        self,
        broker: str = "localhost",
        port: int = 1883,
        username: Optional[str] = None,
        password: Optional[str] = None,
        client_id: Optional[str] = None,
    ):
        """
        Initialize MQTT client for Home Assistant.

        Args:
            broker: MQTT broker hostname
            port: MQTT broker port
            username: Optional MQTT username
            password: Optional MQTT password
            client_id: Optional MQTT client ID
        """
        self.broker = broker
        self.port = port
        self.client_id = client_id or "viessmann_vcontrold"
        
        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        if username and password:
            self.client.username_pw_set(username, password)
        
        self.connected = False
        self._command_callbacks: Dict[str, Callable] = {}
        self._lwt_topic = "viessmann/status"
        
        # Set Last Will and Testament
        self.client.will_set(
            self._lwt_topic,
            payload="offline",
            qos=1,
            retain=True
        )
        
        logger.info(f"MQTT client initialized for broker {broker}:{port}")

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker."""
        if rc == 0:
            self.connected = True
            logger.info("Connected to MQTT broker")
            
            # Publish online status
            self.publish(self._lwt_topic, "online", retain=True)
            
            # Resubscribe to command topics
            for topic in self._command_callbacks.keys():
                self.client.subscribe(topic)
                logger.debug(f"Subscribed to {topic}")
        else:
            self.connected = False
            logger.error(f"Failed to connect to MQTT broker, return code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker."""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnection from MQTT broker, rc: {rc}")
        else:
            logger.info("Disconnected from MQTT broker")

    def _on_message(self, client, userdata, msg):
        """Callback when message received on subscribed topic."""
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        
        logger.debug(f"Received message on {topic}: {payload}")
        
        if topic in self._command_callbacks:
            try:
                self._command_callbacks[topic](payload)
            except Exception as e:
                logger.error(f"Error executing callback for {topic}: {e}", exc_info=True)

    def connect(self):
        """Connect to MQTT broker."""
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            logger.info("MQTT connection initiated")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise

    def disconnect(self):
        """Disconnect from MQTT broker."""
        if self.connected:
            self.publish(self._lwt_topic, "offline", retain=True)
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Disconnected from MQTT broker")

    def publish(self, topic: str, payload: str, retain: bool = False, qos: int = 1):
        """
        Publish message to MQTT topic.

        Args:
            topic: MQTT topic
            payload: Message payload (string)
            retain: Whether to retain message
            qos: Quality of Service level (0, 1, or 2)
        """
        if not self.connected:
            logger.warning(f"Not connected to MQTT broker, cannot publish to {topic}")
            return
        
        try:
            result = self.client.publish(topic, payload, qos=qos, retain=retain)
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.error(f"Failed to publish to {topic}, rc: {result.rc}")
            else:
                logger.debug(f"Published to {topic}: {payload[:100]}")
        except Exception as e:
            logger.error(f"Error publishing to {topic}: {e}")

    def publish_discovery(self, domain: str, object_id: str, config: Dict[str, Any]):
        """
        Publish Home Assistant discovery configuration.

        Args:
            domain: HA domain (sensor, binary_sensor, number, select, climate, etc.)
            object_id: Unique object identifier
            config: Discovery configuration dictionary
        """
        topic = f"homeassistant/{domain}/{object_id}/config"
        payload = json.dumps(config)
        
        logger.info(f"Publishing discovery config for {domain}.{object_id}")
        self.publish(topic, payload, retain=True)

    def subscribe_command(self, topic: str, callback: Callable[[str], None]):
        """
        Subscribe to command topic with callback.

        Args:
            topic: MQTT topic to subscribe to
            callback: Function to call when message received (receives payload as string)
        """
        self._command_callbacks[topic] = callback
        
        if self.connected:
            self.client.subscribe(topic)
            logger.info(f"Subscribed to command topic: {topic}")

    def publish_state(self, topic: str, state: Any, retain: bool = False):
        """
        Publish state value to topic.

        Args:
            topic: State topic
            state: State value (will be converted to string)
            retain: Whether to retain the message
        """
        payload = str(state)
        self.publish(topic, payload, retain=retain)


def create_device_config() -> Dict[str, Any]:
    """
    Create the shared device configuration for all entities.
    
    Returns:
        Device configuration dictionary
    """
    return {
        "identifiers": ["viessmann_vcontrold"],
        "manufacturer": "Viessmann",
        "model": "via vcontrold",
        "name": "Viessmann Heating"
    }
