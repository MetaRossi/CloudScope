import unittest
from datetime import datetime
from datetime import timedelta

from data_structures.instance import InstanceType, InstanceAvailability
from generators import availabilities_generator
from core.tracker import Tracker


class TestTracker(unittest.TestCase):

    def setUp(self) -> None:
        self.tracker = Tracker(start_time=datetime.now())

    def test_initialization(self):
        self.assertFalse(self.tracker.has_ever_observed_instances)
        self.assertIsNone(self.tracker.last_fetch_time)
        self.assertEqual(len(self.tracker.current_availabilities), 0)

    def test_is_first_poll(self):
        self.assertTrue(self.tracker.is_first_poll())
        self.tracker.last_fetch_time = datetime.now()
        self.assertFalse(self.tracker.is_first_poll())

    def test_is_session_active(self):
        self.assertFalse(self.tracker.is_session_active())
        self.tracker.current_availabilities = availabilities_generator(5)
        self.assertTrue(self.tracker.is_session_active())

    def test_get_current_names(self):
        self.tracker.current_availabilities = availabilities_generator(5)
        self.assertEqual(len(self.tracker.get_current_names()), 5)

    def test_has_current_availabilities(self):
        self.assertFalse(self.tracker.has_current_availabilities())
        self.tracker.current_availabilities = availabilities_generator(1)
        self.assertTrue(self.tracker.has_current_availabilities())

    def test_update_method(self):
        fetched_availabilities = availabilities_generator(3)
        self.tracker.update(fetched_availabilities, datetime.now())
        self.assertEqual(len(self.tracker.new_availabilities), 3)
        self.assertTrue(self.tracker.has_ever_observed_instances)

    # Similar tests for get_new_names, get_updated_names, get_removed_names
    # Similar tests for has_new_availabilities, has_updated_availabilities, has_removed_availabilities


class TestTrackerWithUpdate(unittest.TestCase):

    def setUp(self) -> None:
        self.tracker = Tracker(start_time=datetime.now())

    def test_initialization_with_update(self):
        fetched_availabilities = availabilities_generator(0)
        self.tracker.update(fetched_availabilities, datetime.now())
        self.assertFalse(self.tracker.has_ever_observed_instances)
        self.assertIsNotNone(self.tracker.last_fetch_time)

    def test_is_first_poll_with_update(self):
        fetched_availabilities = availabilities_generator(0)
        self.tracker.update(fetched_availabilities, datetime.now())
        self.assertFalse(self.tracker.is_first_poll())

    def test_is_session_active_with_update(self):
        fetched_availabilities = availabilities_generator(0)
        self.tracker.update(fetched_availabilities, datetime.now())
        self.assertFalse(self.tracker.is_session_active())
        fetched_availabilities = availabilities_generator(5)
        self.tracker.update(fetched_availabilities, datetime.now())
        self.assertTrue(self.tracker.is_session_active())

    def test_get_current_names_with_update(self):
        fetched_availabilities = availabilities_generator(5)
        self.tracker.update(fetched_availabilities, datetime.now())
        self.assertEqual(len(self.tracker.get_current_names()), 5)

    def test_has_current_availabilities_with_update(self):
        fetched_availabilities = availabilities_generator(0)
        self.tracker.update(fetched_availabilities, datetime.now())
        self.assertFalse(self.tracker.has_current_availabilities())
        fetched_availabilities = availabilities_generator(1)
        self.tracker.update(fetched_availabilities, datetime.now())
        self.assertTrue(self.tracker.has_current_availabilities())

    def test_get_new_names_with_update(self):
        # Initially, no new availabilities
        fetched_availabilities = availabilities_generator(0)
        self.tracker.update(fetched_availabilities, datetime.now())
        self.assertEqual(len(self.tracker.get_new_names()), 0)

        # Add new availabilities
        new_availabilities = availabilities_generator(3)
        self.tracker.update(new_availabilities, datetime.now())
        self.assertEqual(len(self.tracker.get_new_names()), 3)

    def test_get_updated_names_with_update(self):
        # Setup initial state
        initial_availabilities = availabilities_generator(3)
        now_1 = datetime.now()
        self.tracker.update(initial_availabilities, now_1)

        # Modify some availabilities to simulate an update
        updated_availabilities: dict = dict(list(initial_availabilities.items())[0:2])
        now_2 = datetime.now()
        for key in updated_availabilities.keys():
            # Make a copy
            copy = updated_availabilities[key].model_copy(deep=True)
            copy.update(now_2)
            updated_availabilities[key] = copy

        # Update the tracker
        self.tracker.update(updated_availabilities, now_2)

        self.assertEqual(len(self.tracker.get_updated_names()), len(updated_availabilities))

    def test_get_removed_names_with_update(self):
        # Setup initial state
        initial_availabilities = availabilities_generator(3)
        self.tracker.update(initial_availabilities, datetime.now())

        # Update with fewer availabilities to simulate removal
        removed_availabilities = dict(list(initial_availabilities.items())[0:1])
        self.tracker.update(removed_availabilities, datetime.now())
        self.assertEqual(len(self.tracker.get_removed_names()), 2)  # 3 initial - 1 remaining = 2 removed

    def test_has_new_availabilities_with_update(self):
        # Initially, no new availabilities
        fetched_availabilities = availabilities_generator(0)
        self.tracker.update(fetched_availabilities, datetime.now())
        self.assertFalse(self.tracker.has_new_availabilities())

        # Add new availabilities
        new_availabilities = availabilities_generator(2)
        self.tracker.update(new_availabilities, datetime.now())
        self.assertTrue(self.tracker.has_new_availabilities())

    def test_has_updated_availabilities_with_update(self):
        # Setup initial state
        initial_availabilities = availabilities_generator(3)
        self.tracker.update(initial_availabilities, datetime.now())

        # Modify some availabilities to simulate an update
        updated_availabilities: dict = dict(list(initial_availabilities.items())[0:2])
        for key in updated_availabilities.keys():
            copy = updated_availabilities[key].model_copy(deep=True)
            copy.last_time_available = datetime.now()
            updated_availabilities[key] = copy

        self.tracker.update(updated_availabilities, datetime.now())
        self.assertTrue(self.tracker.has_updated_availabilities())

    def test_has_removed_availabilities_with_update(self):
        # Setup initial state
        initial_availabilities = availabilities_generator(3)
        self.tracker.update(initial_availabilities, datetime.now())

        # Update with fewer availabilities to simulate removal
        removed_availabilities = dict(list(initial_availabilities.items())[0:1])
        self.tracker.update(removed_availabilities, datetime.now())
        self.assertTrue(self.tracker.has_removed_availabilities())


class TestInstanceTypeAndAvailability(unittest.TestCase):

    def test_instance_type_initialization(self):
        instance_type = InstanceType(name="Type1", description="Description1", region="Region1")
        self.assertEqual(instance_type.name, "Type1")
        self.assertEqual(instance_type.description, "Description1")
        self.assertEqual(instance_type.region, "Region1")

    def test_instance_availability_methods(self):
        instance_type = InstanceType(name="Type1", description="Description1", region="Region1")
        now = datetime.now()
        availability = InstanceAvailability(instance_type=instance_type, start_time=now, last_time_available=now)
        self.assertEqual(availability.instance_type, instance_type)
        self.assertEqual(availability.get_duration(), timedelta(0))
        # More assertions for methods like update, get_duration, etc.

