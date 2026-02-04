"""Tests for Gmail service."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from google.oauth2.credentials import Credentials

from backend.services.gmail_service import GmailService


@pytest.fixture
def mock_credentials():
    """Create mock Google credentials."""
    return Credentials(
        token="mock_token",
        refresh_token="mock_refresh",
        token_uri="https://oauth2.googleapis.com/token",
        client_id="mock_id",
        client_secret="mock_secret"
    )


@pytest.fixture
def mock_gmail_message():
    """Create mock Gmail message."""
    return {
        'id': 'msg123',
        'threadId': 'thread123',
        'snippet': 'This is a test email snippet',
        'payload': {
            'headers': [
                {'name': 'Subject', 'value': 'Test Subject'},
                {'name': 'From', 'value': 'John Doe <john@example.com>'},
                {'name': 'To', 'value': 'test@example.com'},
                {'name': 'Date', 'value': 'Mon, 1 Jan 2024 12:00:00 +0000'},
                {'name': 'Message-ID', 'value': '<msg123@example.com>'}
            ],
            'body': {
                'data': 'VGhpcyBpcyB0ZXN0IGVtYWlsIGJvZHk='  # Base64 encoded "This is test email body"
            }
        },
        'labelIds': ['INBOX', 'UNREAD']
    }


class TestGmailService:
    """Test cases for GmailService."""

    @patch('backend.services.gmail_service.build')
    def test_initialization(self, mock_build, mock_credentials):
        """Test GmailService initialization."""
        gmail_service = GmailService(mock_credentials)

        assert gmail_service is not None
        assert gmail_service.credentials == mock_credentials
        mock_build.assert_called_once_with('gmail', 'v1', credentials=mock_credentials)

    @patch('backend.services.gmail_service.build')
    @pytest.mark.asyncio
    async def test_fetch_emails(self, mock_build, mock_credentials, mock_gmail_message):
        """Test fetching emails."""
        # Setup mocks
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': 'msg123'}]
        }
        mock_service.users().messages().get().execute.return_value = mock_gmail_message

        gmail_service = GmailService(mock_credentials)
        emails = await gmail_service.fetch_emails(max_results=5)

        assert len(emails) == 1
        assert emails[0]['id'] == 'msg123'
        assert emails[0]['subject'] == 'Test Subject'
        assert emails[0]['sender_email'] == 'john@example.com'
        assert emails[0]['sender_name'] == 'John Doe'

    @patch('backend.services.gmail_service.build')
    def test_parse_email_address(self, mock_build, mock_credentials):
        """Test email address parsing."""
        gmail_service = GmailService(mock_credentials)

        # Test with name and email
        name, email = gmail_service._parse_email_address('John Doe <john@example.com>')
        assert name == 'John Doe'
        assert email == 'john@example.com'

        # Test with email only
        name, email = gmail_service._parse_email_address('john@example.com')
        assert name == 'john@example.com'
        assert email == 'john@example.com'

    @patch('backend.services.gmail_service.build')
    @pytest.mark.asyncio
    async def test_send_email(self, mock_build, mock_credentials):
        """Test sending email."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_service.users().messages().send().execute.return_value = {
            'id': 'sent123',
            'threadId': 'thread123',
            'labelIds': ['SENT']
        }

        gmail_service = GmailService(mock_credentials)
        result = await gmail_service.send_email(
            to='recipient@example.com',
            subject='Test Subject',
            body='Test body'
        )

        assert result['id'] == 'sent123'
        assert result['thread_id'] == 'thread123'

    @patch('backend.services.gmail_service.build')
    @pytest.mark.asyncio
    async def test_delete_email(self, mock_build, mock_credentials):
        """Test deleting email."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_service.users().messages().trash().execute.return_value = {}

        gmail_service = GmailService(mock_credentials)
        result = await gmail_service.delete_email('msg123')

        assert result is True
        mock_service.users().messages().trash.assert_called_once()
