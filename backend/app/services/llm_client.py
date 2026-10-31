
"""LLM provider abstraction for Vest IQ's personal fashion stylist."""

import logging

import httpx

from app.core.configuration import settings

logger = logging.getLogger("vestiq.llm")

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models"

REFUSAL_REPLY = (
    "I can't help with that one, but I'm happy to help "
    "with clothing and styling ideas."
)


class LLMError(Exception):
    kind = "provider_error"


class LLMNotConfigured(LLMError):
    kind = "not_configured"


class LLMTimeout(LLMError):
    kind = "timeout"


class LLMProviderError(LLMError):
    kind = "provider_error"


def _message_text(content) -> str:
    """Convert string or text-block message content into plain text."""
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        return "\n".join(
            block["text"]
            for block in content
            if isinstance(block, dict)
            and block.get("type") == "text"
            and isinstance(block.get("text"), str)
        )

    return ""


class LLMProvider:
    async def complete(self, system: str, messages: list[dict]) -> str:
        raise NotImplementedError


class GeminiProvider(LLMProvider):
    def __init__(
        self,
        api_key: str,
        model: str,
        timeout: float,
        max_tokens: int,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.transport = transport

    async def complete(self, system: str, messages: list[dict]) -> str:
        contents = []

        for message in messages:
            role = message.get("role")
            content = message.get("content", "")
            if isinstance(content, list):
                parts = [part for part in content if isinstance(part, dict) and ("text" in part or "inline_data" in part or "inlineData" in part)]
            else:
                text = _message_text(content)
                parts = [{"text": text}] if text else []

            if not parts:
                continue
            if role == "assistant":
                gemini_role = "model"
            elif role in ("user", "system"):
                gemini_role = "user"
            else:
                continue

            # Keep images as separate parts; merge only adjacent turns of the same role.
            if contents and contents[-1]["role"] == gemini_role:
                contents[-1]["parts"].extend(parts)
            else:
                contents.append({"role": gemini_role, "parts": parts})

        if not contents:
            raise LLMProviderError("No usable chat messages were provided.")

        payload = {
            "systemInstruction": {
                "parts": [{"text": system}]
            },
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": self.max_tokens,
            },
        }

        headers = {
            "x-goog-api-key": self.api_key,
            "content-type": "application/json",
        }

        url = f"{GEMINI_URL}/{self.model}:generateContent"

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                transport=self.transport,
            ) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                )
        except httpx.TimeoutException:
            logger.warning("Gemini request timed out")
            raise LLMTimeout("The stylist took too long to respond.")
        except httpx.HTTPError:
            logger.warning("Gemini request failed before a response was received")
            raise LLMProviderError("Could not reach Gemini.")

        if response.status_code != 200:
            # Log only the status code; never log keys or user prompts.
            logger.warning("Gemini returned HTTP %s", response.status_code)
            raise LLMProviderError(
                f"Gemini returned HTTP {response.status_code}."
            )

        try:
            data = response.json()
            candidates = data.get("candidates", [])
            parts = candidates[0]["content"]["parts"] if candidates else []
            text = "".join(
                part.get("text", "")
                for part in parts
                if isinstance(part, dict)
            ).strip()
        except (ValueError, KeyError, IndexError, TypeError):
            raise LLMProviderError("Gemini returned an unreadable response.")

        if not text:
            block_reason = data.get("promptFeedback", {}).get("blockReason")
            if block_reason:
                return REFUSAL_REPLY
            raise LLMProviderError("Gemini returned an empty response.")

        return text


class AnthropicProvider(LLMProvider):
    def __init__(
        self,
        api_key: str,
        model: str,
        timeout: float,
        max_tokens: int,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.transport = transport

    async def complete(self, system: str, messages: list[dict]) -> str:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system,
            "messages": messages,
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                transport=self.transport,
            ) as client:
                response = await client.post(
                    ANTHROPIC_URL,
                    headers=headers,
                    json=payload,
                )
        except httpx.TimeoutException:
            logger.warning("Anthropic request timed out")
            raise LLMTimeout("The stylist took too long to respond.")
        except httpx.HTTPError:
            logger.warning("Anthropic request failed")
            raise LLMProviderError("Could not reach Anthropic.")

        if response.status_code != 200:
            logger.warning("Anthropic returned HTTP %s", response.status_code)
            raise LLMProviderError(
                f"Anthropic returned HTTP {response.status_code}."
            )

        try:
            data = response.json()
            text = "".join(
                block.get("text", "")
                for block in data.get("content", [])
                if isinstance(block, dict)
                and block.get("type") == "text"
            ).strip()
        except (ValueError, TypeError):
            raise LLMProviderError("Anthropic returned an unreadable response.")

        if not text:
            if data.get("stop_reason") == "refusal":
                return REFUSAL_REPLY
            raise LLMProviderError("Anthropic returned an empty response.")

        return text


def get_llm_provider() -> LLMProvider:
    provider = (settings.LLM_PROVIDER or "").strip().lower()
    api_key = settings.LLM_API_KEY
    model = settings.LLM_MODEL

    if not api_key:
        raise LLMNotConfigured("LLM_API_KEY is not configured.")

    common = {
        "api_key": api_key,
        "model": model,
        "timeout": settings.LLM_TIMEOUT_SECONDS,
        "max_tokens": settings.LLM_MAX_TOKENS,
    }

    if provider == "gemini":
        return GeminiProvider(**common)

    if provider == "anthropic":
        return AnthropicProvider(**common)

    raise LLMNotConfigured(
        f"Unsupported LLM_PROVIDER '{provider}'."
    )
