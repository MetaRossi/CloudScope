import unittest
from datetime import datetime
from unittest.mock import patch

from src import lambda_api
from src.config import Config
from src.monitor import Monitor
from test.generators import availabilities_generator


class MonitorDetectNewRegions(unittest.TestCase):
    @patch('src.monitor.logging')
    @patch('src.monitor.os.system')
    @patch('src.monitor.print')
    @patch('src.config.datetime')
    def test_no_new_regions_voice_enabled(self, mock_datetime, mock_print, mock_system, mock_logging):
        fixed_now = datetime(2024, 1, 21, 14, 43, 26, 368333)
        mock_datetime.now.return_value = fixed_now

        known_regions = lambda_api.static_dict_of_known_regions()
        new_logged_regions = set()
        availabilities = availabilities_generator(5, region_list=list(known_regions))

        Monitor._detect_new_regions(availabilities, new_logged_regions, enable_voice_notifications=True)
        mock_logging.assert_not_called()
        mock_system.assert_not_called()
        mock_print.assert_not_called()

    @patch('src.monitor.logging')
    @patch('src.monitor.os.system')
    @patch('src.monitor.print')
    @patch('src.config.datetime')
    def test_new_regions_voice_enabled(self, mock_datetime, mock_print, mock_system, mock_logging):
        fixed_now = datetime(2024, 1, 21, 14, 43, 26, 368333)
        mock_datetime.now.return_value = fixed_now

        known_regions = lambda_api.static_dict_of_known_regions()
        new_logged_regions = set()
        new_region = 'us-foo-1'
        availabilities = availabilities_generator(5, region_list=list(known_regions))
        with_new_region = availabilities_generator(1, region_list=[new_region]).popitem()[1]
        availabilities[with_new_region.instance_type] = with_new_region

        Monitor._detect_new_regions(availabilities, new_logged_regions, enable_voice_notifications=True)
        mock_logging.critical.assert_called_with(f"New region observed: {new_region}")
        mock_system.assert_called_with('say "New Region Detected"')
        mock_print.assert_called_with(f"{Config.now_formatted_str(fixed_now)} - New region observed: {new_region}")
        self.assertIn(new_region, new_logged_regions)

    @patch('src.monitor.logging')
    @patch('src.monitor.os.system')
    @patch('src.monitor.print')
    @patch('src.config.datetime')
    def test_no_new_regions_voice_disabled(self, mock_datetime, mock_print, mock_system, mock_logging):
        fixed_now = datetime(2024, 1, 21, 14, 43, 26, 368333)
        mock_datetime.now.return_value = fixed_now

        known_regions = lambda_api.static_dict_of_known_regions()
        new_logged_regions = set()
        availabilities = availabilities_generator(5, region_list=list(known_regions))

        Monitor._detect_new_regions(availabilities, new_logged_regions, enable_voice_notifications=False)
        mock_logging.assert_not_called()
        mock_system.assert_not_called()
        mock_print.assert_not_called()

    @patch('src.monitor.logging')
    @patch('src.monitor.os.system')
    @patch('src.monitor.print')
    @patch('src.config.datetime')
    def test_new_regions_voice_disabled(self, mock_datetime, mock_print, mock_system, mock_logging):
        fixed_now = datetime(2024, 1, 21, 14, 43, 26, 368333)
        mock_datetime.now.return_value = fixed_now

        known_regions = lambda_api.static_dict_of_known_regions()
        new_logged_regions = set()
        new_region = 'us-foo-1'
        availabilities = availabilities_generator(5, region_list=list(known_regions))
        with_new_region = availabilities_generator(1, region_list=[new_region]).popitem()[1]
        availabilities[with_new_region.instance_type] = with_new_region

        Monitor._detect_new_regions(availabilities, new_logged_regions, enable_voice_notifications=False)
        mock_logging.critical.assert_called_with(f"New region observed: {new_region}")
        mock_system.assert_not_called()
        mock_print.assert_called_with(f"{Config.now_formatted_str(fixed_now)} - New region observed: {new_region}")
        self.assertIn(new_region, new_logged_regions)
