"""
Unit test suite for email-sms-automator.
Uses unittest and unittest.mock to thoroughly test all components offline.
"""

import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import smtplib
import imaplib
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add src/ to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from utils import ensure_directory_exists, get_env_variable, setup_logging
from email_sender import EmailSender
from email_receiver import EmailReceiver
from sms_gateway import SMSGateway


class TestUtils(unittest.TestCase):
    """Tests for utils.py helper functions."""

    def test_setup_logging(self):
        logger = setup_logging("test_logger")
        self.assertEqual(logger.name, "test_logger")
        initial_handlers_count = len(logger.handlers)
        # Calling again should not add duplicate handlers
        logger2 = setup_logging("test_logger")
        self.assertEqual(len(logger2.handlers), initial_handlers_count)

    def test_get_env_variable_success(self):
        with patch.dict(os.environ, {"TEST_KEY": "sample_value"}):
            self.assertEqual(get_env_variable("TEST_KEY"), "sample_value")

    def test_get_env_variable_missing_raises_value_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as ctx:
                get_env_variable("NON_EXISTENT_VAR")
            self.assertIn("NON_EXISTENT_VAR", str(ctx.exception))

    def test_ensure_directory_exists(self):
        test_dir = os.path.join(os.path.dirname(__file__), "temp_test_dir")
        try:
            ensure_directory_exists(test_dir)
            self.assertTrue(os.path.isdir(test_dir))
        finally:
            if os.path.exists(test_dir):
                os.rmdir(test_dir)


class TestEmailSender(unittest.TestCase):
    """Tests for EmailSender class."""

    def setUp(self):
        self.sender = EmailSender(
            smtp_server="smtp.example.com",
            smtp_port=587,
            sender_email="sender@example.com",
            sender_password="secret_password"
        )

    @patch("smtplib.SMTP")
    def test_connect_success(self, mock_smtp_class):
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp

        result = self.sender._connect()
        self.assertTrue(result)
        mock_smtp_class.assert_called_once_with("smtp.example.com", 587)
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("sender@example.com", "secret_password")

    @patch("smtplib.SMTP")
    def test_connect_authentication_error(self, mock_smtp_class):
        mock_smtp = MagicMock()
        mock_smtp.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Auth failed")
        mock_smtp_class.return_value = mock_smtp

        result = self.sender._connect()
        self.assertFalse(result)
        self.assertIsNone(self.sender.server)

    @patch("smtplib.SMTP")
    def test_connect_connection_error(self, mock_smtp_class):
        mock_smtp_class.side_effect = smtplib.SMTPConnectError(421, "Connection refused")

        result = self.sender._connect()
        self.assertFalse(result)
        self.assertIsNone(self.sender.server)

    @patch.object(EmailSender, "_connect", return_value=True)
    @patch.object(EmailSender, "_disconnect")
    def test_send_email_plaintext(self, mock_disconnect, mock_connect):
        mock_server = MagicMock()
        self.sender.server = mock_server

        success = self.sender.send_email(
            recipient_email="recipient@example.com",
            subject="Test Subject",
            body="Hello Plaintext",
            is_html=False
        )

        self.assertTrue(success)
        mock_server.send_message.assert_called_once()
        sent_msg = mock_server.send_message.call_args[0][0]
        self.assertEqual(sent_msg['From'], "sender@example.com")
        self.assertEqual(sent_msg['To'], "recipient@example.com")
        self.assertEqual(sent_msg['Subject'], "Test Subject")
        mock_disconnect.assert_called_once()

    @patch.object(EmailSender, "_connect", return_value=True)
    @patch.object(EmailSender, "_disconnect")
    def test_send_email_with_missing_attachment_continues(self, mock_disconnect, mock_connect):
        mock_server = MagicMock()
        self.sender.server = mock_server

        # When attachment does not exist, it should still send the email without throwing an unhandled exception
        success = self.sender.send_email(
            recipient_email="recipient@example.com",
            subject="Test Attachment",
            body="Hello with missing attachment",
            attachment_path="non_existent_file.pdf"
        )
        self.assertTrue(success)
        mock_server.send_message.assert_called_once()


