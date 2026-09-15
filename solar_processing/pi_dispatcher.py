import paho.mqtt.client as mqtt
import json
import logging
import pandas as pd
import time

from solar_processing.packer_plant import PiInstructionPacker
from solar_processing.packer_energy import EnergyInstructionPacker
from solar_processing.packer_system import SystemInstructionPacker

logger = logging.getLogger(__name__)


class PlantformMQTTDispatcher:

    def __init__(
            self,
            broker_ip: str,
            port: int = 1883,
            topic: str = "prototypes/schedule",
    ):
        self.broker = broker_ip
        self.port = port
        self.topic = topic

    def _publish(self, json_dict: dict) -> bool:
        try:
            json_payload = json.dumps(json_dict)

            try:
                client = mqtt.Client(
                    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
                )
            except AttributeError:
                client = mqtt.Client()

            client.connect(self.broker, self.port, keepalive=60)
            result = client.publish(self.topic, json_payload, retain=True)
            result.wait_for_publish(timeout=10)
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

    def dispatch_system_cmd(self, command: str, value: str) -> bool:
        json_dict = SystemInstructionPacker.to_json_instruction(command, value)
        return self._publish(json_dict)

    def power_on_sequence(self) -> bool:
        #Command Group A: Activates power supplies
        logger.info("Executing Power-On sequence (command group A)")

        if not self.dispatch_system_cmd("supply5", "on"):
            return False
        time.sleep(30)

        if not self.dispatch_system_cmd("supply220", "on"):
            return False
        time.sleep(3)

        return True

    def power_off_sequence(self) -> bool:
        #Command group C: Power supplies shutdown
        logger.info("Executing Power-Off sequence (command group C)")

        if not self.dispatch_system_cmd("supply220", "off"):
            return False
        time.sleep(3)

        if not self.dispatch_system_cmd("supply5", "off"):
            return False

        return True

    def run_activation_protocol(self) -> bool:
        logger.info("Plantform activation protocol. Starting...")

        #Power-on
        if not self.power_on_sequence():
            logger.error("Aborted during power-on sequence")
            return False
        
        #Reset/init
        logger.info("Position reset sequence")
        if not self.dispatch_system_cmd("reset", "0"):
            return False
        time.sleep(60)

        if not self.dispatch_system_cmd("init", "0"):
            return False
        time.sleep(60)

        #Power-off
        if not self.power_off_sequence():
            logger.error("Power off sequence failure")
            return False

        logger.info("Plantform1 Activation Protocol completed")
        return True

    
    def dispatch_schedule(self, power_df: pd.DataFrame) -> bool:
        full_day_payload = PiInstructionPacker.to_hourly_payload(power_df)
        working_payload = PiInstructionPacker.slice_working_hours(full_day_payload)

        json_dict = PiInstructionPacker.to_json_instruction(working_payload)
        return self._publish(json_dict)

    def dispatch_gain(self, gain_value: int | str) -> bool:
        json_dict = EnergyInstructionPacker.to_json_instruction(gain_value)
        return self._publish(json_dict)

    def run_display_protocol(self, df: pd.DataFrame) -> bool:
        logger.info("Starting Display Protocol Sequence...")

        logger.info("Executing command group A")
        if not self.power_on_sequence():
            logger.error("Power on sequence failed. Aborting display sequence")
            return False

        logger.info("Dispatching solar schedule")
        schedule_success = self.dispatch_schedule(df)

        if not schedule_success:
            logger.warning("Schedule dispatch failed. Proceeding with power down sequence")

        time.sleep(3)

        logger.info("Executing power down")
        power_off_success = self.power_off_sequence()
        if not power_off_success:
            logger.error("Failed to power down")

        overall_success = schedule_success and power_off_success
        if overall_success:
            logger.info("Display Protocol Completed")
        else:
            logger.error("Display Protocol Completed with Errors")

        return overall_success