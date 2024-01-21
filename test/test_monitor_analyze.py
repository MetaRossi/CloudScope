import unittest
from datetime import datetime, timedelta
import random
from typing import Dict
from src.data_structures import InstanceType, InstanceAvailability
from src.monitor import Monitor


def random_instance_type() -> InstanceType:
    return InstanceType(
        name=f"Type_{random.randint(1, 10000)}",
        description="Random Description",
        region=f"Region_{random.randint(1, 10000)}"
    )


def random_availability() -> InstanceAvailability:
    instance_type = random_instance_type()
    start_time = datetime.now() - timedelta(days=random.randint(0, 5))
    last_time_available = start_time + timedelta(hours=random.randint(1, 24))
    return InstanceAvailability(
        instance_type=instance_type,
        start_time=start_time,
        last_time_available=last_time_available
    )


class TestAnalyzeAvailability(unittest.TestCase):
    def test_analyze_availability(self):
        for _ in range(20):
            all_instances = [random_availability() for _ in range(30)]

            fetch_time = datetime.now()
            current_availabilities = {inst.instance_type: inst for inst in random.sample(all_instances,
                                                                                         k=random.randint(1, 20))}
            fetched_availabilities = {inst.instance_type: inst for inst in random.sample(all_instances,
                                                                                         k=random.randint(1, 20))}

            # Manually calculate expected results
            expected_new = {inst_type: availability for inst_type, availability in fetched_availabilities.items()
                            if inst_type not in current_availabilities}
            expected_updated = {inst_type: current_availabilities[inst_type] for inst_type in current_availabilities
                                if inst_type in fetched_availabilities}
            for inst_type in expected_updated:
                expected_updated[inst_type].update(fetch_time)
            expected_removed = {inst_type: availability for inst_type, availability in current_availabilities.items()
                                if inst_type not in fetched_availabilities}

            # Call the function under test
            new_availabilities, updated_availabilities, removed_availabilities = Monitor._analyze_availability(
                fetch_time, fetched_availabilities, current_availabilities
            )

            # Assertions
            self.assertEqual(new_availabilities, expected_new)
            self.assertEqual(updated_availabilities, expected_updated)
            self.assertEqual(removed_availabilities, expected_removed)


class TestAnalyzeAvailabilityWithDistinctSets(unittest.TestCase):
    def test_analyze_availability_with_distinct_sets(self):
        # Generate unique InstanceTypes
        unique_instance_types = set()
        while len(unique_instance_types) < 1000:
            inst_type = random_instance_type()
            if inst_type not in unique_instance_types:
                unique_instance_types.add(inst_type)

        # Generate InstanceAvailability for each unique InstanceType
        all_instances = [InstanceAvailability(instance_type=inst_type, start_time=datetime.now())
                         for inst_type in unique_instance_types]

        # Split into three non-overlapping sets
        random.shuffle(all_instances)
        split1, split2, split3 = 30, 60, 100  # Example split points

        expected_new_instances = all_instances[:split1]
        to_update = all_instances[split1:split2]
        to_remove = all_instances[split2:split3]

        # Convert to dictionaries
        expected_new = {inst.instance_type: inst for inst in expected_new_instances}
        current_availabilities = {inst.instance_type: inst for inst in (to_update + to_remove)}

        # Update fetch time for 'to_update'
        fetch_time = datetime.now()
        for inst in to_update:
            inst.update(fetch_time)

        # Create fetched availabilities
        fetched_availabilities = {inst.instance_type: inst for inst in (expected_new_instances + to_update)}

        # Expected updated and removed
        expected_updated = {inst.instance_type: inst for inst in to_update}
        expected_removed = {inst.instance_type: inst for inst in to_remove}

        # Call the function under test
        new_availabilities, updated_availabilities, removed_availabilities = Monitor._analyze_availability(
            fetch_time, fetched_availabilities, current_availabilities
        )

        # Assertions
        # New availabilities
        self.assertEqual(len(new_availabilities), len(expected_new))
        for instance_type, availability in new_availabilities.items():
            self.assertIn(instance_type, expected_new)
            self.assertEqual(availability, expected_new[instance_type])

        # Updated availabilities
        self.assertEqual(len(updated_availabilities), len(expected_updated))
        for instance_type, availability in updated_availabilities.items():
            self.assertIn(instance_type, expected_updated)
            self.assertEqual(availability.last_time_available, fetch_time)
            self.assertEqual(availability, expected_updated[instance_type])

        # Removed availabilities
        self.assertEqual(len(removed_availabilities), len(expected_removed))
        for instance_type, availability in removed_availabilities.items():
            self.assertIn(instance_type, expected_removed)
            self.assertEqual(availability, expected_removed[instance_type])
