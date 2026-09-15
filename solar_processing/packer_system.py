import logging

logger = logging.getLogger(__name__)

class SystemInstructionPacker:

    @staticmethod
    def to_json_instruction(command: str, value: str) -> dict:
        return {
            "type": "action",
            "device": "plantform1",
            "command": command,
            "params": [str(value)],
        }