import json
from datetime import datetime, timedelta
from typing import List

from pydantic import BaseModel, Field


class InstanceType(BaseModel):
    name: str
    description: str
    region: str

    class Config:
        frozen = True  # Make entire class immutable


class InstanceAvailability(BaseModel):
    instance_type: InstanceType = Field(frozen=True)
    start_time: datetime = Field(frozen=True)
    last_time_available: datetime

    # Make equality check only compare the instance_type field
    def __eq__(self, other):
        return self.instance_type == other.instance_type

    def update(self, current_time: datetime) -> None:
        self.last_time_available = current_time

    def get_duration(self) -> timedelta:
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
