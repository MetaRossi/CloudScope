from datetime import datetime
from typing import Tuple, Dict

from pydantic import BaseModel, Field

from src.data_structures import InstanceAvailability
from src.lambda_api import fetch_instance_types
from src.output import render_to_console, log_instance_info


class Monitor(BaseModel):
    """
    Monitor class for tracking and logging the availability of cloud instances.

    Attributes:
        api_key (str): API key used to authenticate with the cloud service.
        start_time (datetime): The time when the monitoring started.
        available_instances (Dict[Tuple[str, str, str], InstanceAvailability]):
            A dictionary mapping instance keys to their availability information.
    """

    api_key: str
    start_time: datetime
    available_instances: Dict[Tuple[str, str, str], InstanceAvailability] = Field(default_factory=dict)

    def poll(self) -> None:
        """
        Polls the cloud service for current instance availability and updates
        the monitoring information accordingly.

        This method performs the following actions:
        1. Fetches the current instance types and their availability.
        2. Updates the available instances map with the new information.
        3. Logs information about new or removed instances.
        4. Calls render_to_console to update the console output with the latest availability information.
        """
        # Fetch current instance availability from the cloud service
        instance_types, new_instances = fetch_instance_types(self.api_key)

        # Determine newly available and no longer available instances
        new_instance_keys = {instance.get_key() for instance in new_instances}
        existing_instance_keys = set(self.available_instances.keys())
        newly_available = new_instance_keys - existing_instance_keys
        no_longer_available = existing_instance_keys - new_instance_keys

        # Update available instances map with current information
        for instance in new_instances:
            key = instance.get_key()
            # Update instance's last available time if it's newly available or already exists
            if key in newly_available or key in existing_instance_keys:
                instance.update(current_time=datetime.now())
            self.available_instances[key] = instance

        # Log information for instances that have become available or unavailable
        for key in newly_available:
            instance = self.available_instances[key]
            log_instance_info(instance, "Available")
        for key in no_longer_available:
            instance = self.available_instances.pop(key)
            if instance is not None:
                log_instance_info(instance, "Unavailable")

        # Determine if there's a change in the state of instance availability
        state_change = bool(newly_available or no_longer_available)

        # Add a new line to the console output if there is a state change
        if state_change:
            print()

        # Determine the last time any instance was available for rendering to console
        last_available_time = max(
            (instance.last_time_available for instance in self.available_instances.values()),
            default=self.start_time
        )

        # Update console output with the latest availability information
        render_to_console(
            is_available=bool(self.available_instances),
            instances=list(self.available_instances.values()),
            last_available_time=last_available_time,
            start_time=self.start_time,
        )
