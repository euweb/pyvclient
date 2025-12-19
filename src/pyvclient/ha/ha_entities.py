"""
Home Assistant entity definitions for Viessmann heating system.
Maps vcontrold properties to Home Assistant entity types.
"""
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class HAEntity:
    """Base class for Home Assistant entities."""
    name: str
    object_id: str
    vcontrol_command: str
    state_topic: str
    device_config: Dict[str, Any]
    availability_topic: str = "viessmann/status"
    payload_available: str = "online"
    payload_not_available: str = "offline"
    unique_id: Optional[str] = None
    icon: Optional[str] = None
    entity_category: Optional[str] = None  # "config", "diagnostic", None
    
    def __post_init__(self):
        if not self.unique_id:
            self.unique_id = f"viessmann_{self.object_id}"
    
    def get_discovery_config(self) -> Dict[str, Any]:
        """Get base discovery configuration common to all entities."""
        config = {
            "name": self.name,
            "unique_id": self.unique_id,
            "state_topic": self.state_topic,
            "availability_topic": self.availability_topic,
            "payload_available": self.payload_available,
            "payload_not_available": self.payload_not_available,
            "device": self.device_config,
        }
        
        if self.icon:
            config["icon"] = self.icon
        if self.entity_category:
            config["entity_category"] = self.entity_category
            
        return config


@dataclass
class HASensor(HAEntity):
    """Home Assistant sensor entity."""
    unit_of_measurement: Optional[str] = None
    device_class: Optional[str] = None  # temperature, pressure, energy, etc.
    state_class: Optional[str] = None  # measurement, total, total_increasing
    
    def get_discovery_config(self) -> Dict[str, Any]:
        config = super().get_discovery_config()
        
        if self.unit_of_measurement:
            config["unit_of_measurement"] = self.unit_of_measurement
        if self.device_class:
            config["device_class"] = self.device_class
        if self.state_class:
            config["state_class"] = self.state_class
            
        return config


@dataclass
class HABinarySensor(HAEntity):
    """Home Assistant binary sensor entity."""
    device_class: Optional[str] = None  # running, heat, etc.
    payload_on: str = "ON"
    payload_off: str = "OFF"
    
    def get_discovery_config(self) -> Dict[str, Any]:
        config = super().get_discovery_config()
        
        config["payload_on"] = self.payload_on
        config["payload_off"] = self.payload_off
        
        if self.device_class:
            config["device_class"] = self.device_class
            
        return config


@dataclass
class HANumber(HAEntity):
    """Home Assistant number entity (for settable values)."""
    command_topic: str = ""
    min_value: float = 0
    max_value: float = 100
    step: float = 1
    unit_of_measurement: Optional[str] = None
    mode: str = "auto"  # auto, box, slider
    
    def get_discovery_config(self) -> Dict[str, Any]:
        config = super().get_discovery_config()
        
        config["command_topic"] = self.command_topic
        config["min"] = self.min_value
        config["max"] = self.max_value
        config["step"] = self.step
        config["mode"] = self.mode
        
        if self.unit_of_measurement:
            config["unit_of_measurement"] = self.unit_of_measurement
            
        return config


@dataclass
class HASelect(HAEntity):
    """Home Assistant select entity (for enum values)."""
    command_topic: str = ""
    options: List[str] = field(default_factory=list)
    
    def get_discovery_config(self) -> Dict[str, Any]:
        config = super().get_discovery_config()
        
        config["command_topic"] = self.command_topic
        config["options"] = self.options
        
        return config


@dataclass
class HAClimate(HAEntity):
    """Home Assistant climate entity (for heating circuits)."""
    temperature_command_topic: str = ""
    temperature_state_topic: str = ""
    current_temperature_topic: str = ""
    mode_command_topic: Optional[str] = None
    mode_state_topic: Optional[str] = None
    modes: List[str] = field(default_factory=lambda: ["off", "heat", "auto"])
    min_temp: float = 10.0
    max_temp: float = 30.0
    temp_step: float = 0.5
    temperature_unit: str = "C"
    
    def get_discovery_config(self) -> Dict[str, Any]:
        config = super().get_discovery_config()
        
        # Remove state_topic from base (climate uses specific topics)
        config.pop("state_topic", None)
        
        config["temperature_command_topic"] = self.temperature_command_topic
        config["temperature_state_topic"] = self.temperature_state_topic
        config["current_temperature_topic"] = self.current_temperature_topic
        config["modes"] = self.modes
        config["min_temp"] = self.min_temp
        config["max_temp"] = self.max_temp
        config["temp_step"] = self.temp_step
        config["temperature_unit"] = self.temperature_unit
        
        if self.mode_command_topic:
            config["mode_command_topic"] = self.mode_command_topic
        if self.mode_state_topic:
            config["mode_state_topic"] = self.mode_state_topic
            
        return config


