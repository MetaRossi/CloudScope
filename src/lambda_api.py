from typing import Tuple, Set, Dict, Any, List
import requests
from datetime import datetime

from src.data_structures import InstanceAvailability, InstanceInfo


def fetch_instance_types(api_key: str,
                         api_endpoint: str = "https://cloud.lambdalabs.com/api/v1/instance-types"
                         ) -> Tuple[Set[str], List[InstanceAvailability]]:
    """
    Fetches instance types from a given API endpoint using the provided API key.

    This function makes an HTTP GET request to the specified API endpoint. It expects
    a JSON response with instance details. It extracts and returns a set of available
    instances and a list of InstanceAvailability objects.

    Args:
        api_key (str): The API key used for authorization in the request header.
        api_endpoint (str): The URL of the API endpoint to fetch instance types from.

    Returns:
        Tuple[Set[str], List[InstanceAvailability]]: A tuple containing two elements:
            - A set of instance type strings that have capacity available.
            - A list of InstanceAvailability objects representing each instance type
              and its availability in different regions.

    The function handles connection errors by printing an error message and returning
    an empty set and list. Other HTTP errors are logged with their status codes
    and response text. The function uses type hints for clarity and type safety.
    """
    headers: Dict[str, str] = {"Authorization": f"Bearer {api_key}"}

    try:
        response: requests.Response = requests.get(api_endpoint, headers=headers)
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
        return set(), []

    if response.status_code == 200:
        data: Dict[str, Any] = response.json().get("data", {})
        available_instances: Set[str] = set()
        instance_availability_list: List[InstanceAvailability] = []

        for instance, details in data.items():
            if details.get("regions_with_capacity_available"):
                available_instances.add(instance)

                instance_info_data = details['instance_type']
                for region in details['regions_with_capacity_available']:
                    instance_info = InstanceInfo(
                        name=instance_info_data['name'],
                        description=instance_info_data['description'],
                        region=region['name']
                    )
                    current_time = datetime.now()
                    instance_availability = InstanceAvailability(
                        instance_info=instance_info,
                        start_time=current_time,
                        last_seen_time=current_time
                    )
                    instance_availability_list.append(instance_availability)

        return available_instances, instance_availability_list
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return set(), []
