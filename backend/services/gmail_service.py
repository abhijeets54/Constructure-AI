"""Gmail service for email operations."""
import logging
import base64
from email.mime.text import MIMEText
from typing import List, Dict, Any, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class GmailService:
    """Handles Gmail API operations."""

    def __init__(self, credentials: Credentials):
        """
        Initialize Gmail service with user credentials.

        Args:
            credentials: Google OAuth2 credentials
        """
        self.credentials = credentials
        self.service = build('gmail', 'v1', credentials=credentials)
        logger.info("GmailService initialized")

    async def fetch_emails(self, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch the most recent emails from the user's inbox.

        Args:
            max_results: Maximum number of emails to fetch

        Returns:
            List of email dictionaries with metadata and content
        """
        try:
            logger.info(f"Fetching {max_results} emails from inbox")

            # List messages
            results = self.service.users().messages().list(
                userId='me',
                maxResults=max_results,
                labelIds=['INBOX']
            ).execute()

            messages = results.get('messages', [])

            if not messages:
                logger.info("No messages found")
                return []

            emails = []
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()

                email_data = self._parse_email(msg)
                emails.append(email_data)

            logger.info(f"Successfully fetched {len(emails)} emails")
            return emails

        except HttpError as error:
            logger.error(f"Gmail API error while fetching emails: {error}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching emails: {str(e)}")
            raise

    async def fetch_emails_with_query(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Fetch emails matching a specific query.

        Args:
            query: Gmail search query (e.g., 'from:john@example.com')
            max_results: Maximum number of emails to fetch

        Returns:
            List of email dictionaries
        """
        try:
            logger.info(f"Fetching emails with query: {query}")

            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])

            if not messages:
                logger.info(f"No messages found for query: {query}")
                return []

            emails = []
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()

                email_data = self._parse_email(msg)
                emails.append(email_data)

            logger.info(f"Found {len(emails)} emails matching query")
            return emails

        except HttpError as error:
            logger.error(f"Gmail API error with query: {error}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error with query: {str(e)}")
            raise

    def _parse_email(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a Gmail message into a structured format.

        Args:
            message: Raw Gmail message object

        Returns:
            Parsed email dictionary
        """
        headers = message.get('payload', {}).get('headers', [])

        # Extract header information
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
        from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')
        to_header = next((h['value'] for h in headers if h['name'].lower() == 'to'), '')
        date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
        message_id_header = next((h['value'] for h in headers if h['name'].lower() == 'message-id'), '')

        # Extract body
        body = self._extract_body(message.get('payload', {}))

        # Parse sender information
        sender_name, sender_email = self._parse_email_address(from_header)

        email_data = {
            'id': message['id'],
            'thread_id': message.get('threadId'),
            'subject': subject,
            'from': from_header,
            'sender_name': sender_name,
            'sender_email': sender_email,
            'to': to_header,
            'date': date,
            'snippet': message.get('snippet', ''),
            'body': body,
            'message_id': message_id_header,
            'labels': message.get('labelIds', [])
        }

        return email_data

    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """
        Extract email body from payload.

        Args:
            payload: Email payload object

        Returns:
            Decoded email body text
        """
        body = ""

        if 'body' in payload and payload['body'].get('data'):
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
        elif 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    if 'data' in part.get('body', {}):
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                        break
                elif part.get('mimeType') == 'text/html' and not body:
                    if 'data' in part.get('body', {}):
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                elif 'parts' in part:
                    # Recursive for nested parts
                    body = self._extract_body(part)
                    if body:
                        break

        return body

    def _parse_email_address(self, email_str: str) -> tuple[str, str]:
        """
        Parse email address string into name and email.

        Args:
            email_str: Email string (e.g., "John Doe <john@example.com>")

        Returns:
            Tuple of (name, email)
        """
        if '<' in email_str and '>' in email_str:
            name = email_str.split('<')[0].strip().strip('"')
            email = email_str.split('<')[1].split('>')[0].strip()
            return name, email
        else:
            return email_str, email_str

    async def send_email(self, to: str, subject: str, body: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send an email via Gmail.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            thread_id: Optional thread ID to reply to an existing thread

        Returns:
            Sent message details
        """
        try:
            logger.info(f"Sending email to: {to}")

            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            send_body = {'raw': raw_message}
            if thread_id:
                send_body['threadId'] = thread_id

            sent_message = self.service.users().messages().send(
                userId='me',
                body=send_body
            ).execute()

            logger.info(f"Email sent successfully. Message ID: {sent_message['id']}")
            return {
                'id': sent_message['id'],
                'thread_id': sent_message.get('threadId'),
                'label_ids': sent_message.get('labelIds', [])
            }

        except HttpError as error:
            logger.error(f"Gmail API error while sending email: {error}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending email: {str(e)}")
            raise

    async def delete_email(self, message_id: str) -> bool:
        """
        Delete (trash) an email by message ID.

        Args:
            message_id: Gmail message ID

        Returns:
            True if successful
        """
        try:
            logger.info(f"Deleting email with ID: {message_id}")

            self.service.users().messages().trash(
                userId='me',
                id=message_id
            ).execute()

            logger.info(f"Email {message_id} moved to trash successfully")
            return True

        except HttpError as error:
            logger.error(f"Gmail API error while deleting email: {error}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting email: {str(e)}")
            raise

    async def get_user_profile(self) -> Dict[str, Any]:
        """
        Get the user's Gmail profile information.

        Returns:
            User profile dictionary
        """
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            logger.info(f"Retrieved profile for: {profile.get('emailAddress')}")
            return profile

        except HttpError as error:
            logger.error(f"Gmail API error fetching profile: {error}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching profile: {str(e)}")
            raise
