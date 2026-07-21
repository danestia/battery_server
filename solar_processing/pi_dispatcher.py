import paho.mqtt.client as mqtt
from solar_processing.packer import PiInstructionPacker

class PlantformMQTTDispatcher:
    def __init__(self, broker_ip: str, port: int = 1883, topic: str = "prototypes"):
        self.broker = broker_ip
        self.port = port
        self.topic = topic

    def format_pipe_string(self, working_hours_dict: dict) -> str:
        hours = range(8, 18)
        values = [f"{float(working_hours_dict.get(h, 0.0)):.3f}" for h in hours]
        return f"<plantform|update|{'|'.join(values)}|play>"
    
    def dispatch(self, power_df) -> bool:
        full_day_payload = PiInstructionPacker.to_hourly_payload(power_df)
        working_payload = PiInstructionPacker.slice_working_hours(full_day_payload)

        pipe_str = self.format_pipe_string(working_payload)

        client = mqtt.Client()
        client.connect(self.broker, self.port, 60)
        client.publish(self.topic, pipe_str)
        client.disconnect()
        return True
