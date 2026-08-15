"""
Real AI-drafted support responses via the OpenAI v1 SDK.

Mirrors content-engine/app/services/ai_writer.py's pattern: call the
real provider, report an honest, structured failure (rather than
fabricating output) when it can't run - e.g. no API key configured.
Kept as its own copy rather than a cross-repo import, since every
engine in this fleet is an independently deployable repo.

Deliberately does not fabricate confidence_score/sentiment - a real
chat completion doesn't hand those back, and the old mock's hardcoded
0.85/"frustrated" were invented, not computed. Left null rather than
guessed.
"""

from typing import Any, Dict, Optional

from loguru import logger
from openai import AsyncOpenAI

from app.config import settings


class AIResponder:
    """Drafts a customer support reply via OpenAI, or reports honestly why it couldn't."""

    def __init__(self):
        self._client: Optional[AsyncOpenAI] = (
            AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        )

    async def generate_response(self, customer_message: str, context: Optional[str] = None) -> Dict[str, Any]:
        if self._client is None:
            logger.warning("AI responder called with no OpenAI API key configured")
            return {"success": False, "error": "OpenAI API key not configured", "model": settings.ai_model}

        prompt_parts = [f"Customer message: {customer_message}"]
        if context:
            prompt_parts.append(f"Additional context: {context}")
        prompt = "\n".join(prompt_parts)

        try:
            response = await self._client.chat.completions.create(
                model=settings.ai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful, empathetic customer support agent. Draft a clear, "
                        "concise reply that directly addresses the customer's message.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            body = response.choices[0].message.content or ""
            return {"success": True, "body": body, "model": settings.ai_model, "prompt": prompt}
        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            return {"success": False, "error": str(e), "model": settings.ai_model, "prompt": prompt}
