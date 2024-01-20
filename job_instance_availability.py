# Docs: https://cloud.lambdalabs.com/api/v1/docs#operation/instanceTypes

import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Tuple

import requests

# Constants
API_ENDPOINT = "https://cloud.lambdalabs.com/api/v1/instance-types"
SLEEP_INTERVAL = 1  # in seconds; they rate limit if polling at less than 1 second
PROJECT_ROOT = Path(os.getcwd())
API_KEY_FILE = PROJECT_ROOT / "__config/lambda_labs_key_python.txt"  # Just `secret_python_...` in the file
LOG_DIR = PROJECT_ROOT / "__logs"
START_TIME = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"instance_availability/{START_TIME}.log"

# Setup logging
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")

# Global map to store instance types and their availability times
instance_map = {}


def read_api_key(file_path: str) -> str:
    with open(file_path, "r") as file:
        return file.read().strip()


def log_instance_info(instance_type: str, region_name: str, status: str, start_time: datetime = None) -> None:
    # Log info of the instance type for a specific region
    end_time = datetime.now()

    if status == "Not Available" and start_time is not None:
        duration = end_time - start_time
        logging.info(
            f"Instance Type: {instance_type}, Region: {region_name} - "
            f"Status: {status} - "
            f"Start: {start_time} - "
            f"End: {end_time} - "
            f"Duration: {duration}"
        )
    elif status == "Available":
        if start_time is None:
            start_time = end_time
        duration = end_time - start_time
        logging.info(
            f"Instance Type: {instance_type}, Region: {region_name} - "
            f"Status: {status} - "
            f"Start: {start_time} - "
            f"Duration: {duration}"
        )
    else:
        logging.error(f"Invalid status for Instance Type: {instance_type}, Region: {region_name} - Status: {status}")


def fetch_instance_types(api_key: str) -> Tuple[set, dict]:
    headers = {"Authorization": f"Bearer {api_key}"}

    # Handle connectivity error
    try:
        response = requests.get(API_ENDPOINT, headers=headers)
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
        return set(), {}

    if response.status_code == 200:
        data = response.json().get("data", {})
        available_instances = set()
        for instance, details in data.items():
            if details["regions_with_capacity_available"]:
                available_instances.add(instance)
        return available_instances, data
    else:
        # Print other errors
        print(f"Error: {response.status_code} - {response.text}")
        return set(), {}


def monitor_instance_types() -> None:
    api_key = read_api_key(str(API_KEY_FILE))
    is_first_iteration = True
    first_unavailability_time = None
    previous_message_length = 0
    last_status_found_available_status = False

    while True:
        current_types, data = fetch_instance_types(api_key)

        current_available = set()
        found_available = False  # Flag to track if any available instances are found in this iteration

        for instance_type, details in data.items():
            regions = details["regions_with_capacity_available"]
            for region in regions:
                region_name = region["name"]
                key = (instance_type, region_name)
                current_available.add(key)
                if key not in instance_map:
                    # New instance-region pair found, log as available
                    instance_map[key] = {"start_time": datetime.now(), "region": region_name}
                    log_instance_info(instance_type, region_name, "Available")
                    found_available = True

        # Check for instances that have become unavailable
        for key in list(instance_map):
            if key not in current_available:
                instance_type, region_name = key
                start_time = instance_map[key]["start_time"]
                log_instance_info(instance_type, region_name, "Not Available", start_time)
                del instance_map[key]

        # Create message to print to console
        some_available = len(current_available) > 0
        if some_available:
            available_instances = [f"{key[0]} in {key[1]}" for key in current_available]
            message = f"{datetime.now()} Available instances: {', '.join(available_instances)}"
            first_unavailability_time = None
        else:
            if not first_unavailability_time:
                first_unavailability_time = datetime.now()
            current_time = datetime.now()
            duration = current_time - first_unavailability_time
            message = (
                f"{current_time} No instances available since {first_unavailability_time} " f"(Duration: {duration})"
            )

        # Print message to console
        if last_status_found_available_status != found_available and not is_first_iteration:
            print()  # Print a new line
        print("\r" + " " * previous_message_length, end="")  # Clear previous message
        print("\r" + message, end="")  # Print new message
        sys.stdout.flush()
        previous_message_length = len(message)

        last_status_found_available_status = found_available

        is_first_iteration = False

        time.sleep(SLEEP_INTERVAL)


if __name__ == "__main__":
    print("Logging to:", LOG_FILE)
    logging.info(f"Starting instance availability monitor")
    monitor_instance_types()
