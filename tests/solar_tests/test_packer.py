import pytest
import pandas as pd
from solar_processing.packer import PiInstructionPacker

def test_packer_compresses_to_hourly_averages():
    times = pd.to_datetime(["2026-05-07 08:00:00", "2026-05-07 08:30:00", "2026-05-07 09:00:00"])
    mock_df = pd.DataFrame({"power_percentage": [10.0, 30.0, 50.0]}, index=times)

    payload = PiInstructionPacker.to_hourly_payload(mock_df)
    assert payload[8] == 20.0
    assert payload[9] == 50.0
