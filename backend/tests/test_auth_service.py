"""Tests for authentication service."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import jwt

from backend.services.auth_service import AuthService
from backend.config import settings


@pytest.fixture
def auth_service():
    """Create AuthService instance for testing."""
    return AuthService()


@pytest.fixture
def mock_user_data():
    """Mock user data for testing."""
    return {
        "access_token": "mock_access_token",
        "refresh_token": "mock_refresh_token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "mock_client_id",
        "client_secret": "mock_client_secret",
        "scopes": ["https://mail.google.com/"],
        "expiry": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        "user_info": {
            "email": "test@example.com",
            "name": "Test User",
            "picture": "https://example.com/pic.jpg",
            "id": "12345"
        }
    }


class TestAuthService:
    """Test cases for AuthService."""

    def test_initialization(self, auth_service):
        """Test AuthService initialization."""
        assert auth_service is not None
        assert auth_service.client_config is not None
        assert "web" in auth_service.client_config

    def test_get_authorization_url(self, auth_service):
        """Test generation of authorization URL."""
        with patch('backend.services.auth_service.Flow') as mock_flow:
            mock_flow_instance = MagicMock()
            mock_flow.from_client_config.return_value = mock_flow_instance
            mock_flow_instance.authorization_url.return_value = (
                "https://accounts.google.com/o/oauth2/auth?...",
                "state"
            )

            url = auth_service.get_authorization_url()

            assert url.startswith("https://accounts.google.com")
            mock_flow.from_client_config.assert_called_once()

    def test_create_jwt_token(self, auth_service, mock_user_data):
        """Test JWT token creation."""
        token = auth_service.create_jwt_token(mock_user_data)

        assert token is not None
        assert isinstance(token, str)

        # Verify token can be decoded
        decoded = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        assert decoded["user_info"]["email"] == "test@example.com"
        assert "credentials" in decoded

    def test_verify_jwt_token_valid(self, auth_service, mock_user_data):
        """Test verification of valid JWT token."""
        token = auth_service.create_jwt_token(mock_user_data)
        payload = auth_service.verify_jwt_token(token)

        assert payload is not None
        assert payload["user_info"]["email"] == "test@example.com"

    def test_verify_jwt_token_invalid(self, auth_service):
        """Test verification of invalid JWT token."""
        invalid_token = "invalid.token.here"
        payload = auth_service.verify_jwt_token(invalid_token)

        assert payload is None

    def test_verify_jwt_token_expired(self, auth_service, mock_user_data):
        """Test verification of expired JWT token."""
        # Create token with immediate expiration
        payload = {
            "user_info": mock_user_data["user_info"],
            "credentials": {},
            "exp": datetime.utcnow() - timedelta(hours=1),  # Expired
            "iat": datetime.utcnow() - timedelta(hours=2)
        }

        expired_token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

        result = auth_service.verify_jwt_token(expired_token)
        assert result is None

    def test_get_credentials_from_token_data(self, auth_service, mock_user_data):
        """Test reconstruction of Google credentials."""
        credentials_data = {
            "access_token": "mock_token",
            "refresh_token": "mock_refresh",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "mock_id",
            "client_secret": "mock_secret",
            "scopes": ["https://mail.google.com/"],
            "expiry": datetime.utcnow().isoformat()
        }

        credentials = auth_service.get_credentials_from_token_data(credentials_data)

        assert credentials is not None
        assert credentials.token == "mock_token"
        assert credentials.refresh_token == "mock_refresh"
