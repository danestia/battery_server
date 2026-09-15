import pandas as pd
import logging

logger = logging.getLogger(__name__)


class EnergyInstructionPacker:

    @staticmethod
    def to_json_instruction(
        gain_value: int | str, command: str = "gain") -> dict:

        val_int = int(gain_value)
        clamped_val = max(-10, min (10, val_int))
        values = [str(clamped_val)]
    
        return {
            "type": "action",
            "device": "plantform1",
            "command": command,
            "params": values,
        }