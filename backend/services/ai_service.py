"""AI service for email summarization, reply generation, and NLP processing.

Supports multiple AI providers:
- OpenAI (GPT-4o-mini) - Requires paid API key
- Google Gemini (gemini-pro) - FREE with API key from Google AI Studio
"""
import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import json

from config import settings

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    async def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.5, max_tokens: int = 500) -> str:
        """Generate text using the AI provider."""
        pass


class OpenAIProvider(AIProvider):
    """OpenAI GPT provider."""

    def __init__(self, api_key: str, model: str):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        logger.info(f"OpenAI provider initialized with model: {model}")

    async def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.5, max_tokens: int = 500) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise


import asyncio
import random

class GeminiProvider(AIProvider):
    """Google Gemini provider (FREE!)."""
    
    # Retry configuration
    MAX_RETRIES = 3
    BASE_DELAY = 2  # seconds

    def __init__(self, api_key: str, model: str):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        logger.info(f"Gemini provider initialized with model: {model}")

    async def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.5, max_tokens: int = 500) -> str:
        """
        Generate text using the Gemini API with robust retry logic for rate limits.
        """
        # Gemini doesn't have separate system/user prompts, combine them
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        # Configure generation
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        retries = 0
        last_error = None

        while retries <= self.MAX_RETRIES:
            try:
                response = await self.model.generate_content_async(
                    full_prompt,
                    generation_config=generation_config
                )
                return response.text.strip()
            
            except Exception as e:
                error_str = str(e)
                last_error = e
                
                # Check for rate limit errors (429 or Resource Exhausted)
                if "429" in error_str or "quota" in error_str.lower() or "resource" in error_str.lower():
                    retries += 1
                    if retries > self.MAX_RETRIES:
                        logger.error(f"Gemini API rate limit exceeded after {self.MAX_RETRIES} retries. Giving up.")
                        break
                    
                    # Exponential backoff with jitter
                    # delay = base * (2 ^ retries) + random_jitter
                    delay = (self.BASE_DELAY * (2 ** (retries - 1))) + (random.random() * 0.5)
                    logger.warning(f"Gemini API rate limit hit. Retrying in {delay:.2f}s (Attempt {retries}/{self.MAX_RETRIES})")
                    await asyncio.sleep(delay)
                else:
                    # Non-retryable error
                    logger.error(f"Gemini API error (non-retryable): {error_str}")
                    break
        
        # If we get here, all retries failed
        if last_error:
            raise last_error
        raise Exception("Unknown error in Gemini provider")


class GroqProvider(AIProvider):
    """Groq Cloud provider (FREE, ultra-fast!)."""

    def __init__(self, api_key: str, model: str):
        from groq import AsyncGroq
        self.client = AsyncGroq(api_key=api_key)
        self.model = model
        logger.info(f"Groq provider initialized with model: {model}")

    async def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.5, max_tokens: int = 500) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            raise


