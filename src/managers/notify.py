import logging
import os
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, PrivateAttr, Field

from core import smtp
from data_structures.allow import AllowInstances
from managers.configmanager import ConfigManager
from managers.singleton_meta import SingletonMeta, require_initialization


class NotificationEvent(BaseModel):
    """A class for storing the notification event configuration settings."""
    instance_name: str
    region: str
    time: datetime = Field(default_factory=datetime.now)

    class Config:
        frozen = True

    # Ensure that this is sorted by time only
    def __lt__(self, other):
        return self.time < other.time

    def __eq__(self, other):
        return self.time == other.time

    def __ge__(self, other):
        return self.time >= other.time


class NotifyManager(BaseModel, metaclass=SingletonMeta):
    _emails: Optional[List[str]] = PrivateAttr(default=None)
    _allow_instances: Optional[AllowInstances] = PrivateAttr(default=None)
    _enable_voice_notifications: bool = PrivateAttr(default=False)
    _notification_events: List[NotificationEvent] = PrivateAttr(default_factory=list)

    def initialize(self, emails: List[str], allow_instances: AllowInstances, enable_voice_notifications: bool):
        """Private method to initialize private attributes."""
        self._emails = emails
        self._allow_instances = allow_instances
        self._enable_voice_notifications = enable_voice_notifications

    @classmethod
    @require_initialization
    def can_notify(cls, instance_name: str, region: str) -> bool:
        """Check if the instance_name and region are in the computed sets."""
        return cls._allow_instances.is_allowed(instance_name, region)

    @classmethod
    @require_initialization
    def attempt_to_notify(cls, instance_name: str, region: str) -> bool:
        """Attempt to send a notification for the instance_name and region."""
        if cls.can_notify(instance_name, region):
            try:
                # Send a voice notification if enabled
                if ConfigManager.enable_voice_notifications:
                    os.system(f'say "Instance {instance_name} in {region} is available."')
                    logging.info(f"Voice notification occurred for {instance_name} in {region}.")

                if ConfigManager.notify_emails:
                    smtp.send_email_using_config(
                        subject=f"Instance notification {instance_name}:{region}",
                        text_content=f"Instance {instance_name} in {region} is available.",
                        do_log_success=True
                    )
                    logging.info(f"Notification sent for {instance_name} in {region} to {cls._emails}.")

                return True
            except Exception as e:
                logging.error(f"Error sending notification for {instance_name} in {region} to {cls._emails}: {e}")

        # Did not send a notification
        logging.info(f"Notification evaluated but not sent for {instance_name} in {region}.")
        return False
