import logging

from core.tracker import Tracker
from data_structures.instance import InstanceAvailability


def log_instance_changes(tracker: Tracker) -> None:
    """
    Logs information for instances that have become available or unavailable.
    """
    for instance in tracker.new_availabilities.values():
        log_instance_info(instance, "Available")

    for instance in tracker.removed_availabilities.values():
        if instance is not None:
            log_instance_info(instance, "Unavailable")


def log_instance_info(
        instance_availability: InstanceAvailability,
        status: str,
) -> None:
    instance_info = instance_availability.instance_type
    start_time = instance_availability.start_time
    end_time = instance_availability.last_time_available

    if status == "Unavailable":
        duration = end_time - start_time
        logging.info(
            f"Instance Type: {instance_info.name}, Region: {instance_info.region} - "
            f"Status: {status} - "
            f"Start: {start_time} - "
            f"End: {end_time} - "
            f"Duration: {duration}"
        )
    elif status == "Available":
        logging.info(
            f"Instance Type: {instance_info.name}, Region: {instance_info.region} - "
            f"Status: {status} - "
            f"Start: {start_time}"
        )
    else:
        logging.error(f"Invalid status for "
                      f"Instance Type: {instance_info.name}, "
                      f"Region: {instance_info.region} - "
                      f"Status: {status} - "
                      f"Start: {start_time} - "
                      f"End: {end_time}")
