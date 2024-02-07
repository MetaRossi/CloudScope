from datetime import datetime
from typing import Optional, Set

from core.tracker import Tracker


def print_console_message(current_time: datetime = datetime.now(), message: str = "", do_r: bool = False) -> None:
    print(get_console_message(current_time, message, do_r))


def get_console_message(current_time: datetime = datetime.now(), message: str = "", do_r: bool = False) -> str:
    return f"{'\r' if do_r else ''}{current_time:%Y-%m-%d %H:%M:%S.%f} - {message}"


def render_console_output(tracker: Tracker) -> None:
    """Updates console managers with the latest availability information."""
    # Print a newline if there are any changes to the instance availability
    # Prevent printing a newline on the first poll with did_observe_instances
    if ((tracker.has_new_availabilities() or tracker.has_removed_availabilities())
            and tracker.has_ever_observed_instances
            and not tracker.is_first_poll):
        print()

    # Render the console managers
    render_to_console(
        is_available=tracker.is_session_active(),
        instance_names=tracker.get_current_names(),
        session_start_time=tracker.session_start_time,
        session_end_time=tracker.session_end_time,
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
        duration = current_time - session_start_time

        message = f'Available Instances: {available_instance_names}, ' \
                  f'Availability Duration: {duration}'

        output = get_console_message(current_time, message, True)

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

        message = f'No instances available. ' \
                  f'{last_message}: {reference_time:%Y-%m-%d %H:%M:%S.%f}, ' \
                  f'Duration {duration_message}: {duration_since_reference}'

        output = get_console_message(current_time, message, True)

        print(output, end='')
