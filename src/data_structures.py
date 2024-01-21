import json
from datetime import datetime
from typing import List

from pydantic import BaseModel


class InstanceType(BaseModel):
    name: str
    description: str
    region: str

    class Config:
        frozen = True  # One way to make the class immutable and hashable


class InstanceAvailability(BaseModel):
    instance_type: InstanceType
    start_time: datetime
    last_time_available: datetime = None

    def update(self, current_time: datetime):
        self.last_time_available = current_time

    def get_duration(self):
        return self.last_time_available - self.start_time

    @classmethod
    def from_lambda_json_str(cls, json_str: str) -> List['InstanceAvailability']:
        data = json.loads(json_str)
        instances = []
        fetch_time = datetime.now()
        for instance_details in data['data'].values():
            instance_info_data = instance_details['instance_type']
            for region in instance_details['regions_with_capacity_available']:
                instance_info = InstanceType(
                    name=instance_info_data['name'],
                    description=instance_info_data['description'],
                    region=region['name']
                )
                instance_availability = cls(
                    instance_info=instance_info,
                    start_time=fetch_time,
                    last_time_available=fetch_time
                )
                instances.append(instance_availability)
        return instances
