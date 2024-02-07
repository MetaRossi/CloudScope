import logging
import smtplib
from email.message import EmailMessage
from typing import Set, List

from core.console import print_console_message
from managers.configmanager import ConfigManager


# NOTE: Email setup for Gmail and iCloud/me.com
#       Gmail SMTP server and port: smtp.gmail.com / 465
#       iCloud SMTP server and port: smtp.mail.me.com / 587


def check_login(smtp_server: str, smtp_port: int,
                email_sender: str, email_password: str
                ) -> bool:
    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as smtp:
            smtp.login(email_sender, email_password)
        print_console_message(message=f"SMTP login successful for: {email_sender}")
        logging.info("SMTP login successful for: {email_sender}")
        return True
    except smtplib.SMTPAuthenticationError:
        logging.error("SMTP login failed: authentication error. Check config email_sender and email_password.")
    except Exception as e:
        logging.error(f"SMTP login failed: {e}")
    return False


def send_email(smtp_server: str, smtp_port: int,
               email_sender: str, email_password: str,
               recipient_emails: List[str],
               subject: str, text_content: str,
               do_log_success: bool = False
               ) -> bool:
    try:
        # Create the email message
        em = EmailMessage()
        em['From'] = email_sender
        em['To'] = set(recipient_emails)  # Convert to set to remove duplicates
        em['Subject'] = subject + "\n"
        em.set_content(text_content)

        with smtplib.SMTP_SSL(smtp_server, smtp_port) as smtp:
            smtp.login(email_sender, email_password)
            smtp.send_message(em)

        if do_log_success:
            print_console_message(message=f"Email sent successfully to: {recipient_emails}: {subject}: {text_content}")
            logging.info(f"Email sent successfully to: {recipient_emails}: {subject}: {text_content}")
        return True
    except Exception as e:
        print_console_message(message="ERROR: SMTP failure. Failed to send email. See log for details.")
        logging.error(f"SMTP failure. Failed to send email: {e}")
        return False


def send_email_using_config(subject: str, text_content: str, do_log_success: bool = False) -> bool:
    return send_email(
        smtp_server=ConfigManager.smtp_server,
        smtp_port=ConfigManager.smtp_port,
        email_sender=ConfigManager.email_sender,
        email_password=ConfigManager.email_password,
        recipient_emails=ConfigManager.notify_emails,
        subject=subject,
        text_content=text_content,
        do_log_success=do_log_success
    )
