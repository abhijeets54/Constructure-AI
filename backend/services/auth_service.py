"""Authentication service for Google OAuth2 and JWT token management."""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """Handles Google OAuth2 authentication and session management."""

    def __init__(self):
        """Initialize the authentication service."""
        self.client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
            }
        }
        logger.info("AuthService initialized")

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Generate Google OAuth2 authorization URL.

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL string
        """
        try:
            flow = Flow.from_client_config(
                self.client_config,
                scopes=settings.GMAIL_SCOPES,
                redirect_uri=settings.GOOGLE_REDIRECT_URI
            )

            authorization_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent',
                state=state
            )

            logger.info("Generated authorization URL")
            return authorization_url

        except Exception as e:
            logger.error(f"Error generating authorization URL: {str(e)}")
            raise

    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access tokens.

        Args:
            code: Authorization code from Google

        Returns:
            Dictionary containing tokens and user info
        """
        try:
            flow = Flow.from_client_config(
                self.client_config,
                scopes=settings.GMAIL_SCOPES,
                redirect_uri=settings.GOOGLE_REDIRECT_URI
            )

            # Exchange code for tokens
            flow.fetch_token(code=code)
            credentials = flow.credentials

            # Get user info
            user_info_service = build('oauth2', 'v2', credentials=credentials)
            user_info = user_info_service.userinfo().get().execute()

            token_data = {
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "scopes": credentials.scopes,
                "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
                "user_info": {
                    "email": user_info.get("email"),
                    "name": user_info.get("name"),
                    "picture": user_info.get("picture"),
                    "id": user_info.get("id")
                }
            }

            logger.info(f"Successfully authenticated user: {user_info.get('email')}")
            return token_data

        except Exception as e:
            logger.error(f"Error exchanging code for tokens: {str(e)}")
            raise

    def create_jwt_token(self, user_data: Dict[str, Any]) -> str:
        """
        Create a JWT token for session management.

        Args:
            user_data: User information and credentials

        Returns:
            JWT token string
        """
        try:
            payload = {
                "user_info": user_data.get("user_info"),
                "credentials": {
                    "access_token": user_data.get("access_token"),
                    "refresh_token": user_data.get("refresh_token"),
                    "token_uri": user_data.get("token_uri"),
                    "client_id": user_data.get("client_id"),
                    "client_secret": user_data.get("client_secret"),
                    "scopes": user_data.get("scopes"),
                    "expiry": user_data.get("expiry")
                },
                "exp": datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS),
                "iat": datetime.utcnow()
            }

            token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
            logger.info("JWT token created successfully")
            return token

        except Exception as e:
            logger.error(f"Error creating JWT token: {str(e)}")
            raise

    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            logger.debug("JWT token verified successfully")
            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {str(e)}")
            return None

    def get_credentials_from_token_data(self, credentials_data: Dict[str, Any]) -> Credentials:
        """
        Reconstruct Google credentials from token data.

        Args:
            credentials_data: Credentials dictionary from JWT

        Returns:
            Google Credentials object
        """
        try:
            expiry = None
            if credentials_data.get("expiry"):
                expiry = datetime.fromisoformat(credentials_data["expiry"])

            credentials = Credentials(
                token=credentials_data.get("access_token"),
                refresh_token=credentials_data.get("refresh_token"),
                token_uri=credentials_data.get("token_uri"),
                client_id=credentials_data.get("client_id"),
                client_secret=credentials_data.get("client_secret"),
                scopes=credentials_data.get("scopes"),
                expiry=expiry
            )

            return credentials

        except Exception as e:
            logger.error(f"Error reconstructing credentials: {str(e)}")
            raise


# Global auth service instance
auth_service = AuthService()
