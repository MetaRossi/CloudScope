from typing import Tuple, Set, Dict, Any

import requests


def fetch_instance_types(api_key: str,
                         api_endpoint: str = "https://cloud.lambdalabs.com/api/v1/instance-types"
                         ) -> Tuple[Set[str], Dict[str, Any]]:
    """
    Fetches instance types from a given API endpoint using the provided API key.

    This function makes an HTTP GET request to the specified API endpoint. It expects
    a JSON response with instance details. It extracts and returns a set of available
    instances and the complete data as a dictionary.

    Args:
        api_key (str): The API key used for authorization in the request header.
        api_endpoint (str): The URL of the API endpoint to fetch instance types from.

    Returns:
        Tuple[Set[str], Dict[str, Any]]: A tuple containing two elements:
            - A set of instance type strings that have capacity available.
            - A dictionary containing the complete data of all instance types.

    The function handles connection errors by printing an error message and returning
    an empty set and dictionary. Other HTTP errors are logged with their status codes
    and response text. The function uses type hints for clarity and type safety.
    """
    # Prepare the headers for the HTTP request with the provided API key
    headers: Dict[str, str] = {"Authorization": f"Bearer {api_key}"}

    try:
        # Perform the HTTP GET request to the API endpoint
        response: requests.Response = requests.get(api_endpoint, headers=headers)
    except requests.exceptions.ConnectionError as e:
        # Handle and print connection errors, then return empty set and dictionary
        print(f"Connection error: {e}")
        return set(), {}

    if response.status_code == 200:
        # Parse the JSON response and get the 'data' section
        data: Dict[str, Any] = response.json().get("data", {})
        available_instances: Set[str] = set()

        # Iterate over each instance in the data
        for instance, details in data.items():
            # Check if regions with capacity are available and add to the set
            if details.get("regions_with_capacity_available"):
                available_instances.add(instance)

        # Return the set of available instances and the complete data
        return available_instances, data
    else:
        # Print error details for non-200 HTTP responses and return empty set and dictionary
        print(f"Error: {response.status_code} - {response.text}")
        return set(), {}
