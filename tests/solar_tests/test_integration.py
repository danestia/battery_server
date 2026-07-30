import os
import json
import pytest
import pandas as pd
from solar_processing.interpreter import SolarDataInterpreter
from solar_processing.packer import PiInstructionPacker

def test_production_pipeline_with_real_json():
    fixture_path = os.path.join(
        os.path.dirname(__file__), "fixtures", "pvnode_real_payload.json"
    )

    with open(fixture_path, "r") as f:
        real_json_data = json.load(f)

    interpreter = SolarDataInterpreter(lat=43.446082, lon=-1.552687)

    df = interpreter.turn_json_to_dataframe(real_json_data)

    assert os.path.exists(fixture_path), "Fixture file missing"
    assert not df.empty, "Interpreter returned an empty DataFrame from real JSON"
    assert 'GHI' in df.columns, "Expected 'GHI' column in processed DataFrame"
    assert isinstance(df.index, pd.DatetimeIndex), "DataFrame index must be a DatetimeIndex"

    daily_subset = df.iloc[:96, :]
    calculated_df = interpreter.process_solar_metrics(daily_subset, tilt=27.0, azimuth=180.0)

    assert not calculated_df.empty, "Physics engine failed to calculate metrics"
    assert 'power_percentage' in calculated_df.columns, "Missing 'power_percentage' output"

    payload = PiInstructionPacker.to_hourly_payload(calculated_df)
    #for visible payload
    print("\n--- COMPILED PI PAYLOAD ---")
    import pprint
    pprint.pprint(payload)
    print("---------------------------")

    assert isinstance(payload, dict), "Packer must output a dictionary"
    assert len(payload) == 24, "Packer must produce exactly 24 hourly bins"
    assert all(0 <= val <= 100 for val in payload.values()), "Power percentages must be between 0 and 100" 