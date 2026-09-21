import pytest
import pandas as pd
from solar_processing.packer_plant import PiInstructionPacker

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
    return [0.0, 0.0, 0.052, 0.065, 0.113, 0.266, 0.296, 0.855, 1.000, 0.954]

def test_to_protocol_string_formatting(sample_working_payload):
    protocol_str = PiInstructionPacker.to_protocol_string(
        sample_working_payload, command="play"
    )
    expected = "<plantform|update|0.000|0.000|0.052|0.065|0.113|0.266|0.296|0.855|1.000|0.954|play>"    
    assert protocol_str == expected

def test_to_protocol_string_padding_missing_hours():
    partial_map = {h: 0.0 for h in range(8, 18)}
    partial_map[10] = 0.500
    partial_map[15] = 1.000
    
    # Extract values in working-hour order
    working_payload = [partial_map[h] for h in range(8, 18)]
    protocol_str = PiInstructionPacker.to_protocol_string(working_payload)
    
    expected = "<plantform|update|0.000|0.000|0.500|0.000|0.000|0.000|0.000|1.000|0.000|0.000|play>"
    assert protocol_str == expected
    
def test_to_json_instruction_structure(sample_working_payload):
    json_dict = PiInstructionPacker.to_json_instruction(sample_working_payload)

    assert json_dict["device"] == "plantform1"
    assert json_dict["type"] == "action"
    assert json_dict["command"] == "update-play"
    assert len(json_dict["params"]) == 10
    

def test_integration_full_packing_pipeline():
    times = pd.date_range("2026-05-07 00:00", periods=24, freq="1h")
    powers = [0.0] * 8 + [10.0, 30.0, 50.0, 70.0, 90.0, 100.0, 80.0, 60.0, 40.0, 20.0] + [0.0] * 6
    df = pd.DataFrame({"power_percentage": powers}, index=times)

    full_day = PiInstructionPacker.to_hourly_payload(df)
    working_hours = PiInstructionPacker.slice_working_hours(full_day)
    json_dict = PiInstructionPacker.to_json_instruction(working_hours)

    assert len(working_hours) == 10
    assert json_dict["device"] == "plantform1"
    assert json_dict["type"] == "action"
    assert json_dict["command"] == "update-play"