class EntityFactory:
    """Factory for creating Home Assistant entities from vcontrold item configuration."""
    
    @staticmethod
    def create_entity(
        item,
        device_config: Dict[str, Any],
        base_topic: str = "viessmann"
    ) -> Optional[HAEntity]:
        """
        Create appropriate HA entity from vcontrold item.
        
        Args:
            item: vcontrold item with type, name, value, etc.
            device_config: Shared device configuration
            base_topic: Base MQTT topic prefix
            
        Returns:
            HAEntity subclass instance or None
        """
        name = item.name
        object_id = item.name.lower()
        vcontrol_command = item.get_command
        state_topic = f"{base_topic}/{object_id}"
        
        # Map vcontrold types to HA entities
        if item.type == 'enum':
            # Enum values -> Select (if settable) or Sensor (if readonly)
            if item.settable:
                return HASelect(
                    name=name,
                    object_id=object_id,
                    vcontrol_command=vcontrol_command,
                    state_topic=state_topic,
                    command_topic=f"{state_topic}/set",
                    device_config=device_config,
                    options=item.enum if hasattr(item, 'enum') else [],
                    icon="mdi:cog"
                )
            else:
                return HASensor(
                    name=name,
                    object_id=object_id,
                    vcontrol_command=vcontrol_command,
                    state_topic=state_topic,
                    device_config=device_config,
                    entity_category="diagnostic"
                )
        
        elif item.type == 'short':
            # Short (float) values -> typically temperatures
            unit = getattr(item, 'unit', None)
            
            # Determine if it's a temperature based on unit
            is_temp = unit in ['°C', 'C', 'K'] if unit else 'temp' in name.lower()
            
            if item.settable:
                # Settable temperature -> Number entity
                return HANumber(
                    name=name,
                    object_id=object_id,
                    vcontrol_command=vcontrol_command,
                    state_topic=state_topic,
                    command_topic=f"{state_topic}/set",
                    device_config=device_config,
                    min_value=-50.0,
                    max_value=150.0,
                    step=0.5,
                    unit_of_measurement=unit or "°C",
                    mode="slider",
                    icon="mdi:thermometer" if is_temp else None
                )
            else:
                # Readonly temperature/float -> Sensor
                return HASensor(
                    name=name,
                    object_id=object_id,
                    vcontrol_command=vcontrol_command,
                    state_topic=state_topic,
                    device_config=device_config,
                    unit_of_measurement=unit or "°C",
                    device_class="temperature" if is_temp else None,
                    state_class="measurement",
                    icon="mdi:thermometer" if is_temp else None
                )
        
        elif item.type in ['int', 'uint']:
            # Integer values -> typically counters, hours, starts
            unit = getattr(item, 'unit', None)
            
            # Check if it's a counter/accumulator
            is_counter = any(x in name.lower() for x in ['stunden', 'hours', 'starts', 'count'])
            
            if item.settable:
                return HANumber(
                    name=name,
                    object_id=object_id,
                    vcontrol_command=vcontrol_command,
                    state_topic=state_topic,
                    command_topic=f"{state_topic}/set",
                    device_config=device_config,
                    min_value=0,
                    max_value=100000,
                    step=1,
                    unit_of_measurement=unit,
                    mode="box"
                )
            else:
                return HASensor(
                    name=name,
                    object_id=object_id,
                    vcontrol_command=vcontrol_command,
                    state_topic=state_topic,
                    device_config=device_config,
                    unit_of_measurement=unit,
                    state_class="total_increasing" if is_counter else "measurement",
                    entity_category="diagnostic",
                    icon="mdi:counter" if is_counter else None
                )
        
        elif item.type == 'systime':
            # System time -> Sensor (diagnostic)
            return HASensor(
                name=name,
                object_id=object_id,
                vcontrol_command=vcontrol_command,
                state_topic=state_topic,
                device_config=device_config,
                entity_category="diagnostic",
                icon="mdi:clock"
            )
        
        else:
            logger.warning(f"Unknown item type '{item.type}' for {name}")
            return None
