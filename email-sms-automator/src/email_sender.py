"""
email-sms-automator/src/email_sender.py
Handles sending emails via SMTP protocol with TLS encryption, attachments, and error handling.
"""

import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
try:
    from .utils import setup_logging
except ImportError:
    from utils import setup_logging


logger = setup_logging(__name__)


class EmailSender:
    """
    Handles sending emails via SMTP.
    Supports TLS, plain text/HTML content, and file attachments.
    """

    def __init__(self, smtp_server: str, smtp_port: int, sender_email: str, sender_password: str):
        """
        Initializes the EmailSender with server credentials and connection details.

        :param smtp_server: SMTP server hostname (e.g., 'smtp.gmail.com').
        :param smtp_port: SMTP server port (e.g., 587 for TLS).
        :param sender_email: Sender email address.
        :param sender_password: App password or authentication token.
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.server = None
        logger.info(f"EmailSender initialized for {sender_email} via {smtp_server}:{smtp_port}.")

    def _connect(self) -> bool:
        """
        Establishes and logs into the SMTP server using STARTTLS encryption.

        :return: True if connection and authentication succeed, False otherwise.
        """
        try:
            self.server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            self.server.starttls()  # Secure the connection
            self.server.login(self.sender_email, self.sender_password)
            logger.info("Successfully connected and logged into SMTP server.")
            return True
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed. Check email and app password. Error: {e}")
            self.server = None
            return False
        except smtplib.SMTPConnectError as e:
            logger.error(f"SMTP connection failed. Check server address and port. Error: {e}")
            self.server = None
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during SMTP connect/login: {e}")
            self.server = None
            return False

    def _disconnect(self) -> None:
        """
        Disconnects safely from the SMTP server.
        """
        if self.server:
            try:
                self.server.quit()
                logger.info("Disconnected from SMTP server.")
            except Exception as e:
                logger.warning(f"Error during SMTP disconnection: {e}")
            finally:
                self.server = None

    def send_email(
        self,
        recipient_email: str,
        subject: str,
        body: str,
        attachment_path: str = None,
        is_html: bool = False
    ) -> bool:
        """
        Sends an email to the specified recipient.

        :param recipient_email: The email address of the recipient.
        :param subject: The subject line of the email.
        :param body: The content of the email.
        :param attachment_path: Optional path to a file to attach.
        :param is_html: Set to True if the body is HTML, False for plain text.
        :return: True if email sent successfully, False otherwise.
        """
        if not self._connect():
            return False

        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject

        # Attach body
        if is_html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))

        # Attach file if path is provided
        if attachment_path:
            try:
                with open(attachment_path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
                    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
                    msg.attach(part)
                logger.info(f"Attached file: {attachment_path}")
            except FileNotFoundError:
                logger.error(f"Attachment file not found: {attachment_path}. Email will be sent without it.")
            except Exception as e:
                logger.error(f"Error attaching file {attachment_path}: {e}. Email will be sent without it.")

        try:
            self.server.send_message(msg)
            logger.info(f"Email sent successfully to {recipient_email} with subject: '{subject}'.")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}. Error: {e}")
            return False
        finally:
            self._disconnect()
