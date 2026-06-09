"""
Prompt Engine — Brand Analysis via LLM
Per README §6.2-6.3: takes website content (from Firecrawl) and feeds it to an LLM
to produce positioning, SWOT, competitive analysis, and actionable recommendations.

Currently uses DeepSeek as temporary LLM (Claude pending).
Prompts are loaded from app/prompts/templates/*.yml (Jinja2 + YAML).
"""

import json
import sys
from pathlib import Path

# Ensure backend/ is on path so app.prompts is importable
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from ..providers.deepseek import DeepSeekProvider, DeepSeekError


def _get_llm(deepseek_key: str = None) -> DeepSeekProvider:
    """Get the available LLM provider. Currently DeepSeek-only."""
    return DeepSeekProvider(api_key=deepseek_key)


def _load_prompt(name: str, variables: dict) -> dict:
    """Load a prompt template from YAML. Returns {system, user, model, max_tokens, ...}."""
    try:
        from app.prompts.loader import load_prompt
        return load_prompt(name, variables)
    except Exception:
        return None


def analyze_positioning(brand_name: str, website_text: str, industry: str = "",
                        deepseek_key: str = None) -> dict:
    """
    Analyze brand positioning from website content.
    Returns archetype, value proposition, target audience, brand voice, differentiators, weaknesses.
    """
    llm = _get_llm(deepseek_key)
    tmpl = _load_prompt("positioning", {
        "brand_name": brand_name,
        "industry": industry,
        "website_text": website_text[:6000],
    })

    system = tmpl["system"] if tmpl else "You are a senior brand strategist. Return ONLY valid JSON."
    prompt = tmpl["user"] if tmpl else f"Analyze {brand_name}"
    max_tokens = tmpl.get("max_tokens", 1500) if tmpl else 1500

    try:
        return llm.chat_json(prompt, system=system, max_tokens=max_tokens)
    except DeepSeekError as e:
        return {"error": str(e)}


def analyze_swot(brand_name: str, website_text: str, industry: str = "",
                 deepseek_key: str = None) -> dict:
    """
    Generate SWOT analysis from website content.
    Returns strengths, weaknesses, opportunities, threats, and executive summary.
    """
    llm = _get_llm(deepseek_key)
    tmpl = _load_prompt("swot", {
        "brand_name": brand_name,
        "industry": industry,
        "website_text": website_text[:6000],
    })

    system = tmpl["system"] if tmpl else "You are a senior brand strategist. Return ONLY valid JSON."
    prompt = tmpl["user"] if tmpl else f"SWOT analysis for {brand_name}"
    max_tokens = tmpl.get("max_tokens", 1500) if tmpl else 1500

    try:
        return llm.chat_json(prompt, system=system, max_tokens=max_tokens)
    except DeepSeekError as e:
        return {"error": str(e)}


def analyze_competitive(brand_name: str, website_text: str, industry: str = "",
                        competitor: str = "", deepseek_key: str = None) -> dict:
    """
    Analyze competitive landscape.
    Identifies competitors, compares positioning, and maps the market.
    """
    llm = _get_llm(deepseek_key)
    tmpl = _load_prompt("competitive", {
        "brand_name": brand_name,
        "industry": industry,
        "competitor": competitor,
        "website_text": website_text[:6000],
    })

    system = tmpl["system"] if tmpl else "You are a competitive intelligence analyst. Return ONLY valid JSON."
    prompt = tmpl["user"] if tmpl else f"Competitive landscape for {brand_name}"
    max_tokens = tmpl.get("max_tokens", 1200) if tmpl else 1200

    try:
        return llm.chat_json(prompt, system=system, max_tokens=max_tokens)
    except DeepSeekError as e:
        return {"error": str(e)}


def generate_recommendations(brand_name: str, website_text: str, industry: str = "",
                             seo_score: int = 0, swot: dict = None,
                             deepseek_key: str = None) -> dict:
    """
    Generate actionable recommendations based on all analysis.
    Combines SEO score, SWOT, and website content for holistic advice.
    """
    llm = _get_llm(deepseek_key)

    swot_context = ""
    if swot and "error" not in swot:
        swot_context = (
            f"SWOT analysis:\n"
            f"Strengths: {json.dumps(swot.get('strengths', []))}\n"
            f"Weaknesses: {json.dumps(swot.get('weaknesses', []))}\n"
            f"Opportunities: {json.dumps(swot.get('opportunities', []))}\n"
            f"Threats: {json.dumps(swot.get('threats', []))}\n"
        )

    tmpl = _load_prompt("recommendations", {
        "brand_name": brand_name,
        "industry": industry,
        "seo_score": str(seo_score),
        "swot_context": swot_context,
        "website_text": website_text[:4000],
    })

    system = tmpl["system"] if tmpl else "You are a brand strategy consultant. Return ONLY valid JSON."
    prompt = tmpl["user"] if tmpl else f"Recommendations for {brand_name}"
    max_tokens = tmpl.get("max_tokens", 1500) if tmpl else 1500

    try:
        return llm.chat_json(prompt, system=system, max_tokens=max_tokens)
    except DeepSeekError as e:
        return {"error": str(e)}


def run_prompt_engine(brand_name: str, website_text: str, industry: str = "",
                      competitor: str = "", seo_score: int = 0,
                      deepseek_key: str = None) -> dict:
    """
    Run the full Prompt Engine pipeline.
    Firecrawl content → LLM → positioning, SWOT, competitive, recommendations.

    Returns a dict with all four analysis sections.
    """
    results = {
        "positioning": None,
        "swot": None,
        "competitive": None,
        "recommendations": None,
    }

    # 1. Positioning
    try:
        results["positioning"] = analyze_positioning(
            brand_name, website_text, industry, deepseek_key
        )
    except Exception as e:
        results["positioning"] = {"error": str(e)}

    # 2. SWOT
    try:
        results["swot"] = analyze_swot(
            brand_name, website_text, industry, deepseek_key
        )
    except Exception as e:
        results["swot"] = {"error": str(e)}

    # 3. Competitive
    try:
        results["competitive"] = analyze_competitive(
            brand_name, website_text, industry, competitor, deepseek_key
        )
    except Exception as e:
        results["competitive"] = {"error": str(e)}

    # 4. Recommendations (uses SWOT + SEO context)
    try:
        results["recommendations"] = generate_recommendations(
            brand_name, website_text, industry, seo_score,
            results.get("swot"), deepseek_key
        )
    except Exception as e:
        results["recommendations"] = {"error": str(e)}

    return results
