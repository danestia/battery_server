import paho.mqtt.client as mqtt
import json
import logging
from solar_processing.packer import PiInstructionPacker

logger = logging.getLogger(__name__)

class PlantformMQTTDispatcher:
    def __init__(self, broker_ip: str, port: int = 1883, topic: str = "prototypes/schedule"):
        self.broker = broker_ip
        self.port = port
        self.topic = topic
    
    def dispatch(self, power_df) -> bool:
        try:
            full_day_payload = PiInstructionPacker.to_hourly_payload(power_df)
            working_payload = PiInstructionPacker.slice_working_hours(full_day_payload)

            json_payload = json.dumps(working_payload)

            client = mqtt.Client()
            client.connect(self.broker, self.port, keepalive=60)

            result = client.publish(self.topic, json_payload, retain=True)
            client.disconnect()

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Successfully published retained JSON to {self.topic}: {json_payload}")
                return True
            else:
                logger.error(f"Failed to publish to MQTT broker. Return code: {result.rc}")
                return False
            
        except Exception as e:
            logger.error(f"MQTT Dispatch Exception: {e}")
            return False
