from datetime import datetime
from typing import Optional, List
import logging

from src.data_structures import InstanceAvailability


def log_instance_info(
    instance_availability: InstanceAvailability,
    status: str
) -> None:
    end_time = datetime.now()

    instance_info = instance_availability.instance_info
    start_time = instance_availability.start_time

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
        duration = end_time - start_time
        logging.info(
            f"Instance Type: {instance_info.name}, Region: {instance_info.region} - "
            f"Status: {status} - "
            f"Start: {start_time} - "
            f"Duration: {duration}"
        )
    else:
        logging.error(f"Invalid status for "
                      f"Instance Type: {instance_info.name}, "
                      f"Region: {instance_info.region} - "
                      f"Status: {status} - "
                      f"Start: {start_time} - "
                      f"End: {end_time}")


def render_to_console(
    is_available: bool,
    instances: List[InstanceAvailability],
    last_available_time: Optional[datetime],
    start_time: datetime,
) -> None:
    current_time = datetime.now()
    if is_available:
        available_instance_names = [instance.instance_info.name for instance in instances]
        duration = current_time - (last_available_time or current_time)
        print(f'\r{current_time:%Y-%m-%d %H:%M:%S.%f} - '
              f'Available Instances: {available_instance_names}, '
              f'Availability Duration: {duration}', end='')
    else:
        reference_time = last_available_time if last_available_time is not None else start_time
        duration_since_reference = current_time - reference_time
        duration_message = "since last available" if last_available_time is not None else "since start"
        print(f'\r{current_time:%Y-%m-%d %H:%M:%S.%f} - '
              f'No instances available. '
              f'Last available at: {reference_time:%Y-%m-%d %H:%M:%S.%f}, '
              f'Duration {duration_message}: {duration_since_reference}', end='')
