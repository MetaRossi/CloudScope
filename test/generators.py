import random
from datetime import timedelta, datetime
from typing import Dict, List, Optional

from src.data_structures import InstanceType, InstanceAvailability


def type_generator(type_list: Optional[List[str]] = None) -> str:
    if type_list is None:
        return f"Type_{random.randint(1, 10000)}"
    else:
        return random.choice(type_list)


def description_generator(description_list: Optional[List[str]] = None) -> str:
    if description_list is None:
        return f"Description_{random.randint(1, 10000)}"
    else:
        return random.choice(description_list)


def region_generator(region_list: Optional[List[str]] = None) -> str:
    if region_list is None:
        return f"Region_{random.randint(1, 10000)}"
    else:
        return random.choice(region_list)


def instance_type_generator(type_list: Optional[List[str]] = None,
                            description_list: Optional[List[str]] = None,
                            region_list: Optional[List[str]] = None,
                            ) -> InstanceType:
    return InstanceType(
        name=type_generator(type_list=type_list),
        description=description_generator(description_list=description_list),
        region=region_generator(region_list=region_list)
    )


def availability_generator(type_list: Optional[List[str]] = None,
                           description_list: Optional[List[str]] = None,
                           region_list: Optional[List[str]] = None,
                           ) -> InstanceAvailability:
    instance_type = instance_type_generator(type_list=type_list,
                                            description_list=description_list,
                                            region_list=region_list)
    start_time = datetime.now() - timedelta(days=random.randint(0, 5))
    last_time_available = start_time + timedelta(hours=random.randint(1, 24))
    return InstanceAvailability(
        instance_type=instance_type,
        start_time=start_time,
        last_time_available=last_time_available
    )


def availabilities_generator(num: int,
                             type_list: Optional[List[str]] = None,
                             description_list: Optional[List[str]] = None,
                             region_list: Optional[List[str]] = None,
                             ) -> Dict[InstanceType, InstanceAvailability]:
    availabilities = {}
    for _ in range(num):
        availability = availability_generator(type_list=type_list,
                                              description_list=description_list,
                                              region_list=region_list)
        availabilities[availability.instance_type] = availability

    return availabilities
