"""Main FastAPI application for AI Email Assistant."""
import logging
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Request, Response, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

from config import settings
from services.auth_service import auth_service
from services.gmail_service import GmailService
from services.ai_service import ai_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Pydantic models for request/response
class ChatMessage(BaseModel):
    """Chat message model."""
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = []


class EmailReplyRequest(BaseModel):
    """Request model for generating email reply."""
    email_id: str
    custom_context: Optional[str] = None


class SendEmailRequest(BaseModel):
    """Request model for sending email."""
    to: str
    subject: str
    body: str
    thread_id: Optional[str] = None


class DeleteEmailRequest(BaseModel):
    """Request model for deleting email."""
    email_id: str


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting AI Email Assistant API")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Frontend URL: {settings.FRONTEND_URL}")
    yield
    logger.info("Shutting down AI Email Assistant API")


# Initialize FastAPI app
app = FastAPI(
    title="AI Email Assistant API",
    description="Backend API for AI-powered Gmail assistant",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency to get current user from JWT token
async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Extract and verify JWT token from cookies or Authorization header.

    Args:
        request: FastAPI request object

    Returns:
        Decoded user data from JWT

    Raises:
        HTTPException: If token is missing or invalid
    """
    # Try to get token from cookie
    token = request.cookies.get("auth_token")

    # If not in cookie, try Authorization header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        logger.warning("No authentication token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please log in."
        )

    # Verify token
    payload = auth_service.verify_jwt_token(token)
    if not payload:
        logger.warning("Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please log in again."
        )

    return payload


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Email Assistant API",
        "version": "1.0.0",
        "status": "running"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.get("/auth/login")
async def login():
    """
    Initiate Google OAuth2 login flow.

    Returns:
        Redirect to Google authorization URL
    """
    try:
        logger.info("Login request received")
        authorization_url = auth_service.get_authorization_url()
        return {"authorization_url": authorization_url}

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initiate login")


@app.get("/auth/callback")
async def auth_callback(code: Optional[str] = None, error: Optional[str] = None, response: Response = None):
    """
    Handle Google OAuth2 callback.

    Args:
        code: Authorization code from Google
        error: Error message if authorization failed
        response: FastAPI response object

    Returns:
        Redirect to frontend with token
    """
    try:
        if error:
            logger.error(f"OAuth error: {error}")
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/?error=access_denied"
            )

        if not code:
            logger.error("No authorization code provided")
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/?error=no_code"
            )

        logger.info("Processing OAuth callback")

        # Exchange code for tokens
        token_data = await auth_service.exchange_code_for_tokens(code)

        # Create JWT token
        jwt_token = auth_service.create_jwt_token(token_data)

        # Redirect to frontend with token
        redirect_url = f"{settings.FRONTEND_URL}/dashboard?token={jwt_token}"
        response = RedirectResponse(url=redirect_url)

        # Set secure HttpOnly cookie
        response.set_cookie(
            key="auth_token",
            value=jwt_token,
            httponly=True,
            secure=settings.ENVIRONMENT == "production",
            samesite="lax",
            max_age=settings.JWT_EXPIRATION_HOURS * 3600
        )

        logger.info("OAuth callback processed successfully")
        return response

    except Exception as e:
        logger.error(f"Callback error: {str(e)}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/?error=auth_failed"
        )


@app.post("/auth/logout")
async def logout(response: Response):
    """
    Logout the current user.

    Args:
        response: FastAPI response object

    Returns:
        Success message
    """
    logger.info("Logout request received")
    response.delete_cookie("auth_token")
    return {"message": "Logged out successfully"}


@app.get("/auth/me")
async def get_current_user_info(user_data: Dict[str, Any] = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Args:
        user_data: User data from JWT token

    Returns:
        User information
    """
    return {
        "user": user_data.get("user_info"),
        "authenticated": True
    }


# ============================================================================
# EMAIL ENDPOINTS
# ============================================================================

@app.get("/emails")
async def get_emails(
    limit: int = 5,
    user_data: Dict[str, Any] = Depends(get_current_user)
):
    """
    Fetch recent emails from user's inbox.

    Args:
        limit: Number of emails to fetch
        user_data: User data from JWT token

    Returns:
        List of emails with AI summaries
    """
    try:
        logger.info(f"Fetching {limit} emails")

        # Get credentials and create Gmail service
        credentials = auth_service.get_credentials_from_token_data(
            user_data.get("credentials")
        )
        gmail_service = GmailService(credentials)

        # Fetch emails
        emails = await gmail_service.fetch_emails(max_results=limit)

        # Generate AI summaries for each email
        for email in emails:
            summary = await ai_service.summarize_email(
                email.get('body', ''),
                email.get('subject', '')
            )
            email['ai_summary'] = summary

        logger.info(f"Successfully fetched and summarized {len(emails)} emails")
        return {"emails": emails}

    except Exception as e:
        logger.error(f"Error fetching emails: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails: {str(e)}")


@app.post("/emails/reply/generate")
async def generate_email_reply(
    request: EmailReplyRequest,
    user_data: Dict[str, Any] = Depends(get_current_user)
):
    """
    Generate AI reply for a specific email.

    Args:
        request: Email reply request with email ID
        user_data: User data from JWT token

    Returns:
        Generated reply text
    """
    try:
        logger.info(f"Generating reply for email: {request.email_id}")

        # Get credentials and create Gmail service
        credentials = auth_service.get_credentials_from_token_data(
            user_data.get("credentials")
        )
        gmail_service = GmailService(credentials)

        # Fetch the specific email
        emails = await gmail_service.fetch_emails(max_results=20)
        email = next((e for e in emails if e['id'] == request.email_id), None)

        if not email:
            raise HTTPException(status_code=404, detail="Email not found")

        # Generate reply
        reply = await ai_service.generate_reply(
            email.get('body', ''),
            email.get('subject', ''),
            email.get('sender_name', ''),
            request.custom_context
        )

        logger.info("Reply generated successfully")
        return {
            "reply": reply,
            "original_email": email
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating reply: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate reply: {str(e)}")


@app.post("/emails/send")
async def send_email(
    request: SendEmailRequest,
    user_data: Dict[str, Any] = Depends(get_current_user)
):
    """
    Send an email via Gmail.

    Args:
        request: Send email request
        user_data: User data from JWT token

    Returns:
        Sent email details
    """
    try:
        logger.info(f"Sending email to: {request.to}")

        # Get credentials and create Gmail service
        credentials = auth_service.get_credentials_from_token_data(
            user_data.get("credentials")
        )
        gmail_service = GmailService(credentials)

        # Send email
        result = await gmail_service.send_email(
            to=request.to,
            subject=request.subject,
            body=request.body,
            thread_id=request.thread_id
        )

        logger.info(f"Email sent successfully: {result['id']}")
        return {
            "message": "Email sent successfully",
            "email_id": result['id'],
            "thread_id": result.get('thread_id')
        }

    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


@app.post("/emails/delete")
async def delete_email(
    request: DeleteEmailRequest,
    user_data: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete (trash) an email.

    Args:
        request: Delete email request
        user_data: User data from JWT token

    Returns:
        Success message
    """
    try:
        logger.info(f"Deleting email: {request.email_id}")

        # Get credentials and create Gmail service
        credentials = auth_service.get_credentials_from_token_data(
            user_data.get("credentials")
        )
        gmail_service = GmailService(credentials)

        # Delete email
        await gmail_service.delete_email(request.email_id)

        logger.info(f"Email deleted successfully: {request.email_id}")
        return {"message": "Email deleted successfully"}

    except Exception as e:
        logger.error(f"Error deleting email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete email: {str(e)}")


# ============================================================================
# CHAT / AI ENDPOINTS
# ============================================================================

@app.post("/chat")
async def chat(
    request: ChatMessage,
    user_data: Dict[str, Any] = Depends(get_current_user)
):
    """
    Process natural language chat message and perform appropriate action.

    Args:
        request: Chat message request
        user_data: User data from JWT token

    Returns:
        Chat response with action results
    """
    try:
        logger.info(f"Processing chat message: {request.message[:50]}...")

        # Classify intent
        intent_result = await ai_service.classify_intent(request.message)
        intent = intent_result.get("intent")
        params = intent_result.get("parameters", {})

        logger.info(f"Detected intent: {intent}")

        # Get credentials
        credentials = auth_service.get_credentials_from_token_data(
            user_data.get("credentials")
        )
        gmail_service = GmailService(credentials)

        response_data = {
            "intent": intent,
            "confidence": intent_result.get("confidence"),
            "message": ""
        }

        # Handle different intents
        if intent == "READ_EMAILS":
            limit = params.get("limit") or 5
            emails = await gmail_service.fetch_emails(max_results=limit)

            # Generate summaries
            for email in emails:
                summary = await ai_service.summarize_email(
                    email.get('body', ''),
                    email.get('subject', '')
                )
                email['ai_summary'] = summary

            response_data["emails"] = emails
            response_data["message"] = f"Here are your last {len(emails)} emails:"

        elif intent == "CATEGORIZE":
            limit = params.get("limit") or 20
            emails = await gmail_service.fetch_emails(max_results=limit)

            # Categorize emails
            categories = await ai_service.categorize_emails(emails)

            # Generate summaries for categorized emails
            for category_emails in categories.values():
                for email in category_emails:
                    if 'ai_summary' not in email:
                        summary = await ai_service.summarize_email(
                            email.get('body', ''),
                            email.get('subject', '')
                        )
                        email['ai_summary'] = summary

            # Generate daily digest
            digest = await ai_service.generate_daily_digest(emails)

            response_data["categories"] = categories
            response_data["digest"] = digest
            response_data["message"] = "Here's your categorized email overview:"

        elif intent == "DELETE_EMAIL":
            # Handle natural language email deletion
            sender = params.get("sender")
            subject_keyword = params.get("subject_keyword")
            email_index = params.get("email_index")
            
            logger.info(f"DELETE_EMAIL params: sender={sender}, subject={subject_keyword}, index={email_index}")
            
            email_to_delete = None
            
            # Option 1: Delete by email index (e.g., "delete email 2")
            if email_index is not None:
                try:
                    index = int(email_index) - 1  # Convert to 0-based index
                    if index >= 0:
                        # Fetch the last emails shown to user
                        emails = await gmail_service.fetch_emails(max_results=10)
                        if 0 <= index < len(emails):
                            email_to_delete = emails[index]
                except (ValueError, TypeError):
                    pass
            
            # Option 2: Delete by sender (e.g., "delete email from John")
            if not email_to_delete and sender:
                query = f"from:{sender}"
                logger.info(f"Searching for emails with query: {query}")
                found_emails = await gmail_service.fetch_emails_with_query(query, max_results=1)
                if found_emails:
                    email_to_delete = found_emails[0]
            
            # Option 3: Delete by subject keyword (e.g., "delete email about meeting")
            if not email_to_delete and subject_keyword:
                query = f"subject:{subject_keyword}"
                logger.info(f"Searching for emails with query: {query}")
                found_emails = await gmail_service.fetch_emails_with_query(query, max_results=1)
                if found_emails:
                    email_to_delete = found_emails[0]
            
            # Execute deletion if email was found
            if email_to_delete:
                email_id = email_to_delete.get("id")
                email_subject = email_to_delete.get("subject", "No subject")
                email_sender = email_to_delete.get("sender_name") or email_to_delete.get("sender_email", "Unknown")
                
                await gmail_service.delete_email(email_id)
                logger.info(f"Successfully deleted email: {email_subject} from {email_sender}")
                
                response_data["message"] = f"✅ Successfully deleted email from **{email_sender}**: \"{email_subject}\""
                response_data["deleted_email"] = {
                    "id": email_id,
                    "subject": email_subject,
                    "sender": email_sender
                }
            else:
                # No email found - ask for clarification
                response_data["message"] = """I couldn't find an email matching that description. Please try:

• **By sender**: "Delete the email from John" or "Delete email from support@company.com"
• **By subject**: "Delete the email about meeting" or "Delete email with subject invoice"
• **By number**: "Delete email 2" (refers to the emails I just showed you)
• **Using UI**: Click the Delete button on any email card above"""
                response_data["requires_clarification"] = True

        elif intent == "GENERAL_CHAT":
            # Provide helpful information about capabilities
            user_name = user_data.get("user_info", {}).get("name", "there")
            response_data["message"] = f"""Hello {user_name}! I'm your AI email assistant. Here's what I can help you with:

• **Read Emails**: Say "Show me my latest emails" or "What are my recent messages?"
• **Categorize**: Ask for "daily digest" or "categorize my emails"
• **Reply**: Click the Reply button on any email to generate a smart response
• **Delete**: Click the Delete button on any email to remove it

Just ask me naturally, and I'll help you manage your inbox!"""

        else:
            response_data["message"] = "I'm not sure what you'd like me to do. Try asking me to show your emails, create a digest, or reply to a message."

        return response_data

    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")


@app.post("/chat/categorize")
async def categorize_emails(
    limit: int = 20,
    user_data: Dict[str, Any] = Depends(get_current_user)
):
    """
    Categorize emails and generate daily digest.

    Args:
        limit: Number of emails to categorize
        user_data: User data from JWT token

    Returns:
        Categorized emails and digest
    """
    try:
        logger.info(f"Categorizing {limit} emails")

        # Get credentials and create Gmail service
        credentials = auth_service.get_credentials_from_token_data(
            user_data.get("credentials")
        )
        gmail_service = GmailService(credentials)

        # Fetch emails
        emails = await gmail_service.fetch_emails(max_results=limit)

        # Categorize
        categories = await ai_service.categorize_emails(emails)

        # Generate summaries
        for category_emails in categories.values():
            for email in category_emails:
                summary = await ai_service.summarize_email(
                    email.get('body', ''),
                    email.get('subject', '')
                )
                email['ai_summary'] = summary

        # Generate digest
        digest = await ai_service.generate_daily_digest(emails)

        return {
            "categories": categories,
            "digest": digest
        }

    except Exception as e:
        logger.error(f"Error categorizing emails: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to categorize emails: {str(e)}")


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    logger.error(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again."}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
