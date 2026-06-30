import sys
import os
import unittest
from unittest.mock import MagicMock, patch

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

from solar_processing.storage import SolarStorageManager

class TestSolarStorageManager(unittest.TestCase):

    def setUp(self):
        self.manager = SolarStorageManager()

        self.mock_lat = 43.446082
        self.mock_lon = -1.552687
        self.mock_date = "2026-06-30"
        self.mock_payload = {
            "values": [
                {"dtm": "2026-06-30 12:00:00", "GHI": 500.0, "temp": 22.5}
            ]
        }

    @patch("solar_processing.storage.mysql.connector.connect")
    def test_initialise_storage_success(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        self.manager.initialize_storage()

        mock_connect.assert_called_once()
        mock_cursor.execute.assert_called_once()

        executed_query = mock_cursor.execute.call_args[0][0]
        self.assertIn("CREATE TABLE IF NOT EXISTS pvnode_raw_forecasts", executed_query)

        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("solar_processing.storage.mysql.connector.connect")
    def test_store_raw_forecast_success(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        result = self.manager.store_raw_forecast(
            self.mock_date,
            self.mock_lat,
            self.mock_lon,
            self.mock_payload
        )

        self.assertTrue(result)
        mock_cursor.execute.assert_called_once()

        query, params = mock_cursor.execute.call_args[0]
        self.assertIn("INSERT INTO pvnode_raw_forecasts", query)
        self.assertIn("ON DUPLICATE KEY UPDATE", query)

        self.assertEqual(params[0], self.mock_date)
        self.assertEqual(params[1], self.mock_lat)
        self.assertEqual(params[2], self.mock_lon)

        import json
        self.assertEqual(params[3], json.dumps(self.mock_payload))

        mock_conn.commit.assert_called_once()

    @patch("solar_processing.storage.mysql.connector.connect")
    def test_retrieve_raw_forecast_success(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        import json
        mock_json_str = json.dumps(self.mock_payload)
        mock_cursor.fetchone.return_value = (mock_json_str,)

        retrieved_data = self.manager.retrieve_raw_forecast(self.mock_date)

        self.assertEqual(retrieved_data, self.mock_payload)
        mock_cursor.execute.asser_called_once_with(
            "SELECT raw_payload FROM pvnode_raw_forecasts WHERE forecast_data = %s",
            (self.mock_date,)
        )
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("solar_processing.storage.mysql.connector.connect")
    def test_database_error_handling(self, mock_connect):
        from mysql.connector import Error

        mock_connect.side_effect = Error("Connection refused")

        try:
            self.manager.initialize_storage()
        except Error:
            self.fail("initialize_storage raised an uncaught mysql.connector.Error")

        result_store = self.manager.store_raw_forecast(
            self.mock_date, self.mock_lat, self.mock_lon, self.mock_payload
        )
        self.assertFalse(result_store)

        result_retrieve = self.manager.retrieve_raw_forecast(self.mock_date)
        self.assertIsNone(result_retrieve)

if __name__ == "__main__":
    unittest.main()