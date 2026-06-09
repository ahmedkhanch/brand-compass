"""OpenAI provider — ChatGPT GEO scoring (gpt-4o-mini). Required by client devis."""

import os
import json
from openai import OpenAI


class OpenAIError(Exception):
    pass


class OpenAIProvider:
    """Wraps OpenAI ChatGPT for GEO scoring — third engine alongside Claude + Perplexity."""

    def __init__(self, api_key: str = None):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "sk-...":
            raise OpenAIError("OPENAI_API_KEY not set or still placeholder")
        self.client = OpenAI(api_key=api_key)

    def chat(self, prompt: str, system: str = None, model: str = "gpt-4o-mini",
             max_tokens: int = 800, temperature: float = 0.3) -> str:
        """Send a chat completion and return the text response."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            resp = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            msg = str(e)
            if "401" in msg or "Invalid API Key" in msg.lower():
                raise OpenAIError("Invalid OPENAI_API_KEY")
            if "429" in msg or "rate_limit" in msg.lower():
                raise OpenAIError("OpenAI rate limit reached")
            raise OpenAIError(f"OpenAI API error: {e}")

    def chat_json(self, prompt: str, system: str = None, model: str = "gpt-4o-mini",
                  max_tokens: int = 800, temperature: float = 0.3) -> dict:
        """Send a chat and parse the response as JSON."""
        full_system = "Return ONLY valid JSON — no preamble, no markdown fences."
        if system:
            full_system = system + " " + full_system

        raw = self.chat(prompt, system=full_system, model=model,
                        max_tokens=max_tokens, temperature=temperature)

        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:]) if len(lines) > 1 else raw
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raise OpenAIError(f"OpenAI returned unparseable JSON: {raw[:300]}")

    def check_health(self) -> dict:
        resp = self.chat("Reply with exactly: OK", max_tokens=10)
        return {"ok": "OK" in resp, "response": resp[:60]}
