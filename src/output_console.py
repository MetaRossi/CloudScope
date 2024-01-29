from datetime import datetime
from typing import Optional, Set

from tracker import Tracker


def render_console_output(tracker: Tracker) -> None:
    """
    Updates console output with the latest availability information.
    """
    # Print a newline if there are any changes to the instance availability
    # Prevent printing a newline on the first poll with did_observe_instances
    # TODO move into render_to_console
    if ((tracker.has_new_availabilities() or tracker.has_removed_availabilities())
            and tracker.has_ever_observed_instances
            and not tracker.is_first_poll):
        print()

    # Render the console output
    render_to_console(
        is_available=tracker.is_session_active(),
        instance_names=tracker.get_current_names(),
        session_start_time=tracker.get_session_start_time(),
        session_end_time=tracker.get_session_end_time(),
        start_time=tracker.start_time,
    )


def render_to_console(
        is_available: bool,
        instance_names: Set[str],
        session_start_time: Optional[datetime],
        session_end_time: Optional[datetime],
        start_time: datetime,
) -> None:
    current_time = datetime.now()
    if is_available:
        available_instance_names = set([instance for instance in instance_names])
        duration = current_time - (session_start_time or current_time)

        output = f'\r{current_time:%Y-%m-%d %H:%M:%S.%f} - ' \
                 f'Available Instances: {available_instance_names}, ' \
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

        output = f'\r{current_time:%Y-%m-%d %H:%M:%S.%f} - ' \
                 f'No instances available. ' \
                 f'{last_message}: {reference_time:%Y-%m-%d %H:%M:%S.%f}, ' \
                 f'Duration {duration_message}: {duration_since_reference}'

        print(output, end='')
