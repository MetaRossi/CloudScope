import logging
from datetime import datetime
from typing import Tuple, Dict, Any, List, Optional, Set

import requests

from src.data_structures import InstanceAvailability, InstanceType


def static_dict_of_known_regions() -> Dict[str, str]:
    """
    Returns a dictionary of known regions and their names.
    Static because the Lambda API does not provide region names like it does for instance names.
    Retrieved manually from the launch instance page but only when an instance is available:
    https://cloud.lambdalabs.com/instances
    """
    return {
        "us-east-1": "Virginia, USA",
        "us-west-1": "California, USA",
        "us-west-2": "Arizona, USA",
        "us-west-3": "Utah, USA",
        "us-midwest-1": "Illinois, USA",
        "us-south-1": "Texas, USA",
        "europe-central-1": "Germany",
        "me-west-1": "Israel",
        "asia-south-1": "India",
        "asia-northeast-1": "Osaka, Japan",
        "asia-northeast-2": "Tokyo, Japan",
    }


def fetch_instance_names(api_key: str,
                         api_endpoint: str = "https://cloud.lambdalabs.com/api/v1/instance-types"
                         ) -> set[str]:
    """
    Fetches instance names from the Lambda API.

    This function makes an HTTP GET request to the Lambda API to fetch instance names.
    It expects a JSON response with instance details. It extracts and returns a set
    of instance names.

    Args:
        api_key (str): The API key used for authorization in the request header.
        api_endpoint (str): The URL of the API endpoint to fetch instance types from.

    Returns:
        set[str]: A set of instance names. If the request fails, the function returns
        an empty set. If the request succeeds but the response is not valid JSON, the
        function returns an empty set.

    The function handles connection errors by printing an error message and returning
    an empty set. Other HTTP errors are logged with their status codes and response
    text. The function uses type hints for clarity and type safety.
    """
    headers: Dict[str, str] = {"Authorization": f"Bearer {api_key}"}
    instance_names: Set[str] = set()

    try:
        response: requests.Response = requests.get(api_endpoint, headers=headers)
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
        logging.error(f"Connection error: {e}")
        return instance_names

    if response.status_code == 200:
        data: Dict[str, Any] = response.json().get("data", {})
        for instance, details in data.items():
            # Get the instance name from the instance details
            instance_name = details['instance_type']['name']
            instance_names.add(instance_name)
        return instance_names
    else:
        print(f"Error: {response.status_code} - {response.text}")
        logging.error(f"Error: {response.status_code} - {response.text}")
        return instance_names


def fetch_instance_availabilities(api_key: str,
                                  api_endpoint: str = "https://cloud.lambdalabs.com/api/v1/instance-types"
                                  ) -> Tuple[Optional[datetime], List[InstanceAvailability]]:
    """
    Fetches instance types from a given API endpoint using the provided API key.

    This function makes an HTTP GET request to the specified API endpoint. It expects
    a JSON response with instance details. It extracts and returns a set of available
    instances and a list of InstanceAvailability objects.

    Args:
        api_key (str): The API key used for authorization in the request header.
        api_endpoint (str): The URL of the API endpoint to fetch instance types from.

    Returns:
        Tuple[Optional[datetime], List[InstanceAvailability]]: A tuple containing the
        time the request was made and a list of InstanceAvailability objects. If the
        request fails, the function returns None and an empty list. If the request
        succeeds but the response is not valid JSON, the function returns the time
        the request was made and an empty list.

    The function handles connection errors by printing an error message and returning
    an empty set and list. Other HTTP errors are logged with their status codes
    and response text. The function uses type hints for clarity and type safety.
    """
    headers: Dict[str, str] = {"Authorization": f"Bearer {api_key}"}

    try:
        response: requests.Response = requests.get(api_endpoint, headers=headers)
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
        logging.error(f"Connection error: {e}")
        return None, []

    fetch_time = datetime.now()

    if response.status_code == 200:
        data: Dict[str, Any] = response.json().get("data", {})
        instance_availability_list: List[InstanceAvailability] = []
        for instance, details in data.items():
            if details.get("regions_with_capacity_available"):
                instance_info_data = details['instance_type']
                for region in details['regions_with_capacity_available']:
                    instance_type = InstanceType(
                        name=instance_info_data['name'],
                        description=instance_info_data['description'],
                        region=region['name']
                    )
                    instance_availability = InstanceAvailability(
                        instance_type=instance_type,
                        start_time=fetch_time,
                        last_seen_time=fetch_time
                    )
                    instance_availability_list.append(instance_availability)

        return fetch_time, instance_availability_list
    else:
        print(f"Error: {response.status_code} - {response.text}")
        logging.error(f"Error: {response.status_code} - {response.text}")
        return None, []
