import logging
from datetime import datetime
from unittest import TestCase
from unittest.mock import patch

from src.data_structures import InstanceAvailability, InstanceType
from src.output import log_instance_info


class LogInstanceInfoTests(TestCase):
    @patch.object(logging, 'info')
    def test_instance_unavailable_logs_correct_info(self, mock_logging_info):
        instance_type = InstanceType(name="t2.micro", region="us-west-2", description="Test instance")
        instance_availability = InstanceAvailability(instance_type=instance_type,
                                                     start_time=datetime(2022, 1, 1, 12, 0, 0),
                                                     last_time_available=datetime(2022, 1, 1, 13, 0, 0))
        log_instance_info(instance_availability, "Unavailable")
        mock_logging_info.assert_called_once()

    @patch.object(logging, 'info')
    def test_instance_available_logs_correct_info(self, mock_logging_info):
        instance_type = InstanceType(name="t2.micro", region="us-west-2", description="Test instance")
        instance_availability = InstanceAvailability(instance_type=instance_type,
                                                     start_time=datetime(2022, 1, 1, 12, 0, 0),
                                                     last_time_available=datetime(2022, 1, 1, 13, 0, 0))
        log_instance_info(instance_availability, "Available")
        mock_logging_info.assert_called_once()

    @patch.object(logging, 'error')
    def test_invalid_status_logs_error(self, mock_logging_error):
        instance_type = InstanceType(name="t2.micro", region="us-west-2", description="Test instance")
        instance_availability = InstanceAvailability(instance_type=instance_type,
                                                     start_time=datetime(2022, 1, 1, 12, 0, 0),
                                                     last_time_available=datetime(2022, 1, 1, 13, 0, 0))
        log_instance_info(instance_availability, "Invalid")
        mock_logging_error.assert_called_once()