import pytest
import pandas as pd
from solar_processing.packer import PiInstructionPacker

def test_packer_compresses_to_hourly_averages_scaled_to_decimal():
    times = pd.to_datetime(["2026-05-07 08:00:00", "2026-05-07 08:30:00", "2026-05-07 09:00:00"])
    mock_df = pd.DataFrame({"power_percentage": [10.0, 30.0, 50.0]}, index=times)

    payload = PiInstructionPacker.to_hourly_payload(mock_df)
    assert payload[8] == 0.200
    assert payload[9] == 0.500
    assert payload[0] == 0.0

def test_packer_caps_outlier_spikes():
    times = pd.to_datetime(["2026-05-07 12:00:00", "2026-05-07 13:00"])
    mock_df = pd.DataFrame({"power_percentage": [115.5, -5.0]}, index=times)

    payload = PiInstructionPacker.to_hourly_payload(mock_df)

    assert payload[12] == 1.000
    assert payload[13] == 0.000

def test_packer_handles_empty_dataframe():
    payload = PiInstructionPacker.to_hourly_payload(pd.DataFrame())
    assert payload == {}