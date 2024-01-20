import json
from datetime import datetime
from typing import Tuple, List

from pydantic import BaseModel


class InstanceInfo(BaseModel):
    name: str
    description: str
    region: str

    def get_key(self) -> Tuple[str, str, str]:
        return self.name, self.description, self.region


class InstanceAvailability(BaseModel):
    instance_info: InstanceInfo
    start_time: datetime
    last_time_available: datetime = None

    def get_key(self) -> Tuple[str, str, str]:
        return self.instance_info.get_key()

    def update(self, current_time: datetime = datetime.now()):
        self.last_time_available = current_time

    def get_duration(self):
        return self.last_time_available - self.start_time

    @classmethod
    def from_json_str(cls, json_str: str) -> List['InstanceAvailability']:
        data = json.loads(json_str)
        instances = []
        for instance_details in data['data'].values():
            instance_info_data = instance_details['instance_type']
            for region in instance_details['regions_with_capacity_available']:
                instance_info = InstanceInfo(
                    name=instance_info_data['name'],
                    description=instance_info_data['description'],
                    region=region['name']
                )
                current_time = datetime.now()
                instance_availability = cls(
                    instance_info=instance_info,
                    start_time=current_time,
                    last_time_available=current_time
                )
                instances.append(instance_availability)
        return instances
