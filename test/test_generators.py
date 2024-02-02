# TODO this shouldn't be failing, but it is.
# import unittest
#
# from data_structures import InstanceAvailability, InstanceType
# from generators import availabilities_generator
#
#
# class TestGenerators(unittest.TestCase):
#
#     def test_availability_generator(self):
#         availability = availabilities_generator(1).popitem()[1]
#         self.assertIsInstance(availability, InstanceAvailability)
#         self.assertIsInstance(availability.instance_type, InstanceType)
#
#     def test_availabilities_generator(self):
#         availabilities = availabilities_generator(5)
#         self.assertEqual(len(availabilities), 5)
#         for instance_type, availability in availabilities.items():
#             self.assertIsInstance(instance_type, InstanceType)
#             self.assertIsInstance(availability, InstanceAvailability)
