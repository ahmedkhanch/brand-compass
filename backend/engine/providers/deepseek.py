"""DeepSeek provider — temporary GEO LLM (OpenAI-compatible API)."""

import os
import json
from openai import OpenAI

DEEPSEEK_BASE = "https://api.deepseek.com"


class DeepSeekError(Exception):
    pass


class DeepSeekProvider:
    """Wraps DeepSeek via OpenAI SDK for GEO scoring (temporary stand-in for Claude+Perplexity)."""

    def __init__(self, api_key: str = None):
        api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not api_key or api_key == "sk-...":
            raise DeepSeekError("DEEPSEEK_API_KEY not set")
        self.client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE)

    def chat(self, prompt: str, system: str = None, model: str = "deepseek-chat",
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
            if "401" in msg or "Invalid API Key" in msg:
                raise DeepSeekError("Invalid DEEPSEEK_API_KEY")
            if "402" in msg or "Insufficient Balance" in msg:
                raise DeepSeekError("DeepSeek account has insufficient balance")
            raise DeepSeekError(f"DeepSeek API error: {e}")

    def chat_json(self, prompt: str, system: str = None, model: str = "deepseek-chat",
                  max_tokens: int = 800, temperature: float = 0.3) -> dict:
        """Send a chat and parse the response as JSON. Retries once on failure."""
        full_system = "Return ONLY valid JSON — no preamble, no markdown fences, no extra text."
        if system:
            full_system = system + " " + full_system

        for attempt in range(2):
            raw = self.chat(prompt, system=full_system, model=model,
                            max_tokens=max_tokens, temperature=temperature)
            # Strip markdown code fences if present
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1]
                if raw.endswith("```"):
                    raw = raw[:-3]
                raw = raw.strip()
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                if attempt == 0:
                    continue
                raise DeepSeekError(f"DeepSeek returned unparseable JSON: {raw[:300]}")

        return {}

    def check_health(self) -> dict:
        """Quick health check."""
        resp = self.chat("Reply with exactly: OK", max_tokens=10)
        return {"ok": "OK" in resp, "response": resp[:60]}
