"""
email-sms-automator/src/email_receiver.py
Handles receiving, searching, and parsing emails via IMAP protocol with SSL.
Supports decoding internationalized headers and extracting file attachments.
"""

import email
from email.header import decode_header
import imaplib
import os
from typing import Any, Dict, List, Optional
try:
    from .utils import ensure_directory_exists, setup_logging
except ImportError:
    from utils import ensure_directory_exists, setup_logging


logger = setup_logging(__name__)


class EmailReceiver:
    """
    Handles receiving and parsing emails via IMAP.
    Supports secure SSL connection, filtering, attachment extraction, and read-status tracking.
    """

    def __init__(self, imap_server: str, sender_email: str, sender_password: str):
        """
        Initializes the EmailReceiver with IMAP server credentials.

        :param imap_server: IMAP server hostname (e.g., 'imap.gmail.com').
        :param sender_email: Email address used for authentication.
        :param sender_password: App password or authentication token.
        """
        self.imap_server = imap_server
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.mail = None
        logger.info(f"EmailReceiver initialized for {sender_email} via {imap_server}.")

    def _connect(self) -> bool:
        """
        Establishes and logs into the IMAP server using SSL.

        :return: True if connection and authentication succeed, False otherwise.
        """
        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_server)
            self.mail.login(self.sender_email, self.sender_password)
            logger.info("Successfully connected and logged into IMAP server.")
            return True
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP authentication failed. Check email and app password. Error: {e}")
            self.mail = None
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during IMAP connect/login: {e}")
            self.mail = None
            return False

    def _disconnect(self) -> None:
        """
        Safely logs out and disconnects from the IMAP server.
        """
        if self.mail:
            try:
                self.mail.logout()
                logger.info("Disconnected from IMAP server.")
            except Exception as e:
                logger.warning(f"Error during IMAP disconnection: {e}")
            finally:
                self.mail = None

    def search_emails(
        self,
        mailbox: str = 'INBOX',
        criteria: str = 'UNSEEN',
        from_sender: Optional[str] = None,
        subject_contains: Optional[str] = None
    ) -> List[bytes]:
        """
        Searches for emails in the given mailbox based on criteria.

        :param mailbox: Mailbox to search (e.g., 'INBOX').
        :param criteria: IMAP search criteria (e.g., 'UNSEEN', 'ALL', 'SEEN').
        :param from_sender: Optional sender email address to filter.
        :param subject_contains: Optional substring that the subject must contain.
        :return: List of email UIDs matching criteria.
        """
        if not self._connect():
            return []

        try:
            self.mail.select(mailbox)
            search_query = [criteria]
            if from_sender:
                search_query.extend(['FROM', from_sender])
            if subject_contains:
                search_query.extend(['SUBJECT', subject_contains])

            status, email_ids = self.mail.search(None, *search_query)
            if status != 'OK':
                logger.error(f"IMAP search failed. Status: {status}")
                return []

            uids = email_ids[0].split() if email_ids and email_ids[0] else []
            logger.info(f"Found {len(uids)} emails matching criteria in '{mailbox}'.")
            return uids
        except Exception as e:
            logger.error(f"Error searching emails: {e}")
            return []
        finally:
            self._disconnect()

    def fetch_email_content(
        self,
        uid: bytes,
        mark_as_read: bool = True,
        download_attachments_dir: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fetches the content of a specific email by UID.
        Optionally marks as read and downloads attachments to disk.

        :param uid: The unique ID (UID) of the email.
        :param mark_as_read: If True, marks the email as SEEN.
        :param download_attachments_dir: Directory path to save attachments, or None to skip.
        :return: Dictionary containing email details or None if failed.
        """
        if not self._connect():
            return None

        try:
            self.mail.select('INBOX')

            # Fetch RFC822 full message content
            status, msg_data = self.mail.fetch(uid, '(RFC822)')
            if status != 'OK' or not msg_data or not msg_data[0]:
                logger.error(f"Failed to fetch email UID {uid}. Status: {status}")
                return None

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            sender = self._decode_header_part(msg.get('From'))
            subject = self._decode_header_part(msg.get('Subject'))

            email_body = ""
            attachments_downloaded = []

            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename and download_attachments_dir:
                        decoded_filename = self._decode_header_part(filename)
                        ensure_directory_exists(download_attachments_dir)
                        filepath = os.path.join(download_attachments_dir, decoded_filename)
                        try:
                            with open(filepath, "wb") as f:
                                f.write(part.get_payload(decode=True))
                            attachments_downloaded.append(filepath)
                            logger.info(f"Downloaded attachment: {filepath}")
                        except Exception as e:
                            logger.error(f"Error downloading attachment {decoded_filename}: {e}")

                elif "text/plain" in content_type and "attachment" not in content_disposition:
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        email_body += part.get_payload(decode=True).decode(charset)
                    except Exception as e:
                        logger.warning(f"Could not decode plain text part from email UID {uid}. Error: {e}")
                        email_body += "[ undecodable plain text part ]"

                elif "text/html" in content_type and "attachment" not in content_disposition:
                    # For simplicity, plain text is prioritized; HTML can be parsed if needed
                    pass

            if mark_as_read:
                self.mail.store(uid, '+FLAGS', '\\Seen')
                logger.info(f"Marked email UID {uid} as read.")

            uid_str = uid.decode('utf-8') if isinstance(uid, bytes) else str(uid)
            body_snippet = email_body[:200] + "..." if len(email_body) > 200 else email_body

            return {
                "uid": uid_str,
                "sender": sender,
                "subject": subject,
                "body_snippet": body_snippet,
                "attachments_downloaded": attachments_downloaded
            }
        except Exception as e:
            logger.error(f"Error fetching/parsing email UID {uid}: {e}")
            return None
        finally:
            self._disconnect()

    def _decode_header_part(self, header_value: Optional[str]) -> str:
        """
        Decodes MIME encoded header fields (e.g. '=?UTF-8?B?...?=').

        :param header_value: Raw header value string.
        :return: Decoded human-readable string.
        """
        if header_value is None:
            return ""

        decoded_parts = decode_header(header_value)
        decoded_string = ""
        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                try:
                    decoded_string += part.decode(charset if charset else 'utf-8')
                except Exception:
                    decoded_string += part.decode('latin-1', errors='replace')
            else:
                decoded_string += str(part)
        return decoded_string.strip()
