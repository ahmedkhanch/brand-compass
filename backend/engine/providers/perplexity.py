"""Perplexity provider — real-time web-aware competitive intelligence."""

import os
import requests


class PerplexityError(Exception):
    pass


class PerplexityProvider:
    """Wraps Perplexity API for competitive intel, market trends, and GEO scoring."""

    API_URL = "https://api.perplexity.ai/chat/completions"

    def __init__(self, api_key: str = None):
        api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        if not api_key or api_key.startswith("pplx-..."):
            raise PerplexityError("PERPLEXITY_API_KEY not set or still placeholder")
        self.api_key = api_key

    def chat(self, prompt: str, system: str = None, model: str = "sonar",
             max_tokens: int = 800, temperature: float = 0.3) -> str:
        """Send a chat completion and return the text response."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        body = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            resp = requests.post(self.API_URL, headers=headers, json=body, timeout=45)
            if resp.status_code == 401:
                raise PerplexityError("Invalid PERPLEXITY_API_KEY")
            if resp.status_code == 429:
                raise PerplexityError("Perplexity rate limit reached")
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except requests.exceptions.RequestException as e:
            raise PerplexityError(f"Perplexity API error: {e}")

    def chat_json(self, prompt: str, system: str = None, model: str = "sonar",
                  max_tokens: int = 800, temperature: float = 0.3) -> dict:
        """Send a chat and parse the response as JSON."""
        import json

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
            raise PerplexityError(f"Perplexity returned unparseable JSON: {raw[:300]}")

    def check_health(self) -> dict:
        resp = self.chat("Reply with exactly: OK", max_tokens=10)
        return {"ok": "OK" in resp, "response": resp[:60]}
