import datetime
import random
import unittest
from io import StringIO
from unittest.mock import patch

from src.data_structures.instance_type import InstanceType
from src.data_structures.region import Region
from src.output import render_to_console


class TestRenderToConsole(unittest.TestCase):
    def setUp(self):
        self.mock_start_time = datetime.datetime(2024, 1, 1, 0, 0, 0)
        self.mock_last_available_time = datetime.datetime(2024, 1, 1, 1, 0, 0)
        self.mock_instance = InstanceType(
            name="test-instance",
            description="A test instance",
            price_cents_per_hour=100,
            specs={"CPU": "4 cores", "Memory": "16GB"},
            regions_with_capacity_available=[Region(name="us-west-1", description="US West Region")]
        )

    @patch('sys.stdout', new_callable=StringIO)
    def test_available_instances(self, mock_stdout):
        render_to_console(
            True,
            {"test-instance": self.mock_instance},
            self.mock_last_available_time,
            self.mock_start_time,
        )
        self.assertIn("Available Instances", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_no_instances_no_last_available(self, mock_stdout):
        render_to_console(
            False,
            {},
            None,
            self.mock_start_time,
        )
        self.assertIn("No instances available", mock_stdout.getvalue())
        self.assertIn("since start", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_no_instances_with_last_available(self, mock_stdout):
        render_to_console(
            False,
            {},
            self.mock_last_available_time,
            self.mock_start_time,
        )
        self.assertIn("No instances available", mock_stdout.getvalue())
        self.assertIn("since last available", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_long_duration_since_last_available(self, mock_stdout):
        long_last_available_time = datetime.datetime(2023, 1, 1, 1, 0, 0)
        render_to_console(
            False,
            {},
            long_last_available_time,
            self.mock_start_time,
        )
        self.assertIn("No instances available", mock_stdout.getvalue())
        self.assertIn("since last available", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_multiple_available_instances(self, mock_stdout):
        mock_instance2 = InstanceType(
            name="test-instance-2",
            description="Another test instance",
            price_cents_per_hour=200,
            specs={"CPU": "8 cores", "Memory": "32GB"},
            regions_with_capacity_available=[Region(name="us-east-1", description="US East Region")]
        )
        render_to_console(
            True,
            {"test-instance": self.mock_instance, "test-instance-2": mock_instance2},
            self.mock_last_available_time,
            self.mock_start_time,
        )
        self.assertIn("Available Instances", mock_stdout.getvalue())
        self.assertIn("test-instance", mock_stdout.getvalue())
        self.assertIn("test-instance-2", mock_stdout.getvalue())


class TestRenderToConsoleSwitching(unittest.TestCase):
    def setUp(self):
        self.mock_start_time = datetime.datetime(2024, 1, 1, 0, 0, 0)
        self.mock_instance = InstanceType(
            name="test-instance",
            description="A test instance",
            price_cents_per_hour=100,
            specs={"CPU": "4 cores", "Memory": "16GB"},
            regions_with_capacity_available=[Region(name="us-west-1", description="US West Region")]
        )

    @patch('src.output.datetime')
    @patch('sys.stdout', new_callable=StringIO)
    def test_switching_availability_three_times(self, mock_stdout, mock_datetime):
        mock_times = [datetime.datetime(2024, 1, 1, 1, minute, 0) for minute in range(12)]
        mock_datetime.now.side_effect = mock_times

        buffer = StringIO()
        last_available_time = None
        for i in range(6):
            is_available = i % 2 == 0
            current_time = mock_times[i]
            if is_available:
                instances = {"test-instance": self.mock_instance}
                last_available_time = current_time
                expected_output = (f"\r{current_time:%Y-%m-%d %H:%M:%S.%f} - "
                                   f"Available Instances: ['test-instance'], "
                                   f"Availability Duration: {current_time - last_available_time}")
                render_to_console(
                    True,
                    instances,
                    last_available_time,
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
                    {},
                    last_available_time,
                    self.mock_start_time,
                )

            # Check the buffer content after each switch
            buffer_lines = mock_stdout.getvalue().split('\r')
            if len(buffer_lines) > 1:
                # Get the last line; the first one is empty
                actual_output = buffer_lines[-1].strip()
                self.assertEqual(actual_output, expected_output.strip('\r'))

            # Print the buffer content after each switch for inspection
            print(f"After switch {i + 1}:\n{buffer.getvalue()}\n")


class TestRenderToConsoleSwitchingStartNotAvailable(unittest.TestCase):
    def setUp(self):
        self.mock_start_time = datetime.datetime(2024, 1, 1, 0, 0, 0)
        self.mock_instance = InstanceType(
            name="test-instance",
            description="A test instance",
            price_cents_per_hour=100,
            specs={"CPU": "4 cores", "Memory": "16GB"},
            regions_with_capacity_available=[Region(name="us-west-1", description="US West Region")]
        )

    @patch('src.output.datetime')
    @patch('sys.stdout', new_callable=StringIO)
    def test_switching_start_not_available(self, mock_stdout, mock_datetime):
        mock_times = [datetime.datetime(2024, 1, 1, 1, minute, 0) for minute in range(12)]
        mock_datetime.now.side_effect = mock_times

        buffer = StringIO()
        start_time_str = f"{self.mock_start_time:%Y-%m-%d %H:%M:%S.%f}"
        last_available_time = None
        for i in range(6):
            is_available = i % 2 != 0  # Start with not available
            current_time = mock_times[i]
            if is_available:
                instances = {"test-instance": self.mock_instance}
                last_available_time = current_time
                expected_output = (f"\r{current_time:%Y-%m-%d %H:%M:%S.%f} - "
                                   f"Available Instances: ['test-instance'], "
                                   f"Availability Duration: {current_time - last_available_time}")
                render_to_console(
                    True,
                    instances,
                    last_available_time,
                    self.mock_start_time,
                )
            else:
                duration_since_reference = current_time - (self.mock_start_time if last_available_time is None else last_available_time)
                duration_message = "since start" if last_available_time is None else "since last available"
                last_available_time_str = f"{last_available_time:%Y-%m-%d %H:%M:%S.%f}" if last_available_time is not None else start_time_str
                expected_output = f"\r{current_time:%Y-%m-%d %H:%M:%S.%f} - No instances available. Last available at: {last_available_time_str}, Duration {duration_message}: {duration_since_reference}"
                render_to_console(
                    False,
                    {},
                    last_available_time,
                    self.mock_start_time,
                )

            # Check the buffer content after each switch
            buffer_lines = mock_stdout.getvalue().split('\r')
            if len(buffer_lines) > 1:
                # Get the last line; the first one is empty
                actual_output = buffer_lines[-1].strip()
                self.assertEqual(actual_output, expected_output.strip('\r'))

            # Print the buffer content after each switch for inspection
            print(f"After switch {i + 1}:\n{buffer.getvalue()}\n")



class TestRenderToConsoleNotAvailableUpdates(unittest.TestCase):
    def setUp(self):
        self.mock_start_time = datetime.datetime(2024, 1, 1, 0, 0, 0)
        self.mock_instance = InstanceType(
            name="test-instance",
            description="A test instance",
            price_cents_per_hour=100,
            specs={"CPU": "4 cores", "Memory": "16GB"},
            regions_with_capacity_available=[Region(name="us-west-1", description="US West Region")]
        )

    @patch('src.output.datetime')
    @patch('sys.stdout', new_callable=StringIO)
    def test_not_available_updates(self, mock_stdout, mock_datetime):
        # Create mock times with correct hour and minute values
        mock_times = [self.mock_start_time + datetime.timedelta(minutes=10 * i) for i in range(10)]
        mock_datetime.now.side_effect = mock_times

        buffer = StringIO()
        start_time_str = f"{self.mock_start_time:%Y-%m-%d %H:%M:%S.%f}"
        for i in range(10):
            current_time = mock_times[i]
            duration_since_start = current_time - self.mock_start_time
            expected_output = (f"\r{current_time:%Y-%m-%d %H:%M:%S.%f} - "
                               f"No instances available. "
                               f"Last available at: {start_time_str}, "
                               f"Duration since start: {duration_since_start}")
            render_to_console(
                False,
                {},
                None,
                self.mock_start_time,
            )

            # Check the buffer content after each update
            buffer_lines = mock_stdout.getvalue().split('\r')
            if len(buffer_lines) > 1:
                # Get the last line; the first one is empty
                actual_output = buffer_lines[-1].strip()
                self.assertEqual(actual_output, expected_output.strip('\r'))

            # Print the buffer content after each update for inspection
            print(f"After update {i + 1}:\n{buffer.getvalue()}\n")


class TestRenderToConsoleAvailableRandomUpdates(unittest.TestCase):
    def setUp(self):
        self.mock_start_time = datetime.datetime(2024, 1, 1, 0, 0, 0)
        self.instances = {
            "instance1": InstanceType(
                name="instance1",
                description="Instance type 1",
                price_cents_per_hour=100,
                specs={"CPU": "4 cores", "Memory": "8GB"},
                regions_with_capacity_available=[Region(name="us-west-1", description="US West Region")]
            ),
            "instance2": InstanceType(
                name="instance2",
                description="Instance type 2",
                price_cents_per_hour=200,
                specs={"CPU": "8 cores", "Memory": "16GB"},
                regions_with_capacity_available=[Region(name="us-east-1", description="US East Region")]
            ),
            "instance3": InstanceType(
                name="instance3",
                description="Instance type 3",
                price_cents_per_hour=300,
                specs={"CPU": "16 cores", "Memory": "32GB"},
                regions_with_capacity_available=[Region(name="eu-central-1", description="EU Central Region")]
            )
        }

    @patch('src.output.datetime')
    @patch('sys.stdout', new_callable=StringIO)
    def test_available_random_updates(self, mock_stdout, mock_datetime):
        mock_times = [self.mock_start_time + datetime.timedelta(minutes=5 * i) for i in range(20)]
        mock_datetime.now.side_effect = mock_times

        buffer = StringIO()
        last_available_time = self.mock_start_time
        for i in range(20):
            current_time = mock_times[i]
            # Randomly choose one or more instances
            available_instances = random.sample(list(self.instances.values()), random.randint(1, 3))
            instances_dict = {instance.name: instance for instance in available_instances}
            duration_since_last_available = current_time - last_available_time
            instance_names = [instance.name for instance in available_instances]
            expected_output = (f"\r{current_time:%Y-%m-%d %H:%M:%S.%f} - "
                               f"Available Instances: {instance_names}, "
                               f"Availability Duration: {duration_since_last_available}")
            render_to_console(
                True,
                instances_dict,
                last_available_time,
                self.mock_start_time,
            )

            # Check the buffer content after each update
            buffer_lines = mock_stdout.getvalue().split('\r')
            if len(buffer_lines) > 1:
                # Get the last line; the first one is empty
                actual_output = buffer_lines[-1].strip()
                self.assertEqual(actual_output, expected_output.strip('\r'))

            # Print the buffer content after each update for inspection
            print(f"After update {i + 1}:\n{buffer.getvalue()}\n")
