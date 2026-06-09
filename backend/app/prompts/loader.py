"""
YAML prompt loader with Jinja2 injection.
Per README §6.2: "Prompt-as-configuration" — YAML templates in version control,
non-technical partners can tune them without touching code.
"""

import os
import yaml
from jinja2 import Template


TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")


def load_prompt(template_name: str, variables: dict = None) -> dict:
    """
    Load a YAML prompt template and inject variables via Jinja2.

    Args:
        template_name: e.g. "positioning" (without .yml)
        variables: dict of variables for Jinja2 injection

    Returns:
        {
            "system": "...",
            "user": "...",
            "model": "claude-sonnet-4-5",
            "temperature": 0.3,
            "max_tokens": 2000,
            "expected_schema": {...}  # optional — JSON schema for validation
        }
    """
    filepath = os.path.join(TEMPLATES_DIR, f"{template_name}.yml")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Prompt template not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if variables:
        raw["system"] = Template(raw.get("system", "")).render(**variables)
        raw["user"] = Template(raw.get("user", "")).render(**variables)

    return raw


def load_all_prompts(variables: dict = None) -> dict[str, dict]:
    """Load all prompt templates from the templates directory."""
    prompts = {}
    if not os.path.exists(TEMPLATES_DIR):
        return prompts

    for filename in os.listdir(TEMPLATES_DIR):
        if filename.endswith(".yml"):
            name = filename[:-4]
            try:
                prompts[name] = load_prompt(name, variables)
            except Exception:
                prompts[name] = {"error": f"Failed to load {filename}"}

    return prompts
