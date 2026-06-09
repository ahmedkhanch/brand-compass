"""Claude provider — Anthropic SDK wrapper for brand analysis."""

import os
import json
from anthropic import Anthropic


class ClaudeError(Exception):
    pass


class ClaudeProvider:
    """Wraps Anthropic Claude for positioning, SWOT, competitive analysis, and GEO scoring."""

    def __init__(self, api_key: str = None):
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key or api_key.startswith("sk-ant-..."):
            raise ClaudeError("ANTHROPIC_API_KEY not set or still placeholder")
        self.client = Anthropic(api_key=api_key)

    def chat(self, prompt: str, system: str = None, model: str = "claude-sonnet-4-5",
             max_tokens: int = 2000, temperature: float = 0.3) -> str:
        """Send a message and return the text response."""
        messages = [{"role": "user", "content": prompt}]
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature,
        }
        if system:
            kwargs["system"] = system

        try:
            resp = self.client.messages.create(**kwargs)
            return resp.content[0].text.strip()
        except Exception as e:
            msg = str(e)
            if "401" in msg or "authentication" in msg.lower():
                raise ClaudeError("Invalid ANTHROPIC_API_KEY")
            if "429" in msg or "rate_limit" in msg.lower():
                raise ClaudeError("Claude rate limit reached")
            raise ClaudeError(f"Claude API error: {e}")

    def chat_json(self, prompt: str, system: str = None, model: str = "claude-sonnet-4-5",
                  max_tokens: int = 2000, temperature: float = 0.3) -> dict:
        """Send a chat and parse the response as JSON."""
        full_system = "Return ONLY valid JSON — no preamble, no markdown fences."
        if system:
            full_system = system + " " + full_system

        raw = self.chat(prompt, system=full_system, model=model,
                        max_tokens=max_tokens, temperature=temperature)

        # Strip markdown fences if present
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
            raise ClaudeError(f"Claude returned unparseable JSON: {raw[:300]}")

    def check_health(self) -> dict:
        resp = self.chat("Reply with exactly: OK", max_tokens=10)
        return {"ok": "OK" in resp, "response": resp[:60]}
