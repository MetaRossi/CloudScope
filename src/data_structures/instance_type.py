from typing import List, Any, Dict

from pydantic import BaseModel

from src.data_structures.region import Region


class InstanceType(BaseModel):
    name: str
    description: str
    price_cents_per_hour: int
    specs: Dict[str, Any]
    regions_with_capacity_available: List[Region]
