"""Pro Worker AI -- LLM API wrapper.

Supports Anthropic, OpenAI, and Google Gemini APIs.  The ``chat`` method sends a
system prompt plus a list of user/assistant messages and returns the
assistant's text response.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from hosted.config import (
    LLM_PROVIDER,
    ANTHROPIC_API_KEY,
    OPENAI_API_KEY,
    GOOGLE_API_KEY,
    LLM_MODEL,
)

logger = logging.getLogger(__name__)


class LLMClient:
    """Thin async wrapper around Anthropic / OpenAI / Gemini chat APIs."""

    def __init__(self, provider: str | None = None):
        self.provider = (provider or LLM_PROVIDER).lower()

        if self.provider == "anthropic":
            import anthropic

            self._anthropic = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
            self._model = LLM_MODEL
        elif self.provider == "openai":
            import openai

            self._openai = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
            self._model = LLM_MODEL if LLM_MODEL != "claude-sonnet-4-20250514" else "gpt-4o"
        elif self.provider == "gemini":
            import google.generativeai as genai

            genai.configure(api_key=GOOGLE_API_KEY)
            model_name = LLM_MODEL if "gemini" in LLM_MODEL else "gemini-2.0-flash-exp"
            self._gemini = genai.GenerativeModel(model_name)
            self._model = model_name
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

    # ------------------------------------------------------------------
    # Core chat
    # ------------------------------------------------------------------

    async def chat(
        self,
        system: str,
        messages: list[dict[str, str]],
        max_tokens: int = 4096,
    ) -> str:
        """Send a conversation to the LLM and return the assistant reply.

        Parameters
        ----------
        system : str
            The system prompt.
        messages : list[dict]
            List of ``{"role": "user"|"assistant", "content": "..."}`` dicts.
        max_tokens : int
            Maximum tokens for the response.

        Returns
        -------
        str
            The assistant's text reply.
        """
        if self.provider == "anthropic":
            return await self._chat_anthropic(system, messages, max_tokens)
        elif self.provider == "openai":
            return await self._chat_openai(system, messages, max_tokens)
        elif self.provider == "gemini":
            return await self._chat_gemini(system, messages, max_tokens)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    # ------------------------------------------------------------------
    # Anthropic
    # ------------------------------------------------------------------

    async def _chat_anthropic(
        self, system: str, messages: list[dict], max_tokens: int
    ) -> str:
        response = await self._anthropic.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )
        # response.content is a list of content blocks
        text_parts = [
            block.text for block in response.content if hasattr(block, "text")
        ]
        return "\n".join(text_parts)

    # ------------------------------------------------------------------
    # OpenAI
    # ------------------------------------------------------------------

    async def _chat_openai(
        self, system: str, messages: list[dict], max_tokens: int
    ) -> str:
        oai_messages: list[dict[str, str]] = [{"role": "system", "content": system}]
        for m in messages:
            oai_messages.append({"role": m["role"], "content": m["content"]})

        response = await self._openai.chat.completions.create(
            model=self._model,
            messages=oai_messages,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    # ------------------------------------------------------------------
    # Gemini
    # ------------------------------------------------------------------

    async def _chat_gemini(
        self, system: str, messages: list[dict], max_tokens: int
    ) -> str:
        # Gemini's generate_content_async expects a list of parts
        # System instruction can be set via generation_config or prepended
        history = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})

        # Prepend system instruction as first user message
        if system:
            history.insert(0, {"role": "user", "parts": [f"[System Instruction]\n{system}"]})
            history.insert(1, {"role": "model", "parts": ["Understood. I will follow these instructions."]})

        # Start chat with history
        chat = self._gemini.start_chat(history=history[:-1] if len(history) > 1 else [])
        
        # Send the last message
        last_message = history[-1]["parts"][0] if history else ""
        response = await chat.send_message_async(
            last_message,
            generation_config={"max_output_tokens": max_tokens}
        )
        return response.text

    # ------------------------------------------------------------------
    # Assessment helpers
    # ------------------------------------------------------------------

    async def assess_domains(
        self,
        role: str,
        industry: str,
        responsibilities: str = "",
    ) -> list[str]:
        """Use the LLM to suggest relevant expertise domains for assessment.

        Returns a plain list of domain name strings (6-10 items).
        """
        system = (
            "You are an expert in professional skills taxonomy. Given a "
            "person's role, industry, and responsibilities, suggest 6-10 "
            "expertise domains that are most relevant to their daily work. "
            "Return ONLY a JSON array of strings -- no explanation."
        )
        user_msg = (
            f"Role: {role}\n"
            f"Industry: {industry}\n"
            f"Responsibilities: {responsibilities or 'not specified'}"
        )
        raw = await self.chat(system, [{"role": "user", "content": user_msg}], max_tokens=512)
        # Parse JSON array from the response
        try:
            # Strip markdown fences if present
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            domains = json.loads(cleaned)
            if isinstance(domains, list):
                return [str(d) for d in domains]
        except (json.JSONDecodeError, TypeError):
            logger.warning("Failed to parse domain suggestions from LLM: %s", raw[:200])
        # Fallback
        return [
            "Written Communication",
            "Critical Thinking",
            "Project Management",
            "AI Literacy & Tool Usage",
            "Leadership & Collaboration",
            "Domain Expertise",
        ]

    async def extract_assessment_data(
        self,
        conversation: list[dict[str, str]],
    ) -> dict[str, Any]:
        """Ask the LLM to extract structured assessment data from a completed conversation.

        Returns a dict with keys matching what ``compute_all_scores`` and
        ``generate_profile_markdown`` expect.
        """
        system = (
            "You are an assessment scoring assistant for Pro Worker AI. "
            "Given the assessment conversation below, extract ALL the structured data needed. "
            "Return ONLY valid JSON with these exact keys:\n"
            "{\n"
            '  "name": "string",\n'
            '  "role": "string",\n'
            '  "organization": "string",\n'
            '  "industry": "string",\n'
            '  "context_summary": "string (1-2 sentence summary of their work context)",\n'
            '  "answers": {"A1": int, "A2": int, ..., "B1": int, ..., "D1": int, ...},\n'
            '  "domain_ratings": {"DomainName": int, ...},\n'
            '  "career_goals": ["string", ...],\n'
            '  "skills_to_develop": ["string", ...],\n'
            '  "skills_to_protect": ["string", ...],\n'
            '  "tasks_automate": ["string", ...],\n'
            '  "tasks_augment": ["string", ...],\n'
            '  "tasks_coach": ["string", ...],\n'
            '  "tasks_protect": ["string", ...],\n'
            '  "tasks_hands_off": ["string", ...],\n'
            '  "red_lines": ["string", ...],\n'
            '  "learning_style": "string",\n'
            '  "feedback_style": "string",\n'
            '  "communication_style": "string"\n'
            "}\n\n"
            "For answers, use the item IDs (A1-A5, B1-B5, D1-D4) with integer scores 1-5.\n"
            "For domain_ratings, use the domain names as keys with integer ratings 1-5.\n"
            "If information wasn't collected, use reasonable defaults (3 for scores, "
            'empty lists for missing lists, "balanced" for missing styles).\n'
            "Return ONLY the JSON object, no explanation."
        )

        # Build conversation text
        conv_text = "\n".join(
            f"{'USER' if m['role'] == 'user' else 'ASSISTANT'}: {m['content']}"
            for m in conversation
        )

        raw = await self.chat(
            system,
            [{"role": "user", "content": conv_text}],
            max_tokens=4096,
        )

        try:
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            return json.loads(cleaned)
        except (json.JSONDecodeError, TypeError):
            logger.error("Failed to parse assessment extraction: %s", raw[:500])
            raise ValueError("Could not extract assessment data from conversation")
