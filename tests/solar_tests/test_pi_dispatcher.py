import json
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from solar_processing.pi_dispatcher import PlantformMQTTDispatcher

@pytest.fixture
def sample_power_df():
    times = pd.date_range("2026-07-23 00:00", periods=24, freq="h")

    percentages = [0, 0, 0, 0, 0, 0, 0, 0,
        10, 25, 45, 75, 95, 90, 70, 50, 30, 10,
        0, 0, 0, 0, 0, 0,
    ]
    return pd.DataFrame({"power_percentage": percentages}, index=times)

@patch("paho.mqtt.client.Client")
def test_dispatch_success(mock_mqtt_client_cls, sample_power_df):
    mock_client = MagicMock()
    mock_mqtt_client_cls.return_value = mock_client

    mock_publish_result = MagicMock()
    mock_publish_result.rc = 0
    mock_client.publish.return_value = mock_publish_result

    dispatcher = PlantformMQTTDispatcher(
        broker_ip="127.0.0.1", port=1883, topic="prototypes/schedule"
    )

    success = dispatcher.dispatch(sample_power_df)

    assert success is True
    mock_client.connect.assert_called_once_with("127.0.0.1", 1883, keepalive=60)

    mock_client.publish.assert_called_once()
    args, kwargs = mock_client.publish.call_args

    published_topic = args[0]
    published_payload_str = args[1]

    assert published_topic == "prototypes/schedule"
    assert kwargs.get("retain") is True

    payload_dict = json.loads(published_payload_str)
    assert set(payload_dict.keys()) == {str(h) for h in range(8, 18)}
    assert payload_dict["12"] == 0.95
    assert mock_client.disconnect.called

@patch("paho.mqtt.client.Client")
def test_dispatch_mqtt_error_handling(mock_mqtt_client_cls, sample_power_df):
    mock_client = MagicMock()
    mock_mqtt_client_cls.return_value = mock_client

    mock_client.connect.side_effect = Exception("Connection Refused")

    dispatcher = PlantformMQTTDispatcher(broker_ip="192.168.1.99")
    success = dispatcher.dispatch(sample_power_df)

    assert success is False