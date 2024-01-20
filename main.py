import argparse
import time

import toml

from src.config import Config
from src.monitor import Monitor

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the application with specified configuration.")
    parser.add_argument("config_file", help="Path to the configuration file.")
    parser.add_argument("namespace", help="TOML configuration namespace.")
    args = parser.parse_args()

    # Attempt to load the TOML configuration file
    try:
        with open(args.config_file, "r") as file:
            config_data = toml.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"The configuration file '{args.config_file}' was not found.")

    # Ensure the specified namespace exists
    if args.namespace not in config_data:
        raise ValueError(f"Namespace '{args.namespace}' not found in the configuration file.")

    # Get the configuration for the specified namespace
    namespace_config = config_data[args.namespace]

    # Create an instance of the Config class, which also sets up logging
    config = Config(**namespace_config)

    # Create an instance of the Monitor class
    monitor = Monitor(api_key=config.api_key, start_time=config.start_time)

    # Start monitoring instance availability
    while True:
        monitor.poll()
        # Sleep for the configured interval in ms
        time.sleep(config.sleep_interval_ms / 1000)