class AIService:
    """Handles AI operations using configured provider."""

    def __init__(self):
        """Initialize the AI service with the configured provider."""
        provider_name = settings.AI_PROVIDER.lower()

        if provider_name == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is required when AI_PROVIDER=openai")
            self.provider = OpenAIProvider(settings.OPENAI_API_KEY, settings.OPENAI_MODEL)
            logger.info("AIService initialized with OpenAI provider")

        elif provider_name == "gemini":
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is required when AI_PROVIDER=gemini. Get free key at: https://makersuite.google.com/app/apikey")
            self.provider = GeminiProvider(settings.GEMINI_API_KEY, settings.GEMINI_MODEL)
            logger.info("AIService initialized with Gemini provider (FREE)")

        elif provider_name == "groq":
            if not settings.GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY is required when AI_PROVIDER=groq. Get free key at: https://console.groq.com")
            self.provider = GroqProvider(settings.GROQ_API_KEY, settings.GROQ_MODEL)
            logger.info("AIService initialized with Groq provider (FREE, ultra-fast!)")

        else:
            raise ValueError(f"Unknown AI_PROVIDER: {provider_name}. Use 'openai', 'gemini', or 'groq'")

    async def summarize_email(self, email_content: str, subject: str) -> str:
        """
        Generate a concise summary of an email.

        Args:
            email_content: Full email body text
            subject: Email subject line

        Returns:
            AI-generated summary string
        """
        try:
            # logger.info("Generating email summary") # Reduce log noise

            system_prompt = "You are a helpful email assistant that creates concise, accurate summaries."

            user_prompt = f"""Summarize the following email in 1-2 concise sentences. Focus on the main point and any action items.

Subject: {subject}

Email Content:
{email_content[:2000]}

Provide only the summary, no additional commentary."""

            summary = await self.provider.generate_text(system_prompt, user_prompt, temperature=0.3, max_tokens=150)
            return summary

        except Exception as e:
            logger.error(f"Error generating email summary: {str(e)}")
            return "Summary unavailable (AI service busy)"

    async def generate_reply(self, email_content: str, subject: str, sender: str, context: Optional[str] = None) -> str:
        """
        Generate a professional reply to an email.

        Args:
            email_content: Original email body
            subject: Original email subject
            sender: Sender's name or email
            context: Optional additional context for the reply

        Returns:
            AI-generated reply text
        """
        try:
            logger.info(f"Generating reply for email from: {sender}")

            context_section = f"\n\nAdditional Context: {context}" if context else ""

            system_prompt = "You are a professional email assistant that writes clear, appropriate responses."

            user_prompt = f"""Generate a professional, context-aware reply to the following email. The reply should be:
- Polite and professional
- Addressing the main points raised
- Concise but complete
- Ready to send without modification

Original Email:
From: {sender}
Subject: {subject}

{email_content[:1500]}
{context_section}

Generate only the email body (no subject line, no "Dear X" unless natural, just the message content)."""

            reply = await self.provider.generate_text(system_prompt, user_prompt, temperature=0.7, max_tokens=400)
            logger.info("Email reply generated successfully")
            return reply

        except Exception as e:
            logger.error(f"Error generating email reply: {str(e)}")
            return "I apologize, but I'm currently unable to generate a reply due to high demand. Please try again in a moment."

    async def classify_intent(self, user_message: str) -> Dict[str, Any]:
        """
        Classify user's intent and extract parameters using NLP.

        Args:
            user_message: User's natural language command

        Returns:
            Dictionary with intent and extracted parameters
        """
        try:
            logger.info(f"Classifying intent for message: {user_message[:50]}...")

            system_prompt = "You are an intent classification system. Always respond with valid JSON only."

            user_prompt = f"""Analyze the following user message and determine the intent and extract relevant parameters.

User Message: "{user_message}"

Classify the intent as one of:
- READ_EMAILS: User wants to see/read emails
- GENERATE_REPLY: User wants to reply to an email
- SEND_EMAIL: User wants to send a new email or confirm sending a reply
- DELETE_EMAIL: User wants to delete an email
- CATEGORIZE: User wants emails categorized or a daily digest
- GENERAL_CHAT: General conversation or unclear intent

Also extract these parameters if present:
- limit: Number of emails (integer)
- sender: Specific sender name or email
- subject_keyword: Subject line keyword
- email_index: Reference to a previously shown email (e.g., "email 2", "the first one")
- category: Category mentioned (work, personal, urgent, promotions)
- custom_message: Any custom message content the user wants to include

Respond ONLY with a JSON object in this exact format:
{{
  "intent": "INTENT_NAME",
  "parameters": {{
    "limit": number or null,
    "sender": "string or null",
    "subject_keyword": "string or null",
    "email_index": number or null,
    "category": "string or null",
    "custom_message": "string or null"
  }},
  "confidence": 0.0 to 1.0
}}"""

            result_text = await self.provider.generate_text(system_prompt, user_prompt, temperature=0.2, max_tokens=300)

            # Remove markdown code blocks if present
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()

            result = json.loads(result_text)
            logger.info(f"Intent classified: {result.get('intent')} (confidence: {result.get('confidence')})")
            return result

        except Exception as e:
            logger.error(f"Error classifying intent: {str(e)}")
            # Return graceful fallback based on keywords if AI fails
            lower_msg = user_message.lower()
            if "mail" in lower_msg or "inbox" in lower_msg or "show" in lower_msg:
                 return {"intent": "READ_EMAILS", "parameters": {"limit": 5}, "confidence": 0.5}
            elif "digest" in lower_msg or "summar" in lower_msg or "categor" in lower_msg:
                 return {"intent": "CATEGORIZE", "parameters": {"limit": 20}, "confidence": 0.5}
            
            return {
                "intent": "GENERAL_CHAT",
                "parameters": {},
                "confidence": 0.0,
                "message": "I'm having trouble connecting to my AI brain right now. You can try asking me to 'read emails' directly."
            }

    async def categorize_emails(self, emails: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize emails into groups (Work, Personal, Promotions, Urgent).

        Args:
            emails: List of email dictionaries

        Returns:
            Dictionary with categories as keys and email lists as values
        """
        try:
            logger.info(f"Categorizing {len(emails)} emails")

            if not emails:
                return {"Work": [], "Personal": [], "Promotions": [], "Urgent": []}

            # Create a summary of emails for categorization
            email_summaries = []
            for idx, email in enumerate(emails):
                email_summaries.append(f"{idx}: From: {email.get('sender_name', 'Unknown')}, Subject: {email.get('subject', 'No subject')}, Snippet: {email.get('snippet', '')[:100]}")

            emails_text = "\n".join(email_summaries)

            system_prompt = "You are an email categorization system. Always respond with valid JSON only."

            user_prompt = f"""Categorize these emails into the following categories: Work, Personal, Promotions, Urgent.
An email can belong to multiple categories if appropriate.

Emails:
{emails_text}

Respond with a JSON object where keys are email indices (0, 1, 2...) and values are arrays of categories.
Example: {{"0": ["Work", "Urgent"], "1": ["Personal"], "2": ["Promotions"]}}

Respond ONLY with the JSON object, no other text."""

            result_text = await self.provider.generate_text(system_prompt, user_prompt, temperature=0.3, max_tokens=500)

            # Remove markdown code blocks if present
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()

            categorization = json.loads(result_text)

            # Organize emails by category
            categories = {
                "Work": [],
                "Personal": [],
                "Promotions": [],
                "Urgent": []
            }

            for idx, email in enumerate(emails):
                email_categories = categorization.get(str(idx), ["Personal"])
                for category in email_categories:
                    if category in categories:
                        categories[category].append(email)

            logger.info(f"Emails categorized successfully")
            return categories

        except Exception as e:
            logger.error(f"Error categorizing emails: {str(e)}")
            # Fallback: put all in Personal
            return {
                "Work": [],
                "Personal": emails,
                "Promotions": [],
                "Urgent": []
            }

    async def generate_daily_digest(self, emails: List[Dict[str, Any]]) -> str:
        """
        Generate a daily digest summary of emails.

        Args:
            emails: List of email dictionaries

        Returns:
            AI-generated digest text
        """
        try:
            logger.info(f"Generating daily digest for {len(emails)} emails")

            if not emails:
                return "No emails to summarize for today."

            # Prepare email data
            email_data = []
            for email in emails[:20]:  # Limit to 20 most recent
                email_data.append(f"From: {email.get('sender_name', 'Unknown')}\nSubject: {email.get('subject', 'No subject')}\nSnippet: {email.get('snippet', '')[:150]}\n")

            emails_text = "\n---\n".join(email_data)

            system_prompt = "You are a helpful email assistant creating daily digests."

            user_prompt = f"""Create a daily email digest summary. Include:

1. A brief overview of the day's emails
2. Key emails that require attention
3. Suggested actions or follow-ups
4. Any urgent or time-sensitive items

Emails:
{emails_text}

Format the digest in a clear, organized manner with bullet points and sections."""

            digest = await self.provider.generate_text(system_prompt, user_prompt, temperature=0.5, max_tokens=800)
            logger.info("Daily digest generated successfully")
            return digest

        except Exception as e:
            logger.error(f"Error generating daily digest: {str(e)}")
            return "Unable to generate daily digest at this time."


# Global AI service instance
ai_service = AIService()
