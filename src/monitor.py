import logging
import os
from typing import Set, Dict, Optional

from pydantic import BaseModel, PrivateAttr

import lambda_api
import output_console
import output_log
from data_structures import InstanceType, InstanceAvailability
from src.config import Config
from src.lambda_api import fetch_instance_availabilities
from tracker import Tracker


# TODO alert if a new region is observed; not one in the lambda API region dict


class Monitor(BaseModel):
    """
    Monitor class for tracking and logging the availability of cloud instances.

    Attributes:
        config (Config): The application configuration.
        _tracker (Tracker): The tracker for monitoring instance availability.
    """
    # Required fields
    config: Config
    # Handled in code
    _tracker: Optional[Tracker] = PrivateAttr(default=None)

    def __init__(self, **data):
        super().__init__(**data)

        # Initialize the tracker
        self._tracker = Tracker(start_time=self.config.start_time)

    def poll(self) -> None:
        """
        Polls the cloud service for current instance availability and updates
        the monitoring information accordingly.
        """
        # Fetch instance availability data from the API
        fetch_time, fetched_availabilities_list = fetch_instance_availabilities(self.config.api_key)

        # Make a dictionary mapping instance keys to their availability information
        fetched_availabilities = {instance.instance_type: instance for instance in fetched_availabilities_list}

        # If the fetch time is None, the request failed. We should skip this poll.
        if fetch_time is None:
            logging.warning("No fetch time returned from API. Skipping this poll.")
            return

        # Update the tracker with the fetched availabilities
        self._tracker.update(fetched_availabilities, fetch_time)

        # Log the instance changes
        output_log.log_instance_changes(self._tracker)

        # Update the console output with the latest availability information
        output_console.render_console_output(self._tracker)

        # Log when a region not in the config.static_regions_dict is observed
        # When a new region is observed, it is added to the config.new_logged_regions set to prevent logging it again
        Monitor._detect_new_regions(self._tracker.current_availabilities,
                                    self.config.new_logged_regions,
                                    self.config.enable_voice_notifications)

    @staticmethod
    def _detect_new_regions(availabilities: Dict[InstanceType, InstanceAvailability],
                            new_logged_regions: Set[str],
                            enable_voice_notifications: bool
                            ) -> None:
        """
        Detects when a region not in the config.static_regions_dict is observed.
        """
        # Get the static regions from the config
        known_regions = set(lambda_api.static_dict_of_known_regions().keys())

        # Get the current available regions from the InstanceType in availabilities
        current_available_regions = set([instance.region for instance in availabilities.keys()])

        # Get the new regions
        new_regions = current_available_regions - known_regions

        # Log the new regions
        for region in new_regions:
            if region not in new_logged_regions:
                logging.critical(f"New region observed: {region}")
                print(f"""{Config.now_formatted_str()} - New region observed: {region}""")
                if enable_voice_notifications:
                    os.system('say "New Region Detected"')
                # TODO send an email alert; this should not occur often

        # Prevent logging the same new regions multiple times
        new_logged_regions.update(new_regions)
