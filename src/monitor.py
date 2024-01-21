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
    # Required fields
    api_key: str
    start_time: datetime
    # Private fields
    current_availabilities: Dict[InstanceType, InstanceAvailability] = Field(default_factory=dict, repr=False)
    is_first_poll: bool = Field(default=True, repr=False)
    session_start_time: Optional[datetime] = Field(default=None, repr=False)

    def poll(self) -> None:
        """
        Polls the cloud service for current instance availability and updates
        the monitoring information accordingly.

        This method performs the following actions:1
        1. Fetches the current instance types and their availability.
        2. Updates the available instances map with the new information.
        3. Logs information about new or removed instances.
        4. Calls render_to_console to update the console output with the latest availability information.
        """
        # Fetch current instance availability from the cloud service
        fetched_availabilities = fetch_instance_availabilities(self.api_key)
        fetch_time = datetime.now()

        if fetched_availabilities is None:
            fetched_availabilities = []

        # Determine newly available and no longer available instances
        current_types = set(i.instance_type for i in fetched_availabilities)
        existing_types = set(self.current_availabilities.keys())
        newly_available_types = current_types - existing_types
        no_longer_available_types = existing_types - current_types

        # Update available instances map with current information
        for fetched_availability in fetched_availabilities:
            # Get the current instance availability information
            current_availability = self.current_availabilities.get(fetched_availability.instance_type)

            # Create a new instance availability if it doesn't exist
            if current_availability is None:
                current_availability = fetched_availability

            # Get the instance type for the current availability
            current_instance_type = current_availability.instance_type

            # Update instance's last available time if it's newly available or already exists
            if current_instance_type in newly_available_types or current_instance_type in existing_types:
                current_availability.update(fetch_time)
            self.current_availabilities[current_instance_type] = current_availability

        # Log information for instances that have become available or unavailable
        for instance_type in newly_available_types:
            instance = self.current_availabilities[instance_type]
            log_instance_info(instance, "Available")
        for instance_type in no_longer_available_types:
            instance = self.current_availabilities.pop(instance_type)
            if instance is not None:
                log_instance_info(instance, "Unavailable")

        # Add a new line to the console output if there is a state change
        if bool(newly_available_types or no_longer_available_types) and not self.is_first_poll:
            print()

        # Track the first time any instance was available in this monitoring session
        if self.session_start_time is None and self.current_availabilities.values():
            # Get the earliest time any instance was available
            self.session_start_time = (
                min(instance.start_time for instance in self.current_availabilities.values())
            )

        # Clear the first time any instance was available in this monitoring session
        if not self.current_availabilities:
            self.session_start_time = None

        # Update console output with the latest availability information
        render_to_console(
            is_available=bool(self.current_availabilities),
            instances=list(self.current_availabilities.values()),
            session_start_time=self.session_start_time,
            start_time=self.start_time,
        )

        # Update the first poll flag
        self.is_first_poll = False
