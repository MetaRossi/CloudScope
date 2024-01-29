from datetime import datetime
from typing import Optional, Dict, Set

from pydantic import BaseModel, Field, PrivateAttr

from data_structures import InstanceAvailability, InstanceType


class Tracker(BaseModel):
    start_time: datetime = Field(frozen=True)
    has_ever_observed_instances: bool = False

    last_fetch_time: Optional[datetime] = None
    _session_start_time: Optional[datetime] = PrivateAttr(default=None)
    _session_end_time: Optional[datetime] = PrivateAttr(default=None)

    current_availabilities: Dict[InstanceType, InstanceAvailability] = Field(default_factory=dict, repr=False)
    new_availabilities: Dict[InstanceType, InstanceAvailability] = Field(default_factory=dict, repr=False)
    updated_availabilities: Dict[InstanceType, InstanceAvailability] = Field(default_factory=dict, repr=False)
    removed_availabilities: Dict[InstanceType, InstanceAvailability] = Field(default_factory=dict, repr=False)

    def is_first_poll(self) -> bool:
        return self.last_fetch_time is None

    def is_session_active(self) -> bool:
        return len(self.current_availabilities) > 0

    def get_session_start_time(self) -> Optional[datetime]:
        return self._session_start_time if self.is_session_active() else None

    def get_session_end_time(self) -> Optional[datetime]:
        return self._session_end_time if self.is_session_active() else None

    def get_current_names(self) -> Set[str]:
        return {instance_type.name for instance_type in self.current_availabilities.keys()}

    def get_updated_names(self) -> Set[str]:
        return {instance_type.name for instance_type in self.updated_availabilities.keys()}

    def get_new_names(self) -> Set[str]:
        return {instance_type.name for instance_type in self.new_availabilities.keys()}

    def get_removed_names(self) -> Set[str]:
        return {instance_type.name for instance_type in self.removed_availabilities.keys()}

    def has_current_availabilities(self) -> bool:
        return len(self.current_availabilities) > 0

    def has_new_availabilities(self) -> bool:
        return len(self.new_availabilities) > 0

    def has_updated_availabilities(self) -> bool:
        return len(self.updated_availabilities) > 0

    def has_removed_availabilities(self) -> bool:
        return len(self.removed_availabilities) > 0

    def update(self,
               fetched_availabilities: Dict[InstanceType, InstanceAvailability],
               fetch_time: datetime
               ) -> None:
        # Update the last fetch time with the fetch time
        self.last_fetch_time = fetch_time

        # Update if the Tracker has ever observed instances
        if not self.has_ever_observed_instances and len(fetched_availabilities) > 0:
            self.has_ever_observed_instances = True

        # Create dictionaries for new, updated, and removed availabilities
        self.new_availabilities = {}
        self.updated_availabilities = {}
        self.removed_availabilities = {}

        # Update the new and updated availabilities
        for instance_type, availability in fetched_availabilities.items():
            if instance_type not in self.current_availabilities:
                self.new_availabilities[instance_type] = availability
            elif self.current_availabilities[instance_type] != availability:
                self.updated_availabilities[instance_type] = availability

        # Update the removed availabilities
        for instance_type, availability in self.current_availabilities.items():
            if instance_type not in fetched_availabilities:
                self.removed_availabilities[instance_type] = availability

        # Replace the current availabilities with the fetched data
        self.current_availabilities = fetched_availabilities

        # Log instance changes
        self._log_instance_changes(self.new_availabilities, self.removed_availabilities)

        # Update the session start and end times
        # Is start of a session? (no current availabilities and new availabilities)
        if not self.is_session_active() and self.has_new_availabilities():
            self._session_start_time = fetch_time
        # Is end of a session? (no new availabilities and current availabilities)
        elif self.is_session_active() and not self.has_new_availabilities():
            self._session_end_time = fetch_time
        # Else, no session in progress; leave session start and end times as they are
        else:
            pass
