import io
import logging
import sys
from datetime import datetime
from typing import Dict, Optional

from src.data_structures.instance_type import InstanceType


def log_instance_info(instance_type: str, region_name: str, status: str, start_time: datetime = None) -> None:
    # Log info of the instance type for a specific region
    end_time = datetime.now()

    if status == "Not Available" and start_time is not None:
        duration = end_time - start_time
        logging.info(
            f"Instance Type: {instance_type}, Region: {region_name} - "
            f"Status: {status} - "
            f"Start: {start_time} - "
            f"End: {end_time} - "
            f"Duration: {duration}"
        )
    elif status == "Available":
        if start_time is None:
            start_time = end_time
        duration = end_time - start_time
        logging.info(
            f"Instance Type: {instance_type}, Region: {region_name} - "
            f"Status: {status} - "
            f"Start: {start_time} - "
            f"Duration: {duration}"
        )
    else:
        logging.error(f"Invalid status for Instance Type: {instance_type}, Region: {region_name} - Status: {status}")


def render_to_console(
    is_available: bool,
    instances: Dict[str, InstanceType],
    last_available_time: Optional[datetime],
    start_time: datetime,
    output_stream: io.TextIOWrapper = sys.stdout
) -> None:
    current_time = datetime.now()
    if is_available:
        available_instance_names = [instance.name for instance in instances.values()]
        duration = current_time - (last_available_time or current_time)
        output_stream.write(f'\r{current_time:%Y-%m-%d %H:%M:%S.%f} - '
                            f'Available Instances: {available_instance_names}, '
                            f'Availability Duration: {duration}')
    else:
        reference_time = last_available_time if last_available_time is not None else start_time
        duration_since_reference = current_time - reference_time
        duration_message = "since last available" if last_available_time is not None else "since start"
        output_stream.write(f'\r{current_time:%Y-%m-%d %H:%M:%S.%f} - '
                            f'No instances available. '
                            f'Last available at: {reference_time:%Y-%m-%d %H:%M:%S.%f}, '
                            f'Duration {duration_message}: {duration_since_reference}')
    output_stream.flush()

# # Example usage in tests
# from io import StringIO
#
# def test_render_to_console():
#     buffer = StringIO()
#     # Call the function with mock data and buffer as the output_stream
#     render_to_console(True, mock_instances, mock_last_available_time, mock_start_time, buffer)
#     # Now buffer.getvalue() contains the output of the function
#     print(buffer.getvalue())  # or use assertions to test the output\
