import argparse
import time

import toml

from src.config import Config
from src.monitor import Monitor

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the application with specified configuration.")
    parser.add_argument("config_file", help="Path to the configuration file.")
    args = parser.parse_args()

    # Load the TOML configuration file
    with open(args.config_file, "r") as file:
        config_data = toml.load(file)

    # Create an instance of the Config class, which also sets up logging
    config = Config(**config_data["default"])

    # Create an instance of the Monitor class
    monitor = Monitor(start_time=config.start_time)

    # Start monitoring instance availability
    while True:
        monitor.poll(api_key=config.api_key)
        # Sleep for the configured interval in ms
        time.sleep(config.sleep_interval_ms / 1000)
