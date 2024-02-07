import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

from email_validator import validate_email, EmailNotValidError
from pydantic import BaseModel, Field, field_validator, PrivateAttr

from core import lambda_api, smtp
from data_structures.allow import AllowInstances
from data_structures.launch import LaunchInstances
from managers.singleton_meta import SingletonMeta


# TODO convert to just use JSON as the config file


class ConfigManager(BaseModel, metaclass=SingletonMeta):
    """
    A configuration class for storing application settings.

    This class uses Pydantic for data validation and management. It is designed
    to load and store various configuration parameters used throughout the application.
    The class is immutable (frozen), meaning that once an instance is created,
    its fields cannot be modified.

    Attributes:
        min_poll_delay_ms (int): The minimum poll delay in milliseconds.
        log_dir (Path): The directory for storing log files.
        api_key (str): The API key for accessing the Lambda API.
        console_instances (List[str]): A list of instance names to monitor and log to the console.
        notify_instances (List[str]): A list of instance names to monitor and send notifications for.
        notify_emails (List[str]): A list of email addresses to send notifications to.
        launch_instances (List[str]): A list of instance names to monitor and launch instances for.
        launch_emails (List[str]): A list of email addresses to send launch notifications to.
        launch_total_max_instances (int): The total maximum number of instances to launch across all regions.
        enable_voice_notifications (bool): A flag to enable voice notifications.
        new_regions (Dict[str, str]): A dictionary of new regions to add to the Lambda API region dictionary.
        email_sender (Optional[str]): The email address to send notifications from.
        email_password (Optional[str]): The password for the email address to send notifications from.
        smtp_server (Optional[str]): The SMTP server to use for sending emails.
        smtp_port (Optional[int]): The SMTP port to use for sending emails.
        send_info_emails_at_startup (bool): A flag to send info emails at startup.


    Methods:
        setup_logging(): Sets up logging based on the configuration.
        now_formatted_str(input_datetime: Optional[datetime] = None): Returns a formatted string of the current time.
        add_new_logged_region(region: str): Adds a new region to the set of new logged regions.
        get_new_logged_regions(): Returns the set of new logged regions.
    """
    # Required fields
    min_poll_delay_ms: int = Field(frozen=True)
    log_dir: Path = Field(frozen=True)
    api_key: str = Field(frozen=True)
    # Optional fields
    console_instances: List[str] = Field(default_factory=set, frozen=True)
    notify_instances: List[str] = Field(default_factory=set, frozen=True)
    notify_emails: List[str] = Field(default_factory=set, frozen=True)
    launch_instances: List[str] = Field(default_factory=set, frozen=True)
    launch_emails: List[str] = Field(default_factory=set, frozen=True)
    launch_total_max_instances: int = Field(default=0, frozen=True, ge=0)
    enable_voice_notifications: bool = Field(default=False, frozen=True)
    new_regions: Dict[str, str] = Field(default_factory=dict, frozen=True)
    email_sender: Optional[str] = Field(default=None, frozen=True)
    email_password: Optional[str] = Field(default=None, frozen=True)
    smtp_server: Optional[str] = Field(default=None, frozen=True)
    smtp_port: Optional[int] = Field(default=None, frozen=True)
    send_info_emails_at_startup: bool = Field(default=True, frozen=True)
    # Loaded from the Lambda API
    _instance_names: set = PrivateAttr(default_factory=set)
    _regions_dict: dict = PrivateAttr(default_factory=dict)
    # Handled in code
    start_time: datetime = Field(default_factory=datetime.now, frozen=True)
    _start_time_str: str = PrivateAttr(default_factory=str)
    _log_file: Path = PrivateAttr(default_factory=lambda: Path(datetime.now().strftime("%Y%m%d_%H%M%S.log")))
    _new_logged_regions: set = PrivateAttr(default_factory=set)
    _console_instances: Optional[AllowInstances] = PrivateAttr(default=None)
    _notify_instances: Optional[AllowInstances] = PrivateAttr(default=None)
    _launch_instances: Optional[LaunchInstances] = PrivateAttr(default=None)

    def __init__(self, **data):
        super().__init__(**data)

        # Set the start time string
        self._start_time_str = self.start_time.isoformat(timespec='seconds')

        # Set up logging
        self.setup_logging()

        # Fetch regions from the Lambda API
        self._regions_dict = lambda_api.static_dict_of_known_regions()
        self._regions_dict.update(self.new_regions)  # Add any new regions from the config file
        print(f"{ConfigManager.now_formatted_str()} - Regions: {self._regions_dict}")
        logging.info(f"Regions: {self._regions_dict}")

        # Fetch instance names from the Lambda API
        self._instance_names = lambda_api.fetch_instance_names(self.api_key)
        print(f"{ConfigManager.now_formatted_str()} - Instance names: {self._instance_names}")
        logging.info(f"Instance names: {self._instance_names}")
        time.sleep(self.min_poll_delay_ms / 1000)

        # Parse the instance and region filters from JSON using Pydantic
        self._console_instances = AllowInstances.from_config_json_array(self.console_instances,
                                                                        self._instance_names,
                                                                        set(self._regions_dict.keys()))
        self._notify_instances = AllowInstances.from_config_json_array(self.notify_instances,
                                                                       self._instance_names,
                                                                       set(self._regions_dict.keys()))
        self._launch_instances = LaunchInstances.from_config_json_array(self.launch_instances,
                                                                        self._instance_names,
                                                                        set(self._regions_dict.keys()))

        # Log the computed sets
        self._console_instances.log_allow_instances("console")
        self._notify_instances.log_allow_instances("notify")
        self._launch_instances.log_launch_instances("launch")

        # Validate all emails and raise a single error if any are invalid
        invalid_emails = []
        for email in self.notify_emails + self.launch_emails:
            try:
                validate_email(email)
            except EmailNotValidError:
                invalid_emails.append(email)
        if invalid_emails:
            raise ValueError(f"Invalid email(s): {invalid_emails}")

        # Log the email addresses and voice notifications
        logging.info(f"Notify emails: {self.notify_emails}")
        logging.info(f"Launch emails: {self.launch_emails}")
        logging.info(f"Enable voice notifications set to: {self.enable_voice_notifications}")
        logging.info(f"Send info emails at startup set to: {self.send_info_emails_at_startup}")

        # Check and log email sender and password
        if self.email_sender is not None and self.email_password is not None:
            try:
                validate_email(self.email_sender)
            except EmailNotValidError:
                raise ValueError(f"Invalid email: {self.email_sender}")

            logging.info(f"Email sender: {self.email_sender}")
            logging.info(f"Email password: <<REDACTED>>")
            logging.info(f"SMTP server: {self.smtp_server}")
            logging.info(f"SMTP port: {self.smtp_port}")

            if self.smtp_server is not None and self.smtp_port is not None:
                try:
                    if not self.send_info_emails_at_startup:
                        smtp.check_login(self.smtp_server, self.smtp_port,
                                         self.email_sender, self.email_password)
                    else:
                        subject = "Lambda Monitor Startup Email"
                        text_content = f"Lambda Monitor started at: {self._start_time_str}"
                        smtp.send_email(self.smtp_server, self.smtp_port,
                                        self.email_sender, self.email_password,
                                        set(self.notify_emails + self.launch_emails),
                                        subject, text_content, do_log_success=True)
                except Exception as e:
                    raise ValueError(f"SMTP check login failed: {e}")
            elif self.smtp_server is None and self.smtp_port is None:
                raise ValueError("SMTP server and port not set. Set smtp_server and smtp_port in the config file.")
            elif self.smtp_server is None:
                raise ValueError("SMTP server not set. Set smtp_server in the config file.")
            elif self.smtp_port is None:
                raise ValueError("SMTP port not set. Set smtp_port in the config file.")

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
            filename=self.log_dir / self._log_file,
            level=logging.INFO,
            format="%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        print(f"{ConfigManager.now_formatted_str()} - Logging to: {self._log_file}")
        logging.info(f"Starting job at: {self._start_time_str}")
        logging.info(f"Target sleep Interval (ms): {self.min_poll_delay_ms}")

    @staticmethod
    def now_formatted_str(input_datetime: Optional[datetime] = None) -> str:
        if input_datetime is not None:
            return input_datetime.strftime("%Y-%m-%d %H:%M:%S.%f")
        else:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    def add_new_logged_region(self, region: str) -> None:
        """
        Adds a new region to the set of new logged regions.

        Args:
            region (str): The region to add to the set.
        """
        self._new_logged_regions.add(region)

    def get_new_logged_regions(self) -> set:
        """
        Returns the set of new logged regions.

        Returns:
            set: The set of new logged regions.
        """
        return self._new_logged_regions
