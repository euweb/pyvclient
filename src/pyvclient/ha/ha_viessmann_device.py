"""
Home Assistant Viessmann device implementation.
Main class that manages MQTT discovery, state updates, and command handling.
"""
import logging
import time
from typing import Dict, List, Any, Optional

from pyvclient.ha.ha_mqtt_discovery import HAMqttClient, create_device_config
from pyvclient.ha.ha_entities import EntityFactory, HAEntity
from pyvclient.vcomm.vcomm import VComm, VCommError

logger = logging.getLogger(__name__)


class ViessmannDevice:
    """
    Home Assistant device for Viessmann heating system via vcontrold.
    Manages MQTT discovery, state publishing, and command handling.
    """

    def __init__(
        self,
        items: List[Any],
        vcomm: VComm,
        mqtt_settings: Dict[str, Any],
        base_topic: str = "viessmann"
    ):
        """
        Initialize Viessmann HA device.

        Args:
            items: List of vcontrold items (properties)
            vcomm: VComm instance for vcontrold communication
            mqtt_settings: MQTT configuration dictionary
            base_topic: Base MQTT topic prefix
        """
        self.vcomm = vcomm
        self.base_topic = base_topic
        self.device_config = create_device_config()
        
        # Initialize MQTT client
        self.mqtt = HAMqttClient(
            broker=mqtt_settings.get("MQTT_BROKER", "localhost"),
            port=mqtt_settings.get("MQTT_PORT", 1883),
            username=mqtt_settings.get("MQTT_USERNAME"),
            password=mqtt_settings.get("MQTT_PASSWORD"),
            client_id=mqtt_settings.get("MQTT_CLIENT_ID")
        )
        
        # Create entities from items
        self.entities: Dict[str, HAEntity] = {}
        self._create_entities(items)
        
        logger.info(f"Initialized Viessmann device with {len(self.entities)} entities")

    def _create_entities(self, items: List[Any]):
        """Create HA entities from vcontrold items."""
        for item in items:
            entity = EntityFactory.create_entity(
                item,
                self.device_config,
                self.base_topic
            )
            
            if entity:
                self.entities[item.name] = entity
                # Store initial value from item
                entity._initial_value = getattr(item, 'value', None)
                logger.debug(f"Created entity: {entity.name} ({entity.__class__.__name__})")
            else:
                logger.warning(f"Failed to create entity for item: {item.name}")

    def start(self):
        """Start the device: connect MQTT and publish discovery."""
        logger.info("Starting Viessmann device")
        
        # Connect to MQTT
        self.mqtt.connect()
        
        # Wait a bit for connection to establish
        time.sleep(1)
        
        if not self.mqtt.connected:
            logger.error("Failed to connect to MQTT broker")
            raise ConnectionError("MQTT connection failed")
        
        # Publish discovery configurations
        self._publish_discovery()
        
        # Publish initial state values
        self._publish_initial_states()
        
        # Subscribe to command topics for settable entities
        self._subscribe_commands()
        
        logger.info("Viessmann device started successfully")

    def stop(self):
        """Stop the device and disconnect MQTT."""
        logger.info("Stopping Viessmann device")
        self.mqtt.disconnect()

    def _publish_discovery(self):
        """Publish Home Assistant discovery configurations for all entities."""
        logger.info("Publishing discovery configurations")
        
        for name, entity in self.entities.items():
            try:
                # Determine domain based on entity type
                domain = self._get_domain_for_entity(entity)
                
                # Get discovery config
                config = entity.get_discovery_config()
                
                # Publish discovery
                self.mqtt.publish_discovery(domain, entity.object_id, config)
                
                logger.debug(f"Published discovery for {domain}.{entity.object_id}")
                
            except Exception as e:
                logger.error(f"Failed to publish discovery for {name}: {e}", exc_info=True)
        
        logger.info("Discovery configurations published")

    def _publish_initial_states(self):
        """Publish initial state values for all entities."""
        logger.info("Publishing initial state values")
        
        for name, entity in self.entities.items():
            try:
                # Get initial value stored during creation
                initial_value = getattr(entity, '_initial_value', None)
                
                if initial_value is not None:
                    # Parse and publish the value
                    parsed_value = str(initial_value).strip()
                    self.mqtt.publish_state(entity.state_topic, parsed_value)
                    logger.debug(f"Published initial state for {name}: {parsed_value}")
                else:
                    logger.debug(f"No initial value for {name}, skipping")
                    
            except Exception as e:
                logger.error(f"Failed to publish initial state for {name}: {e}", exc_info=True)
        
        logger.info("Initial state values published")

    def _get_domain_for_entity(self, entity: HAEntity) -> str:
        """Get Home Assistant domain for entity type."""
        from pyvclient.ha.ha_entities import (
            HASensor, HABinarySensor, HANumber, HASelect, HAClimate
        )
        
        if isinstance(entity, HASensor):
            return "sensor"
        elif isinstance(entity, HABinarySensor):
            return "binary_sensor"
        elif isinstance(entity, HANumber):
            return "number"
        elif isinstance(entity, HASelect):
            return "select"
        elif isinstance(entity, HAClimate):
            return "climate"
        else:
            return "sensor"  # Default fallback

    def _subscribe_commands(self):
        """Subscribe to command topics for settable entities."""
        from pyvclient.ha.ha_entities import HANumber, HASelect, HAClimate
        
        for name, entity in self.entities.items():
            try:
                if isinstance(entity, (HANumber, HASelect)):
                    command_topic = entity.command_topic
                    self.mqtt.subscribe_command(
                        command_topic,
                        lambda payload, entity_name=name: self._handle_command(entity_name, payload)
                    )
                    logger.debug(f"Subscribed to commands for {name} on {command_topic}")
                
                elif isinstance(entity, HAClimate):
                    # Subscribe to temperature command topic
                    self.mqtt.subscribe_command(
                        entity.temperature_command_topic,
                        lambda payload, entity_name=name: self._handle_temperature_command(entity_name, payload)
                    )
                    
                    # Subscribe to mode command topic if exists
                    if entity.mode_command_topic:
                        self.mqtt.subscribe_command(
                            entity.mode_command_topic,
                            lambda payload, entity_name=name: self._handle_mode_command(entity_name, payload)
                        )
                    
                    logger.debug(f"Subscribed to climate commands for {name}")
                    
            except Exception as e:
                logger.error(f"Failed to subscribe commands for {name}: {e}", exc_info=True)

    def _handle_command(self, entity_name: str, payload: str):
        """
        Handle command for settable entity (number or select).
        
        Args:
            entity_name: Name of the entity
            payload: Command payload (new value)
        """
        logger.info(f"Received command for {entity_name}: {payload}")
        
        entity = self.entities.get(entity_name)
        if not entity:
            logger.error(f"Entity {entity_name} not found")
            return
        
        try:
            # Execute vcontrold set command
            # Convert get command to set command (e.g., getTempA -> setTempA)
            set_command = entity.vcontrol_command.replace('get', 'set', 1)
            
            success = self.vcomm.set_command(set_command[3:], payload)  # Remove 'set' prefix
            
            if success:
                logger.info(f"Successfully set {entity_name} to {payload}")
                # Publish new state
                self.mqtt.publish_state(entity.state_topic, payload)
            else:
                logger.error(f"Failed to set {entity_name} to {payload}")
                
        except VCommError as e:
            logger.error(f"VComm error setting {entity_name}: {e}")
        except Exception as e:
            logger.error(f"Error handling command for {entity_name}: {e}", exc_info=True)

    def _handle_temperature_command(self, entity_name: str, payload: str):
        """Handle temperature command for climate entity."""
        self._handle_command(entity_name, payload)

    def _handle_mode_command(self, entity_name: str, payload: str):
        """Handle mode command for climate entity."""
        self._handle_command(entity_name, payload)

    def update_properties(self, properties: List[str]):
        """
        Update multiple properties by reading from vcontrold and publishing to MQTT.
        
        Args:
            properties: List of property names to update
        """
        logger.debug(f"Updating properties: {properties}")
        
        try:
            # Build command dictionary
            commands = {}
            for prop in properties:
                entity = self.entities.get(prop)
                if entity:
                    commands[entity.vcontrol_command] = prop
            
            if not commands:
                logger.warning("No valid properties to update")
                return
            
            # Execute commands via vcontrold
            results = self.vcomm.process_commands(commands.keys())
            
            # Publish updated values
            for vcontrol_cmd, prop_name in commands.items():
                if vcontrol_cmd in results:
                    raw_value = results[vcontrol_cmd]
                    if raw_value and len(raw_value) > 0:
                        value = raw_value[0]
                        self.update_value(prop_name, value)
                    else:
                        logger.warning(f"Empty result for {prop_name}")
                else:
                    logger.warning(f"No result for {prop_name}")
                    
        except Exception as e:
            logger.error(f"Error updating properties: {e}", exc_info=True)

    def update_value(self, entity_name: str, value: Any):
        """
        Update and publish single entity value.
        
        Args:
            entity_name: Name of the entity
            value: New value to publish
        """
        entity = self.entities.get(entity_name)
        if not entity:
            logger.warning(f"Entity {entity_name} not found")
            return
        
        try:
            # Parse/clean value if needed
            parsed_value = self._parse_value(value, entity)
            
            # Publish to state topic
            self.mqtt.publish_state(entity.state_topic, parsed_value)
            
            logger.debug(f"Updated {entity_name} to {parsed_value}")
            
        except Exception as e:
            logger.error(f"Error updating value for {entity_name}: {e}", exc_info=True)

    def _parse_value(self, value: Any, entity: HAEntity) -> Any:
        """
        Parse and clean value from vcontrold.
        
        Args:
            value: Raw value from vcontrold
            entity: Entity to update
            
        Returns:
            Parsed value suitable for MQTT publishing
        """
        from pyvclient.ha.ha_entities import HASensor
        
        # Convert to string and clean
        value_str = str(value).strip()
        
        # Remove unit from value if present
        if isinstance(entity, HASensor) and entity.unit_of_measurement:
            value_str = value_str.replace(entity.unit_of_measurement, '').strip()
        
        return value_str
