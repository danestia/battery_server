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
    times = pd.to_datetime(["2026-05-07 12:00:00", "2026-05-07 13:00:00"])
    mock_df = pd.DataFrame({"power_percentage": [115.5, -5.0]}, index=times)

    payload = PiInstructionPacker.to_hourly_payload(mock_df)

    assert payload[12] == 1.000
    assert payload[13] == 0.000

def test_packer_handles_empty_dataframe():
    payload = PiInstructionPacker.to_hourly_payload(pd.DataFrame())
    assert payload == {}

@pytest.fixture
def sample_working_payload():
    return {
        8: 0.000,
        9: 0.000,
        10: 0.052,
        11: 0.065,
        12: 0.113,
        13: 0.266,
        14: 0.296,
        15: 0.855,
        16: 1.000,
        17: 0.954,
    }

def test_to_protocol_string_formatting(sample_working_payload):
    protocol_str = PiInstructionPacker.to_protocol_string(
        sample_working_payload, command="play"
    )
    expected = "<plantform|update|0.000|0.000|0.052|0.065|0.113|0.266|0.296|0.855|1.000|0.954|play>"
    assert protocol_str == expected

def test_to_protocol_string_padding_missing_hours():
    partial_payload = {10: 0.500, 15: 1.000}
    protocol_str = PiInstructionPacker.to_protocol_string(partial_payload)

    expected = "<plantform|update|0.000|0.000|0.500|0.000|0.000|0.000|0.000|1.000|0.000|0.000|play>"
    assert protocol_str == expected

def test_to_json_instruction_structure(sample_working_payload):
    json_dict = PiInstructionPacker.to_json_instruction(sample_working_payload)

    assert json_dict["device"] == "plantform"
    assert json_dict["action"] == "update"
    assert json_dict["command"] == "play"

    expected_schedule = {str(k): v for k, v in sample_working_payload.items()}
    assert json_dict["schedule"] == expected_schedule
    

def test_integration_full_packing_pipeline():
    times = pd.date_range("2026-05-07 00:00", periods=24, freq="1h")
    powers = [0.0] * 8 + [10.0, 30.0, 50.0, 70.0, 90.0, 100.0, 80.0, 60.0, 40.0, 20.0] + [0.0] * 6
    df = pd.DataFrame({"power_percentage": powers}, index=times)

    full_day = PiInstructionPacker.to_hourly_payload(df)
    working_hours = PiInstructionPacker.slice_working_hours(full_day)
    json_dict = PiInstructionPacker.to_json_instruction(working_hours)

    assert len(working_hours) == 10
    assert json_dict["device"] == "plantform"
    assert json_dict["action"] == "update"
    assert json_dict["command"] == "play"
    assert json_dict["schedule"]["12"] == 0.900