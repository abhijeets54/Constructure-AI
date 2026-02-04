"""Tests for AI service."""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import json

from backend.services.ai_service import AIService


@pytest.fixture
def ai_service():
    """Create AIService instance for testing."""
    return AIService()


@pytest.fixture
def mock_email():
    """Mock email data for testing."""
    return {
        'id': 'msg123',
        'subject': 'Project Update',
        'sender_name': 'John Doe',
        'sender_email': 'john@example.com',
        'body': 'Hi, here is the latest update on the project. We have completed phase 1 and are moving to phase 2.',
        'snippet': 'Hi, here is the latest update...'
    }


class TestAIService:
    """Test cases for AIService."""

    def test_initialization(self, ai_service):
        """Test AIService initialization."""
        assert ai_service is not None
        assert ai_service.client is not None
        assert ai_service.model == "gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_summarize_email(self, ai_service, mock_email):
        """Test email summarization."""
        with patch.object(ai_service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Project update: Phase 1 complete, moving to phase 2."
            mock_create.return_value = mock_response

            summary = await ai_service.summarize_email(
                mock_email['body'],
                mock_email['subject']
            )

            assert summary is not None
            assert len(summary) > 0
            assert "phase" in summary.lower() or "project" in summary.lower()
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_reply(self, ai_service, mock_email):
        """Test reply generation."""
        with patch.object(ai_service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Thank you for the update, John. Looking forward to phase 2."
            mock_create.return_value = mock_response

            reply = await ai_service.generate_reply(
                mock_email['body'],
                mock_email['subject'],
                mock_email['sender_name']
            )

            assert reply is not None
            assert len(reply) > 0
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_intent_read_emails(self, ai_service):
        """Test intent classification for reading emails."""
        with patch.object(ai_service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "intent": "READ_EMAILS",
                "parameters": {"limit": 5},
                "confidence": 0.9
            })
            mock_create.return_value = mock_response

            result = await ai_service.classify_intent("Show me my last 5 emails")

            assert result['intent'] == 'READ_EMAILS'
            assert result['parameters']['limit'] == 5
            assert result['confidence'] > 0.8

    @pytest.mark.asyncio
    async def test_classify_intent_categorize(self, ai_service):
        """Test intent classification for categorization."""
        with patch.object(ai_service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "intent": "CATEGORIZE",
                "parameters": {},
                "confidence": 0.85
            })
            mock_create.return_value = mock_response

            result = await ai_service.classify_intent("Give me today's email digest")

            assert result['intent'] == 'CATEGORIZE'
            assert result['confidence'] > 0.7

    @pytest.mark.asyncio
    async def test_categorize_emails(self, ai_service):
        """Test email categorization."""
        mock_emails = [
            {'sender_name': 'Boss', 'subject': 'Quarterly Review', 'snippet': 'Meeting tomorrow'},
            {'sender_name': 'Newsletter', 'subject': '50% Off Sale', 'snippet': 'Limited time offer'},
        ]

        with patch.object(ai_service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "0": ["Work", "Urgent"],
                "1": ["Promotions"]
            })
            mock_create.return_value = mock_response

            categories = await ai_service.categorize_emails(mock_emails)

            assert 'Work' in categories
            assert 'Promotions' in categories
            assert len(categories['Work']) > 0 or len(categories['Promotions']) > 0

    @pytest.mark.asyncio
    async def test_generate_daily_digest(self, ai_service):
        """Test daily digest generation."""
        mock_emails = [
            {'sender_name': 'John', 'subject': 'Meeting', 'snippet': 'Tomorrow at 2pm'},
            {'sender_name': 'Jane', 'subject': 'Report', 'snippet': 'Attached is the report'},
        ]

        with patch.object(ai_service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Daily Digest: You have a meeting tomorrow and a report to review."
            mock_create.return_value = mock_response

            digest = await ai_service.generate_daily_digest(mock_emails)

            assert digest is not None
            assert len(digest) > 0
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling(self, ai_service):
        """Test error handling in AI service."""
        with patch.object(ai_service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")

            summary = await ai_service.summarize_email("Test content", "Test subject")

            assert "Unable to generate" in summary