class TestEmailReceiver(unittest.TestCase):
    """Tests for EmailReceiver class."""

    def setUp(self):
        self.receiver = EmailReceiver(
            imap_server="imap.example.com",
            sender_email="receiver@example.com",
            sender_password="secret_password"
        )

    @patch("imaplib.IMAP4_SSL")
    def test_connect_success(self, mock_imap_class):
        mock_imap = MagicMock()
        mock_imap_class.return_value = mock_imap

        result = self.receiver._connect()
        self.assertTrue(result)
        mock_imap_class.assert_called_once_with("imap.example.com")
        mock_imap.login.assert_called_once_with("receiver@example.com", "secret_password")

    @patch("imaplib.IMAP4_SSL")
    def test_connect_auth_failure(self, mock_imap_class):
        mock_imap = MagicMock()
        mock_imap.login.side_effect = imaplib.IMAP4.error("Authentication failed")
        mock_imap_class.return_value = mock_imap

        result = self.receiver._connect()
        self.assertFalse(result)
        self.assertIsNone(self.receiver.mail)

    @patch.object(EmailReceiver, "_connect", return_value=True)
    @patch.object(EmailReceiver, "_disconnect")
    def test_search_emails(self, mock_disconnect, mock_connect):
        mock_mail = MagicMock()
        mock_mail.search.return_value = ('OK', [b'101 102 103'])
        self.receiver.mail = mock_mail

        uids = self.receiver.search_emails(
            mailbox='INBOX',
            criteria='UNSEEN',
            from_sender='boss@example.com',
            subject_contains='Urgent'
        )

        self.assertEqual(uids, [b'101', b'102', b'103'])
        mock_mail.select.assert_called_once_with('INBOX')
        mock_mail.search.assert_called_once_with(None, 'UNSEEN', 'FROM', 'boss@example.com', 'SUBJECT', 'Urgent')
        mock_disconnect.assert_called_once()

    def test_decode_header_part(self):
        # ASCII string
        self.assertEqual(self.receiver._decode_header_part("Simple Subject"), "Simple Subject")
        # Encoded UTF-8 base64
        encoded = "=?utf-8?b?4Lih4Li04LmI4LiH4LiX4LmI4Lin4LiH?="
        decoded = self.receiver._decode_header_part(encoded)
        self.assertIsInstance(decoded, str)
        self.assertTrue(len(decoded) > 0)
        # None header
        self.assertEqual(self.receiver._decode_header_part(None), "")

    @patch.object(EmailReceiver, "_connect", return_value=True)
    @patch.object(EmailReceiver, "_disconnect")
    def test_fetch_email_content(self, mock_disconnect, mock_connect):
        mock_mail = MagicMock()
        self.receiver.mail = mock_mail

        msg = MIMEMultipart()
        msg['From'] = 'sender@example.com'
        msg['Subject'] = 'Test Subject'
        msg.attach(MIMEText('This is the test body content for snippet extraction.', 'plain'))

        mock_mail.fetch.return_value = ('OK', [(b'1 (RFC822 {100})', msg.as_bytes())])

        details = self.receiver.fetch_email_content(uid=b'1', mark_as_read=True)

        self.assertIsNotNone(details)
        self.assertEqual(details['uid'], '1')
        self.assertEqual(details['sender'], 'sender@example.com')
        self.assertEqual(details['subject'], 'Test Subject')
        self.assertIn('test body content', details['body_snippet'])
        mock_mail.store.assert_called_once_with(b'1', '+FLAGS', '\\Seen')


class TestSMSGateway(unittest.TestCase):
    """Tests for SMSGateway class."""

    def setUp(self):
        self.mock_sender = MagicMock(spec=EmailSender)
        self.gateway = SMSGateway(self.mock_sender)

    def test_initialization_type_check(self):
        with self.assertRaises(TypeError):
            SMSGateway("invalid_sender_object")

    def test_send_sms_with_carrier(self):
        self.mock_sender.send_email.return_value = True

        result = self.gateway.send_sms(
            phone_number="1234567890",
            message="Test SMS",
            carrier_name="att"
        )

        self.assertTrue(result)
        self.mock_sender.send_email.assert_called_once_with(
            recipient_email="1234567890@txt.att.net",
            subject="",
            body="Test SMS"
        )

    def test_send_sms_with_direct_email_address(self):
        self.mock_sender.send_email.return_value = True

        result = self.gateway.send_sms(
            phone_number="0987654321@vtext.com",
            message="Direct Gateway Message"
        )

        self.assertTrue(result)
        self.mock_sender.send_email.assert_called_once_with(
            recipient_email="0987654321@vtext.com",
            subject="",
            body="Direct Gateway Message"
        )

    def test_send_sms_invalid_carrier_and_phone(self):
        result = self.gateway.send_sms(
            phone_number="1234567890",
            message="No carrier provided"
        )
        self.assertFalse(result)
        self.mock_sender.send_email.assert_not_called()


if __name__ == "__main__":
    unittest.main()
