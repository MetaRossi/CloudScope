import logging
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class Config(BaseModel):
    """
    A configuration class for storing application settings.

    This class uses Pydantic for data validation and management. It is designed
    to load and store various configuration parameters used throughout the application.
    The class is immutable (frozen), meaning that once an instance is created,
    its fields cannot be modified.

    Attributes:
        sleep_interval_ms (int): The sleep interval in milliseconds.
        log_dir (Path): The directory path for logs.
        start_time (str): The start time in ISO 8601 format.
        api_key (str): The API key.

    Methods:
        check_log_dir_exists: A field validator for 'log_dir' to ensure the log directory exists.
    """

    sleep_interval_ms: int
    log_dir: Path = Field(...)
    start_time: str = Field(default_factory=lambda: datetime.now().isoformat(timespec='seconds'))
    log_file: Path = Field(default_factory=lambda: Path(datetime.now().strftime("%Y%m%d_%H%M%S.log")))
    api_key: str

    class Config:
        """
        Configuration class for Pydantic model behavior.

        This nested class is used to configure the behavior of the parent Pydantic model.
        """
        frozen = True  # Set the model to be immutable

    def __init__(self, **data):
        super().__init__(**data)
        self.setup_logging()

    @field_validator('log_dir', mode='before')
    def check_log_dir_exists(cls, v: str) -> Path:
        """
        Validator to ensure the log directory exists, creates it if it doesn't.

        Args:
            v (str): The string representation of the log directory path.

        Returns:
            Path: The Path object for the log directory.
        """
        log_dir_path = Path(v)
        log_dir_path.mkdir(parents=True, exist_ok=True)
        return log_dir_path

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

        print(f"Logging to: {self.log_file}")
        logging.info(f"Starting job at: {self.start_time}")
        logging.info(f"Sleep Interval (ms): {self.sleep_interval_ms}")

