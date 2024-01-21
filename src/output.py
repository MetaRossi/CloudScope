import logging
from datetime import datetime
from typing import Optional, List

from src.data_structures import InstanceAvailability


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


def render_to_console(
    is_available: bool,
    instances: List[InstanceAvailability],
    session_start_time: Optional[datetime],
    session_end_time: Optional[datetime],
    start_time: datetime,
) -> None:
    current_time = datetime.now()
    if is_available:
        available_instance_names = set([instance.instance_type.name for instance in instances])
        duration = current_time - (session_start_time or current_time)

        output = f'\r{current_time:%Y-%m-%d %H:%M:%S.%f} - '\
                 f'Available Instances: {available_instance_names}, '\
                 f'Availability Duration: {duration}'

        print(output, end='')
    else:
        # Determine the reference time and duration message
        if session_start_time is not None:
            reference_time = session_start_time
            last_message = "Session started at"
            duration_message = "since session start"
        elif session_end_time is not None:
            reference_time = session_end_time
            last_message = "Last available at"
            duration_message = "since last available"
        else:
            reference_time = start_time
            last_message = "Started at"
            duration_message = "since start"

        duration_since_reference = current_time - reference_time

        output = f'\r{current_time:%Y-%m-%d %H:%M:%S.%f} - '\
                 f'No instances available. '\
                 f'{last_message}: {reference_time:%Y-%m-%d %H:%M:%S.%f}, '\
                 f'Duration {duration_message}: {duration_since_reference}'

        print(output, end='')
