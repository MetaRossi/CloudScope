import logging
import os
from datetime import datetime
from typing import Tuple, Dict, Optional, Set, List

from pydantic import BaseModel, Field

from src import lambda_api
from src.config import Config
from src.data_structures import InstanceAvailability, InstanceType
from src.lambda_api import fetch_instance_availabilities
from src.output import render_to_console, log_instance_info


# TODO alert if a new region is observed; not one in the lambda API region dict


class Monitor(BaseModel):
    """
    Monitor class for tracking and logging the availability of cloud instances.

    Attributes:
        config (Config): The application configuration.
        current_availabilities (Dict[Tuple[str, str, str], InstanceAvailability]):
            A dictionary mapping instance keys to their availability information.
    """
    # Required fields
    config: Config
    # Handled in code
    current_availabilities: Dict[InstanceType, InstanceAvailability] = Field(default_factory=dict, repr=False)
    did_observe_instances: bool = Field(default=False, repr=False)
    session_start_time: Optional[datetime] = Field(default=None, repr=False)
    session_end_time: Optional[datetime] = Field(default=None, repr=False)
    is_first_poll: bool = Field(default=True, repr=False)

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

        # Update the current availability information with the fetched data
        # Returns a tuple of new, updated, and removed availabilities
        new_availabilities, updated_availabilities, removed_availabilities = (
            self._analyze_availability(fetch_time, fetched_availabilities, self.current_availabilities))

        # Replace the current availabilities with the new and updated availabilities
        self.current_availabilities = {**new_availabilities, **updated_availabilities}

        # Log information for instances that have become available or unavailable
        Monitor._log_instance_changes(new_availabilities, removed_availabilities)

        # Update the session start and end times
        self.did_observe_instances, self.session_start_time, self.session_end_time = (
            Monitor._update_time_state(self.did_observe_instances, bool(self.current_availabilities),
                                       self.session_start_time, self.session_end_time, fetch_time)
        )

        # Analyze the availability names
        new_availability_names, current_availability_names, removed_availability_names = (
            Monitor._analyze_availability_names(fetched_availabilities, self.current_availabilities))

        # Update the console output with the latest availability information
        Monitor._render_console_output(current_availability_names,
                                       self.session_start_time, self.session_end_time, self.config.start_time,
                                       # Only needed for new line detection
                                       bool(new_availability_names), bool(removed_availability_names),
                                       self.did_observe_instances, self.is_first_poll)

        # Set the is_first_poll flag to False
        self.is_first_poll = False

        # Log when a region not in the config.static_regions_dict is observed
        # When a new region is observed, it is added to the config.new_logged_regions set to prevent logging it again
        Monitor._detect_new_regions(self.current_availabilities,
                                    self.config.new_logged_regions,
                                    self.config.enable_voice_notifications)

    @staticmethod
    def _render_console_output(availability_names: List[str],
                               session_start_time: Optional[datetime],
                               session_end_time: Optional[datetime],
                               start_time: datetime,
                               new_availabilities: bool,
                               removed_availabilities: bool,
                               did_observe_instances: bool,
                               is_first_poll: bool
                               ) -> None:
        """
        Updates console output with the latest availability information.
        """
        # Print a newline if there are any changes to the instance availability
        # Prevent printing a newline on the first poll with did_observe_instances
        # TODO move into render_to_console
        if (new_availabilities or removed_availabilities) and did_observe_instances and not is_first_poll:
            print()

        # Render the console output
        render_to_console(
            is_available=bool(availability_names),
            instances=list(availability_names),
            session_start_time=session_start_time,
            session_end_time=session_end_time,
            start_time=start_time,
        )

    @staticmethod
    def _analyze_availability_names(fetched_availabilities: Dict[InstanceType, InstanceAvailability],
                                    current_availabilities: Dict[InstanceType, InstanceAvailability]
                                    ) -> Tuple[List[str],
                                               List[str],
                                               List[str]]:
        # Lists for new, updated, and removed availability names
        new_availability_names: List[str] = []
        removed_availability_names: List[str] = []

        # Just the names of the availabilities
        fetched_availability_names = [instance.instance_type.name for instance in fetched_availabilities.values()]
        current_availability_names = [instance.instance_type.name for instance in current_availabilities.values()]

        # Find new availability names
        for fetched_availability_name in fetched_availability_names:
            if fetched_availability_name not in current_availability_names:
                new_availability_names.append(fetched_availability_name)

        # Find removed availability names
        for current_availability_name in current_availability_names:
            if current_availability_name not in fetched_availability_names:
                removed_availability_names.append(current_availability_name)

        # Make list of current availability names
        # This overrides the list of current availability names from the input
        current_availability_names = fetched_availability_names

        return new_availability_names, current_availability_names, removed_availability_names

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
    def _update_time_state(did_observe_instances: bool,
                           current_availabilities: bool,
                           session_start_time: Optional[datetime],
                           session_end_time: Optional[datetime],
                           fetch_time: datetime
                           ) -> Tuple[bool, Optional[datetime], Optional[datetime]]:
        # Update the session start and end times
        if not did_observe_instances and not current_availabilities:
            # No instances have been observed yet
            session_start_time = None
            session_end_time = None
        elif session_start_time is None and current_availabilities:
            # If this is the first time we've seen any availabilities for this session, set the session start time
            session_start_time = fetch_time
            session_end_time = None
            # Set the did_observe_instances flag to True
            did_observe_instances = True
        elif session_end_time is None and not current_availabilities:
            # If there are no availabilities, set the session end time
            session_start_time = None
            session_end_time = fetch_time
        elif session_start_time is not None and current_availabilities:
            # If there are availabilities, and we've already seen availabilities for this session
            pass
        elif session_end_time is not None and not current_availabilities:
            # If there are no availabilities, and we've already seen availabilities for this session
            pass
        else:
            logging.error("Invalid state for session start and end times. Variables:\n"
                          "did_observe_instances: %s"
                          "session_start_time: %s, "
                          "session_end_time: %s, "
                          "start_time: %s"
                          "current_availabilities: %s"
                          )

        return did_observe_instances, session_start_time, session_end_time

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
