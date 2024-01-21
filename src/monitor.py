import logging
from datetime import datetime
from typing import Tuple, Dict, Optional

from pydantic import BaseModel, Field

from src.data_structures import InstanceAvailability, InstanceType
from src.lambda_api import fetch_instance_availabilities
from src.output import render_to_console, log_instance_info


class Monitor(BaseModel):
    """
    Monitor class for tracking and logging the availability of cloud instances.

    Attributes:
        api_key (str): API key used to authenticate with the cloud service.
        start_time (datetime): The time when the monitoring started.
        current_availabilities (Dict[Tuple[str, str, str], InstanceAvailability]):
            A dictionary mapping instance keys to their availability information.
    """
    api_key: str
    start_time: datetime
    current_availabilities: Dict[InstanceType, InstanceAvailability] = Field(default_factory=dict, repr=False)
    is_first_poll: bool = Field(default=True, repr=False)
    session_start_time: Optional[datetime] = Field(default=None, repr=False)

    def poll(self) -> None:
        """
        Polls the cloud service for current instance availability and updates
        the monitoring information accordingly.
        """
        # Fetch instance availability data from the API
        fetch_time, fetched_availabilities_list = fetch_instance_availabilities(self.api_key)
        # Make a dictionary mapping instance keys to their availability information
        fetched_availabilities = {instance.instance_type: instance for instance in fetched_availabilities_list}

        # If the fetch time is None, the request failed. We should skip this poll.
        if fetch_time is None:
            logging.warning("No fetch time returned from API. Skipping this poll.")
            return

        # Update the current availability information with the fetched data
        # Returns a tuple of new, updated, and removed availabilities
        new_availabilities, updated_availabilities, removed_availabilities = (
            self._analyze_availability(fetch_time, fetched_availabilities, self.current_availabilities))

        # Replace the current availabilities with the new and updated availabilities
        self.current_availabilities = {**new_availabilities, **updated_availabilities}

        # Log information for instances that have become available or unavailable
        Monitor._log_instance_changes(new_availabilities, removed_availabilities)

        # Print a newline if there are any changes to the instance availability
        if bool(new_availabilities or removed_availabilities) and not self.is_first_poll:
            print()

        # Set the session start time if it is not already set and there are available instances
        if self.session_start_time is None and self.current_availabilities:
            self.session_start_time = min(instance.start_time for instance in self.current_availabilities.values())
        if not self.current_availabilities:
            self.session_start_time = None

        # Update the console output with the latest availability information
        Monitor._render_console_output(self.current_availabilities, self.session_start_time, self.start_time)

        # Set the first poll flag to false
        self.is_first_poll = False

    @staticmethod
    def _analyze_availability(fetch_time: datetime,
                              fetched_availabilities: Dict[InstanceType, InstanceAvailability],
                              current_availabilities: Dict[InstanceType, InstanceAvailability]
                              ) -> Tuple[Dict[InstanceType, InstanceAvailability],
                                         Dict[InstanceType, InstanceAvailability],
                                         Dict[InstanceType, InstanceAvailability]]:
        new_availabilities: Dict[InstanceType, InstanceAvailability] = {}
        updated_availabilities: Dict[InstanceType, InstanceAvailability] = {}
        removed_availabilities: Dict[InstanceType, InstanceAvailability] = {}

        # Find updated and new availabilities
        for fetched_availability in fetched_availabilities.values():
            current_availability = current_availabilities.get(fetched_availability.instance_type)
            if current_availability is not None:
                # If the instance is already in the current availabilities, update it and add it to the updated dict
                current_availability.update(fetch_time)
                updated_availabilities[fetched_availability.instance_type] = current_availability
            else:
                # If the instance is not in the current availabilities, add it to the new dict
                new_availabilities[fetched_availability.instance_type] = fetched_availability

        # Find removed availabilities
        for current_availability in current_availabilities.values():
            if current_availability.instance_type not in fetched_availabilities:
                # If the instance is not in the fetched availabilities, add it to the removed dict
                removed_availabilities[current_availability.instance_type] = current_availability

        return new_availabilities, updated_availabilities, removed_availabilities

    @staticmethod
    def _log_instance_changes(new_availabilities: Dict[InstanceType, InstanceAvailability],
                              removed_availabilities: Dict[InstanceType, InstanceAvailability],
                              ) -> None:
        """
        Logs information for instances that have become available or unavailable.
        """
        for instance in new_availabilities.values():
            log_instance_info(instance, "Available")

        for instance in removed_availabilities.values():
            if instance is not None:
                log_instance_info(instance, "Unavailable")

    @staticmethod
    def _render_console_output(availabilities: Dict[InstanceType, InstanceAvailability],
                               session_start: Optional[datetime],
                               start_time: datetime
                               ) -> None:
        """
        Updates console output with the latest availability information.
        """
        render_to_console(
            is_available=bool(availabilities),
            instances=list(availabilities.values()),
            session_start_time=session_start,
            start_time=start_time,
        )
