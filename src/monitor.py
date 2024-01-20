from datetime import datetime
from typing import List, Dict, Optional

from pydantic import BaseModel, Field

from src.data_structures.instance_type import InstanceType
from src.data_structures.region import Region
from src.lambda_api import fetch_instance_types
from src.output import log_instance_info, render_to_console


class Monitor(BaseModel):
    # Required fields
    start_time: datetime = Field(frozen=True)
    # Handled by code
    available_instances: Dict[str, InstanceType] = Field(default_factory=dict)
    last_available_time: Optional[datetime] = None
    is_available: bool = False

    def poll(self, api_key: str) -> None:
        new_available, data = fetch_instance_types(api_key)
        previous_state = self.is_available
        self.is_available = bool(new_available)

        # Update last_available_time only when transitioning from no available instances to some available instances
        if self.is_available and not previous_state:
            if self.last_available_time is None:
                self.last_available_time = datetime.now()

        # Process and compare the fetched data with the current state
        for instance_name in new_available:
            instance_data = data[instance_name]["instance_type"]
            regions = [Region(**region) for region in data[instance_name]["regions_with_capacity_available"]]

            if instance_name not in self.available_instances:
                # New instance available
                self.available_instances[instance_name] = InstanceType(**instance_data,
                                                                       regions_with_capacity_available=regions)
                self.log_change(instance_name, regions, 'available')
            else:
                # Check for changes in regions
                available_regions = self.available_instances[instance_name].regions_with_capacity_available
                current_regions = {region.name for region in available_regions}
                new_regions = {region.name for region in regions}

                if current_regions != new_regions:
                    self.available_instances[instance_name].regions_with_capacity_available = regions
                    self.log_change(instance_name, regions, 'updated')

        # Check for instances that are no longer available
        for instance_name in list(self.available_instances):
            if instance_name not in new_available:
                available_regions = self.available_instances[instance_name].regions_with_capacity_available
                self.log_change(instance_name, available_regions, 'unavailable')
                del self.available_instances[instance_name]

        # Render to console with new information
        if previous_state != self.is_available:
            print()  # Start a new line on availability status change
        render_to_console(self.is_available,
                          self.available_instances,
                          self.last_available_time,
                          self.start_time)

    @staticmethod
    def log_change(instance_type: str, regions: List[Region], status: str) -> None:
        for region in regions:
            log_instance_info(instance_type, region.name, status)
