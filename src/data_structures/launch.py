import json
import logging
from typing import Optional, Set, List

from pydantic import BaseModel, Field

from data_structures.allow import AllowSet


class LaunchInstance(BaseModel):
    """A class for storing the launch instance configuration settings."""
    instance_name: str = Field(frozen=True)
    max_price: float = Field(frozen=True)
    max_instances: int = Field(frozen=True)
    regions: AllowSet = Field(frozen=True)

    def is_allowed(self, instance_name: str, price: float, current_running_instances: int, region: str) -> bool:
        """Check if the instance_name, region, price, and current_running_instances are allowed."""
        return (self.instance_name == instance_name and
                price <= self.max_price and
                current_running_instances < self.max_instances and
                self.regions.is_allowed(region))

    def log_launch_instance(self, label: Optional[str] = None) -> None:
        """Log the launch instance configuration settings."""
        if label:
            logging.info(f"For {label}, "
                         f"instance name: {self.instance_name}; "
                         f"max price: {self.max_price}; "
                         f"max instances: {self.max_instances}; "
                         f"computed regions: {self.regions.get_computed_set()}")
        else:
            logging.info(f"Instance name: {self.instance_name}; "
                         f"max price: {self.max_price}; "
                         f"max instances: {self.max_instances}; "
                         f"computed regions: {self.regions.get_computed_set()}")

    def __eq__(self, other):
        return self.instance_name == other.instance_name

    def __hash__(self):
        return hash(self.instance_name)


class LaunchInstances(BaseModel):
    """A class for storing the launch instance set configuration settings."""
    launch_instances: Set[LaunchInstance] = Field(default_factory=set, frozen=True)

    @staticmethod
    def from_config_json_array(config_json_array: List[str],
                               instances_full_set: Set[str],
                               regions_full_set: Set[str]
                               ) -> "LaunchInstances":
        """Create a LaunchInstanceSet object from a config json array."""
        launch_instances = set()
        for json_str in config_json_array:
            # Parse the json string like:
            #     '{"instance_names": "gpu_1x_h100", "max_price": 0.5, "max_instances": 1, "regions": ["*"]}'
            data: dict = json.loads(json_str)
            instance_name = data['instance_name']
            max_price = data['max_price']
            max_instances = data['max_instances']
            regions = AllowSet(full_set=regions_full_set,
                               allow_set=data['regions'])

            # Ensure that the instance_name is in the full set
            if instance_name not in instances_full_set:
                raise ValueError(f"Instance name not in full set: {json_str}")

            # Ensure that the LaunchInstance is not a duplicate
            if LaunchInstance(instance_name=instance_name,
                              max_price=max_price,
                              max_instances=max_instances,
                              regions=regions) in launch_instances:
                raise ValueError(f"Duplicate LaunchInstance: {json_str}")

            # Add the LaunchInstance to the set
            launch_instances.add(LaunchInstance(instance_name=instance_name,
                                                max_price=max_price,
                                                max_instances=max_instances,
                                                regions=regions))

        return LaunchInstances(launch_instances=launch_instances)

    def log_launch_instances(self, label: Optional[str] = None) -> None:
        """Log the launch instance set on multiple lines."""
        if label:
            logging.info(f"For {label}, computed set:")
        else:
            logging.info(f"Computed set:")
        for launch_instance in self.launch_instances:
            launch_instance.log_launch_instance(label)
