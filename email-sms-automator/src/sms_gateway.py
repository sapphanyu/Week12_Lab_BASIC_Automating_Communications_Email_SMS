"""
email-sms-automator/src/sms_gateway.py
Provides a simplified interface to dispatch SMS text messages via carrier email-to-SMS gateways.
"""

from typing import Optional
try:
    from .email_sender import EmailSender
    from .utils import setup_logging
except ImportError:
    from email_sender import EmailSender
    from utils import setup_logging


logger = setup_logging(__name__)


class SMSGateway:
    """
    Provides a simplified interface to send SMS via email-to-SMS gateways.
    Relies on an EmailSender instance for transmission.
    """

    def __init__(self, email_sender_instance: EmailSender):
        """
        Initializes the SMSGateway with an active EmailSender instance.

        :param email_sender_instance: An instance of EmailSender.
        :raises TypeError: If the provided instance is not an EmailSender.
        """
        if not isinstance(email_sender_instance, EmailSender):
            raise TypeError("SMSGateway requires an instance of EmailSender.")

        self.email_sender = email_sender_instance

        # Common US carrier email-to-SMS gateways
        self.carrier_gateways = {
            "att": "@txt.att.net",
            "verizon": "@vtext.com",
            "tmobile": "@tmomail.net",
            "sprint": "@messaging.sprintpcs.com",
            "boost": "@sms.boostmobile.com",
            "cricket": "@mms.cricketwireless.net",
            "us_cellular": "@email.uscc.net",
        }
        logger.info("SMSGateway initialized.")

    def send_sms(self, phone_number: str, message: str, carrier_name: Optional[str] = None) -> bool:
        """
        Sends an SMS message via email-to-SMS gateway.

        :param phone_number: Recipient phone number (e.g., '1234567890') or full gateway email.
        :param message: The text message content.
        :param carrier_name: Optional carrier key ('att', 'verizon', 'tmobile', etc.).
        :return: True if message was successfully dispatched via email, False otherwise.
        """
        sms_gateway_address = None

        if carrier_name and carrier_name.lower() in self.carrier_gateways:
            sms_gateway_address = f"{phone_number}{self.carrier_gateways[carrier_name.lower()]}"
        elif '@' in phone_number and '.' in phone_number:
            # Assume phone_number is already a full gateway address
            sms_gateway_address = phone_number
        else:
            logger.warning(
                "No specific carrier provided and phone number is not a gateway address. Cannot send SMS."
            )
            return False

        if sms_gateway_address:
            subject = ""  # SMS email gateways typically ignore or omit subject lines
            logger.info(f"Attempting to send SMS to {phone_number} via gateway: {sms_gateway_address}")
            return self.email_sender.send_email(
                recipient_email=sms_gateway_address,
                subject=subject,
                body=message
            )
        else:
            logger.error("Could not determine SMS gateway address.")
            return False
