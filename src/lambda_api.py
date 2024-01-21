import logging
from datetime import datetime
from typing import Tuple, Dict, Any, List, Optional

import requests

from src.data_structures import InstanceAvailability, InstanceType


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
