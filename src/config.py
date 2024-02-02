import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from src import lambda_api


class Config(BaseModel):
    """
    A configuration class for storing application settings.

    This class uses Pydantic for data validation and management. It is designed
    to load and store various configuration parameters used throughout the application.
    The class is immutable (frozen), meaning that once an instance is created,
    its fields cannot be modified.

    Attributes:
        min_poll_delay_ms (int): The minimum delay between API requests in milliseconds.
        log_dir (Path): The directory path for logs.
        start_time_str (str): The start time in ISO 8601 format.
        api_key (str): The API key.

    Methods:
        check_log_dir_exists: A field validator for 'log_dir' to ensure the log directory exists.
    """
    # Required fields
    min_poll_delay_ms: int = Field(frozen=True)
    log_dir: Path = Field(frozen=True)
    api_key: str = Field(frozen=True)
    # Optional fields
    enable_voice_notifications: bool = Field(default=False, frozen=True)
    # TODO add instance filter fields
    # TODO region should support 'us*' and '*' wildcards
    # Loaded from the Lambda API
    instance_names: set = Field(default_factory=set)
    regions_dict: dict = Field(default_factory=dict)
    # Handled in code
    start_time: datetime = Field(default_factory=datetime.now, frozen=True)
    start_time_str: str = Field(default_factory=str)
    log_file: Path = Field(default_factory=lambda: Path(datetime.now().strftime("%Y%m%d_%H%M%S.log")), frozen=True)
    new_logged_regions: set = Field(default_factory=set)

    def __init__(self, **data):
        super().__init__(**data)

        # Set the start time string
        self.start_time_str = self.start_time.isoformat(timespec='seconds')

        # Set up logging
        self.setup_logging()

        # Fetch regions from the Lambda API
        self.regions_dict = lambda_api.static_dict_of_known_regions()
        print(f"{Config.now_formatted_str()} - Regions: {self.regions_dict}")
        logging.info(f"Regions: {self.regions_dict}")

        # Fetch instance names from the Lambda API
        self.instance_names = lambda_api.fetch_instance_names(self.api_key)
        print(f"{Config.now_formatted_str()} - Instance names: {self.instance_names}")
        logging.info(f"Instance names: {self.instance_names}")
        time.sleep(self.min_poll_delay_ms / 1000)

        # TODO load instance filters from config file and deconflict

    # noinspection PyMethodParameters
    @field_validator('log_dir', mode='before')
    def check_log_dir_exists(cls, log_dir_str: str) -> Path:
        """
        Validator to ensure the log directory exists, creates it if it doesn't.

        Args:
            log_dir_str (str): The string representation of the log directory path.

        Returns:
            Path: The Path object for the log directory.
        """
        log_dir_path = Path(log_dir_str)
        log_dir_path.mkdir(parents=True, exist_ok=True)
        return log_dir_path

    @field_validator('min_poll_delay_ms', mode='before')
    def check_min_poll_delay_ms(cls, min_poll_delay_ms: int) -> int:
        """
        Validator to ensure the minimum poll delay is at least 1100 ms.

        Args:
            min_poll_delay_ms (int): The minimum poll delay in milliseconds.

        Returns:
            int: The minimum poll delay in milliseconds.
        """
        # Validate the minimum poll delay
        if min_poll_delay_ms < 1100:
            raise ValueError("Minimum poll delay must be at least 1100 ms. "
                             "Lambda API rate limit is 1 request per second. "
                             "There is some variability in processing time so 1100 ms is safe.")

        return min_poll_delay_ms

    def setup_logging(self):
        """
        Sets up logging based on the configuration.

        Configures the basic logging setup with the filename, log level,
        and format as specified in the configuration.
        """
        logging.basicConfig(
            filename=self.log_dir / self.log_file,
            level=logging.INFO,
            format="%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        print(f"{Config.now_formatted_str()} - Logging to: {self.log_file}")
        logging.info(f"Starting job at: {self.start_time_str}")
        logging.info(f"Target sleep Interval (ms): {self.min_poll_delay_ms}")

    @staticmethod
    def now_formatted_str(input_datetime: Optional[datetime] = None) -> str:
        if input_datetime is not None:
            return input_datetime.strftime("%Y-%m-%d %H:%M:%S.%f")
        else:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
