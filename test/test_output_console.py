import datetime
import random
import unittest
from io import StringIO
from unittest.mock import patch

from helpers import helper_assert_and_print
from data_structures.instance import InstanceAvailability, InstanceType
from core.console import render_to_console


class TestRenderToConsole(unittest.TestCase):
    def setUp(self):
        self.mock_start_time = datetime.datetime(2024, 1, 1, 0, 0, 0)
        self.mock_session_start_time = datetime.datetime(2024, 1, 1, 1, 0, 0)
        self.mock_session_end_time = datetime.datetime(2024, 1, 1, 2, 0, 0)
        self.mock_instance_type = InstanceType(
            name="test-instance",
            description="A test instance",
            region="us-west-1"
        )
        self.mock_instance = InstanceAvailability(
            instance_type=self.mock_instance_type,
            start_time=self.mock_start_time,
            last_time_available=self.mock_start_time
        )

    @patch('sys.stdout', new_callable=StringIO)
    def test_available_instances(self, mock_stdout):
        render_to_console(
            True,
            {self.mock_instance.instance_type.name},
            self.mock_session_start_time,
            None,
            self.mock_start_time,
        )
        self.assertIn("Available Instances", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_no_instances_no_last_available(self, mock_stdout):
        render_to_console(
            False,
            set(),
            None,
            None,
            self.mock_start_time,
        )
        self.assertIn("No instances available", mock_stdout.getvalue())
        self.assertIn("since start", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_no_instances_with_last_available(self, mock_stdout):
        render_to_console(
            False,
            set(),
            None,
            self.mock_session_end_time,
            self.mock_start_time,
        )
        self.assertIn("No instances available", mock_stdout.getvalue())
        self.assertIn("since last available", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_long_duration_since_last_available(self, mock_stdout):
        long_last_available_time = datetime.datetime(2023, 1, 1, 1, 0, 0)
        render_to_console(
            False,
            set(),
            None,
            long_last_available_time,
            self.mock_start_time,
        )
        self.assertIn("No instances available", mock_stdout.getvalue())
        self.assertIn("since last available", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_multiple_available_instances(self, mock_stdout):
        mock_instance2_type = InstanceType(
            name="test-instance-2",
            description="Another test instance",
            region="us-east-1"
        )
        mock_instance2 = InstanceAvailability(
            instance_type=mock_instance2_type,
            start_time=self.mock_start_time,
            last_time_available=self.mock_start_time
        )
        render_to_console(
            True,
            {self.mock_instance.instance_type.name, mock_instance2.instance_type.name},
            self.mock_session_start_time,
            None,
            self.mock_start_time,
        )
        self.assertIn("Available Instances", mock_stdout.getvalue())
        self.assertIn("test-instance", mock_stdout.getvalue())
        self.assertIn("test-instance-2", mock_stdout.getvalue())

    @patch('src.output_console.datetime')
    @patch('sys.stdout', new_callable=StringIO)
    def test_no_availability_five_messages(self, mock_stdout, mock_datetime):
        mock_times = [self.mock_start_time + datetime.timedelta(minutes=5 * i) for i in range(5)]
        mock_datetime.now.side_effect = mock_times

        start_time_str = f"{self.mock_start_time:%Y-%m-%d %H:%M:%S.%f}"
        for i in range(5):
            current_time = mock_times[i]
            duration_since_start = current_time - self.mock_start_time
            expected_output = (f"\r{current_time:%Y-%m-%d %H:%M:%S.%f} - "
                               f"No instances available. "
                               f"Started at: {start_time_str}, "
                               f"Duration since start: {duration_since_start}")
            render_to_console(
                False,
                set(),
                None,
                None,
                self.mock_start_time,
            )

            # Check the buffer content after each message
            helper_assert_and_print(expected_output, i, mock_stdout)

    @patch('src.output_console.datetime')
    @patch('sys.stdout', new_callable=StringIO)
    def test_one_availability_five_messages(self, mock_stdout, mock_datetime):
        mock_times = [self.mock_start_time + datetime.timedelta(minutes=5 * i) for i in range(5)]
        mock_datetime.now.side_effect = mock_times

        for i in range(5):
            current_time = mock_times[i]
            duration_since_start = current_time - self.mock_start_time
            expected_output = (f"\r{current_time:%Y-%m-%d %H:%M:%S.%f} - "
                               f"Available Instances: {{'test-instance'}}, "
                               f"Availability Duration: {duration_since_start}")
            render_to_console(
                True,
                {self.mock_instance.instance_type.name},
                self.mock_start_time,
                None,
                self.mock_start_time,
            )

            # Check the buffer content after each message
            helper_assert_and_print(expected_output, i, mock_stdout)


class TestRenderToConsoleSwitching(unittest.TestCase):
    def setUp(self):
        self.mock_start_time = datetime.datetime(2024, 1, 1, 0, 0, 0)
        self.mock_instance_type = InstanceType(
            name="test-instance",
            description="A test instance",
            region="us-west-1"
        )
        self.mock_instance = InstanceAvailability(
            instance_type=self.mock_instance_type,
            start_time=self.mock_start_time,
            last_time_available=self.mock_start_time
        )

    @patch('src.output_console.datetime')
    @patch('sys.stdout', new_callable=StringIO)
    def test_switching_availability_three_times(self, mock_stdout, mock_datetime):
        mock_times = [datetime.datetime(2024, 1, 1, 1, minute, 0) for minute in range(12)]
        mock_datetime.now.side_effect = mock_times

        last_available_time = None
        for i in range(6):
            is_available = i % 2 == 0
            current_time = mock_times[i]
            if is_available:
                instances = [self.mock_instance]
                last_available_time = current_time
                expected_output = (f"\r{current_time:%Y-%m-%d %H:%M:%S.%f} - "
                                   f"Available Instances: {{'test-instance'}}, "
                                   f"Availability Duration: {current_time - last_available_time}")
                render_to_console(
                    True,
                    set([i.instance_type.name for i in instances]),
                    last_available_time,
                    None,
                    self.mock_start_time,
                )
            else:
                duration_since_reference = current_time - (last_available_time if last_available_time is not None
                                                           else self.mock_start_time)
                duration_message = "since last available" if last_available_time is not None else "since start"
                expected_output = (f"\r{current_time:%Y-%m-%d %H:%M:%S.%f} - "
                                   f"No instances available. "
                                   f"Last available at: {last_available_time:%Y-%m-%d %H:%M:%S.%f}, "
                                   f"Duration {duration_message}: {duration_since_reference}")
                render_to_console(
                    False,
                    set(),
                    None,
                    last_available_time,
                    self.mock_start_time,
                )

            helper_assert_and_print(expected_output, i, mock_stdout)


class TestRenderToConsoleSwitchingStartNotAvailable(unittest.TestCase):
    def setUp(self):
        self.mock_start_time = datetime.datetime(2024, 1, 1, 0, 0, 0)
        self.mock_instance_type = InstanceType(
            name="test-instance",
            description="A test instance",
            region="us-west-1"
        )
        self.mock_instance = InstanceAvailability(
            instance_type=self.mock_instance_type,
            start_time=self.mock_start_time,
            last_time_available=self.mock_start_time
        )

    @patch('src.output_console.datetime')
    @patch('sys.stdout', new_callable=StringIO)
    def test_switching_start_not_available(self, mock_stdout, mock_datetime):
        mock_times = [datetime.datetime(2024, 1, 1, 1, minute, 0) for minute in range(12)]
        mock_datetime.now.side_effect = mock_times

        start_time_str = f"{self.mock_start_time:%Y-%m-%d %H:%M:%S.%f}"
        last_available_time = None
        for i in range(6):
            is_available = i % 2 != 0  # Start with not available
            current_time = mock_times[i]
            if is_available:
                instances = [self.mock_instance]
                last_available_time = current_time
                expected_output = (f"\r{current_time:%Y-%m-%d %H:%M:%S.%f} - "
                                   f"Available Instances: {{'test-instance'}}, "
                                   f"Availability Duration: {current_time - last_available_time}")
                render_to_console(
                    True,
                    set([i.instance_type.name for i in instances]),
                    last_available_time,
                    None,
                    self.mock_start_time,
                )
            else:
                last_message = "Started at" if last_available_time is None else "Last available at"
                duration_since_reference = current_time - (
                    self.mock_start_time if last_available_time is None else last_available_time)
                duration_message = "since start" if last_available_time is None else "since last available"
                last_available_time_str = f"{last_available_time:%Y-%m-%d %H:%M:%S.%f}" \
                    if last_available_time is not None else start_time_str
                expected_output = (f"\r{current_time:%Y-%m-%d %H:%M:%S.%f} - No instances available. "
                                   f"{last_message}: {last_available_time_str}, "
                                   f"Duration {duration_message}: {duration_since_reference}")
                render_to_console(
                    False,
                    set(),
                    None,
                    last_available_time,
                    self.mock_start_time,
                )

            helper_assert_and_print(expected_output, i, mock_stdout)


class TestRenderToConsoleNotAvailableUpdates(unittest.TestCase):
    def setUp(self):
        self.mock_start_time = datetime.datetime(2024, 1, 1, 0, 0, 0)

    @patch('src.output_console.datetime')
    @patch('sys.stdout', new_callable=StringIO)
    def test_not_available_updates(self, mock_stdout, mock_datetime):
        mock_times = [self.mock_start_time + datetime.timedelta(minutes=10 * i) for i in range(10)]
        mock_datetime.now.side_effect = mock_times

        start_time_str = f"{self.mock_start_time:%Y-%m-%d %H:%M:%S.%f}"
        for i in range(10):
            current_time = mock_times[i]
            duration_since_start = current_time - self.mock_start_time
            expected_output = (f"\r{current_time:%Y-%m-%d %H:%M:%S.%f} - "
                               f"No instances available. "
                               f"Started at: {start_time_str}, "
                               f"Duration since start: {duration_since_start}")
            render_to_console(
                False,
                set(),
                None,
                None,
                self.mock_start_time,
            )

            helper_assert_and_print(expected_output, i, mock_stdout)


class TestRenderToConsoleAvailableRandomUpdates(unittest.TestCase):
    def setUp(self):
        self.mock_start_time = datetime.datetime(2024, 1, 1, 0, 0, 0)
        self.instances = {
            "instance1": InstanceAvailability(
                instance_type=InstanceType(name="instance1", description="Instance type 1", region="us-west-1"),
                start_time=self.mock_start_time,
                last_time_available=self.mock_start_time
            ),
            "instance2": InstanceAvailability(
                instance_type=InstanceType(name="instance2", description="Instance type 2", region="us-east-1"),
                start_time=self.mock_start_time,
                last_time_available=self.mock_start_time
            ),
            "instance3": InstanceAvailability(
                instance_type=InstanceType(name="instance3", description="Instance type 3", region="eu-central-1"),
                start_time=self.mock_start_time,
                last_time_available=self.mock_start_time
            )
        }

    @patch('src.output_console.datetime')
    @patch('sys.stdout', new_callable=StringIO)
    def test_available_random_updates(self, mock_stdout, mock_datetime):
        mock_times = [self.mock_start_time + datetime.timedelta(minutes=5 * i) for i in range(20)]
        mock_datetime.now.side_effect = mock_times

        last_available_time = self.mock_start_time
        for i in range(20):
            current_time = mock_times[i]
            # Randomly choose one or more instances
            available_instances = random.sample(list(self.instances.values()), random.randint(1, 3))
            duration_since_last_available = current_time - last_available_time
            instance_names = set([instance.instance_type.name for instance in available_instances])
            expected_output = (f"\r{current_time:%Y-%m-%d %H:%M:%S.%f} - "
                               f"Available Instances: {instance_names}, "
                               f"Availability Duration: {duration_since_last_available}")
            render_to_console(
                True,
                instance_names,
                last_available_time,
                None,
                self.mock_start_time,
            )

            # Check the buffer content after each switch
            helper_assert_and_print(expected_output, i, mock_stdout)

