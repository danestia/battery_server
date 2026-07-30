import pytest
import pandas as pd
from solar_processing.interpreter import SolarDataInterpreter

@pytest.fixture
def mock_json_payload():
    return {
        "values": [
            {"dtm": "2026-05-07 12:00:00", "GHI": 600.0, "DHI": 60.0, "BNI": 500.0, "temp": 21.0, "spec_watts": 0.0},
            {"dtm": "2026-05-07 12:15:00", "GHI": 650.0, "DHI": 65.0, "BNI": 520.0, "temp": 21.5, "spec_watts": 0.0}
        ]
    }

def test_dataframe_parsing_structure(mock_json_payload):
    interpreter = SolarDataInterpreter(lat=43.446, lon=-1.552)
    df = interpreter.turn_json_to_dataframe(mock_json_payload)
    processed_df = interpreter.process_solar_metrics(df, tilt=27.0, azimuth=180.0)

    assert 'POA' in processed_df.columns
    assert 'cell_temp' in processed_df.columns
    assert 'power_percentage' in processed_df.columns
    assert processed_df['power_percentage'].max() <= 100.0