"""
Demo / mock providers — brand-seeded, deterministic stand-ins for every paid API.

When DEMO_MODE is on OR a specific API key is missing, the call sites in the
scorers and orchestrator construct these instead of the real providers. Each
provider auto-switches independently: add FIRECRAWL_API_KEY → Firecrawl becomes
real; add DEEPSEEK_API_KEY → DeepSeek becomes real; etc. Providers without keys
keep serving mock data (graceful degradation — never crash).

The REAL scoring math, report assembly, SSE progress and cost tracking still run
end-to-end — only the outbound HTTP calls (Firecrawl / SerpAPI / DeepSeek /
Claude / OpenAI / Perplexity / Apify) are replaced by realistic, brand-tailored
fixtures when a key is missing.

Everything is seeded from the brand name so the same brand always yields the same
report (good for a live demo), while different brands look genuinely different.
"""

import re
import sys
import random
from pathlib import Path

# Ensure backend/ is importable so `app.config` resolves regardless of cwd
# (pytest, ARQ worker thread, direct script) — mirrors positioning.py/main.py.
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.config import settings


def demo_enabled() -> bool:
    """Master override: when True, every provider stays mocked regardless of keys."""
    return bool(getattr(settings, "DEMO_MODE", False))


def provider_ready(key_name: str) -> bool:
    """True when demo is OFF AND the named API key is present (non-empty, non-placeholder).

    Use this at every gate point so each paid provider switches independently:
        if provider_ready("FIRECRAWL_API_KEY"):  real;  else:  mock.
    """
    if demo_enabled():
        return False
    key = getattr(settings, key_name, None)
    if not key:
        return False
    if isinstance(key, str) and key.endswith("..."):
        return False  # placeholder like "sk-..." — not a real key
    return True


def _seed(*parts: str) -> random.Random:
    """Deterministic RNG seeded from the given strings (stable across runs)."""
    return random.Random("::".join(p.lower().strip() for p in parts if p))


def _extract_domain(url: str) -> str:
    return (
        url.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
        if url else "example.com"
    )


# ── Brand / industry extraction from a prompt (the LLM mock only sees the prompt) ──
_BRAND_PATTERNS = [
    r"Brand:\s*([^\n]+)",
    r"know about ([A-Za-z0-9&'’\- ]+?)\?",
    r"perception of ([A-Za-z0-9&'’\- ]+?) in the",
    r"Describe ([A-Za-z0-9&'’\- ]+?) in one sentence",
    r"what makes ([A-Za-z0-9&'’\- ]+?) unique",
]
_INDUSTRY_PATTERNS = [
    r"Industry:\s*([^\n]+)",
    r"in the ([A-Za-z0-9&'’\- ]+?) industry",
]


def _extract(prompt: str, patterns: list[str], default: str) -> str:
    for pat in patterns:
        m = re.search(pat, prompt)
        if m:
            val = m.group(1).strip()
            if val and val.lower() not in ("", "{ industry }", "{ brand_name }"):
                return val
    return default


# ── Fixture pools (picked deterministically per brand) ───────────────────────
_ARCHETYPES = ["Hero", "Creator", "Explorer", "Sage", "Magician", "Ruler", "Everyman"]
_VOICE = ["confident", "aspirational", "authentic", "energetic", "premium",
          "approachable", "bold", "trustworthy", "innovative", "warm"]
_PRICE_AXIS = ["mainstream", "premium", "luxury"]
_APPEAL_AXIS = ["emotional", "mixed", "functional"]
_MARKET_POS = ["strong challenger", "market leader", "niche player", "emerging"]
_THREAT = ["high", "medium", "low"]


class MockFirecrawl:
    """Returns plausible homepage markdown + metadata for a brand."""

    def __init__(self, brand_name: str = "", industry: str = "", api_key: str = None):
        self.brand = brand_name or "The Brand"
        self.industry = industry or "its market"

    def extract_text(self, url: str):
        rng = _seed(self.brand, "site")
        tagline = rng.choice([
            f"{self.brand} — built for people who expect more.",
            f"Discover {self.brand}: {self.industry} done right.",
            f"{self.brand}. Quality, crafted with intent.",
        ])
        md = (
            f"# {self.brand}\n\n{tagline}\n\n"
            f"## Why {self.brand}\n\n"
            f"{self.brand} is a leading name in {self.industry}, trusted by thousands of "
            f"customers for premium quality, thoughtful design and dependable service. "
            f"Our collection spans everyday essentials to flagship products.\n\n"
            f"## Our products\n\nExplore the new season range — engineered materials, "
            f"sustainable sourcing and a relentless focus on customer experience.\n\n"
            f"## About us\n\nFounded with a simple mission: make {self.industry} better. "
            f"Today {self.brand} ships worldwide with award-winning support.\n"
        )
        meta = {
            "title": f"{self.brand} — Official Site",
            "description": tagline,
        }
        return md, meta

    def scrape(self, url: str, **kw):
        md, meta = self.extract_text(url)
        return {"success": True, "data": {"markdown": md, "metadata": meta}}

    def check_health(self):
        return {"ok": True}


class MockSerp:
    """Returns Google SERP-shaped fixtures so the real SEO scorer computes a strong score."""

    def __init__(self, brand_name: str = "", brand_domain: str = "", api_key: str = None):
        self.brand = brand_name or "Brand"
        self.domain = brand_domain or "example.com"

    def search(self, query: str, num: int = 10, **extra) -> dict:
        q = query.lower()
        rng = _seed(self.brand, query)
        brand_l = self.brand.lower()

        # Negative-content probe → no negative triggers (clean reputation).
        if "complaint" in q or "reviews complaints" in q:
            return {"organic_results": [
                {"link": f"https://{self.domain}/reviews",
                 "title": f"{self.brand} Reviews — Verified Customer Ratings",
                 "snippet": f"Customers rate {self.brand} highly for quality and service."},
                {"link": "https://www.trustpilot.com/review/" + self.domain,
                 "title": f"{self.brand} is rated Excellent",
                 "snippet": "4.6 / 5 based on thousands of reviews."},
            ]}

        is_brand_query = brand_l in q
        organic = []
        if is_brand_query:
            # Brand owns #1 for its own name; the rest are third-party references.
            organic = [
                {"link": f"https://{self.domain}/", "title": f"{self.brand} — Official Site",
                 "snippet": f"The official home of {self.brand}."},
                {"link": "https://en.wikipedia.org/wiki/" + self.brand.replace(" ", "_"),
                 "title": f"{self.brand} - Wikipedia", "snippet": "Encyclopedia entry."},
                {"link": "https://www.linkedin.com/company/" + self.domain.split(".")[0],
                 "title": f"{self.brand} | LinkedIn", "snippet": "Company profile."},
            ]
            # A knowledge panel is typical for established brands; PAA/related vary by brand.
            paa = [{"question": f"Is {self.brand} a good brand?"},
                   {"question": f"Where is {self.brand} based?"},
                   {"question": f"Who owns {self.brand}?"}]
            rel = [{"query": f"{self.brand} reviews"}, {"query": f"{self.brand} products"}]
            if rng.random() > 0.4:
                paa.append({"question": f"What does {self.brand} sell?"})
            if rng.random() > 0.5:
                rel.append({"query": f"{self.brand} near me"})
            return {
                "organic_results": organic,
                "knowledge_graph": {"title": self.brand, "type": "Brand"},
                "related_questions": paa,
                "related_searches": rel,
            }

        # Keyword query (brand not named): brand ranks at a seeded position 2–6 or absent.
        brand_pos = rng.choice([2, 3, 4, 5, None, None])
        for i in range(1, 8):
            if i == brand_pos:
                organic.append({"link": f"https://{self.domain}/c/{abs(hash(query)) % 99}",
                                "title": f"{self.brand} — {query.title()}",
                                "snippet": f"Shop {query} at {self.brand}."})
            else:
                organic.append({"link": f"https://competitor{i}.com/{query.replace(' ', '-')}",
                                "title": f"{query.title()} | Result {i}",
                                "snippet": "A competing result."})
        return {"organic_results": organic,
                "related_questions": [{"question": f"best {query}?"}],
                "related_searches": [{"query": f"{query} brands"}]}

    def check_health(self):
        return {"ok": True, "total_results": 1234567}


class MockLLM:
    """
    Mock LLM that detects which prompt it received (positioning / SWOT / competitive /
    recommendations / GEO probes) and returns the matching JSON shape. Brand and
    industry are parsed out of the prompt so output is brand-specific.
    """

    def __init__(self, engine: str = "claude", api_key: str = None):
        self.engine = engine

    def chat(self, prompt: str, system: str = None, **kw) -> str:
        return f"{self.engine} mock response"

    def chat_json(self, prompt: str, system: str = None, **kw) -> dict:
        brand = _extract(prompt, _BRAND_PATTERNS, "the brand")
        industry = _extract(prompt, _INDUSTRY_PATTERNS, "the market")
        rng = _seed(brand, self.engine, prompt[:40])
        p = prompt

        # ── Prompt-engine sections (detected by their distinctive JSON keys) ──
        if "archetype" in p:
            return {
                "archetype": _seed(brand).choice(_ARCHETYPES),
                "value_proposition": f"{brand} delivers premium {industry} with a focus on "
                                     f"quality, design and customer trust.",
                "target_audience": f"Quality-conscious customers seeking dependable {industry} "
                                   f"from a brand they can believe in.",
                "brand_voice": _seed(brand, "voice").sample(_VOICE, 5),
                "differentiators": [
                    "Distinctive, recognisable brand identity",
                    "Strong product quality and craftsmanship",
                    "Loyal, engaged customer community",
                    "Consistent omnichannel experience",
                ],
                "weaknesses": [
                    "Limited presence in emerging segments",
                    "Higher price point than discount rivals",
                    "Room to grow international awareness",
                ],
                "positioning": {
                    "price_axis": _seed(brand, "price").choice(_PRICE_AXIS),
                    "appeal_axis": _seed(brand, "appeal").choice(_APPEAL_AXIS),
                },
            }

        if "direct_competitors" in p:
            comp_seed = _seed(brand, industry, "comp")
            names = comp_seed.sample(
                ["Apex", "Northwind", "Vanta", "Lumen", "Orbit", "Cardinal", "Helio", "Forge"], 3
            )
            return {
                "direct_competitors": [
                    {"name": n,
                     "positioning": f"{n} competes on "
                                    f"{comp_seed.choice(['price', 'scale', 'design', 'speed'])} in {industry}.",
                     "threat_level": lvl}
                    for n, lvl in zip(names, ["high", "medium", "low"])
                ],
                "brand_differentiator": f"{brand} stands out through brand strength and a premium, "
                                        f"trust-led customer experience competitors struggle to match.",
                "market_position": _seed(brand, "pos").choice(_MARKET_POS),
                "competitive_advantage": f"{brand}'s brand equity and loyal community form a moat "
                                         f"that is hard to replicate.",
                "competitive_threat": "Fast-moving, lower-priced challengers compressing margins.",
            }

        if "quick_wins" in p:
            return {
                "quick_wins": [
                    {"action": f"Publish a comparison page targeting '{industry} alternatives'",
                     "impact": "high", "effort": "days"},
                    {"action": "Add structured data (FAQ + Product schema) to key pages",
                     "impact": "medium", "effort": "hours"},
                    {"action": "Launch a retargeting campaign on warm Meta audiences",
                     "impact": "high", "effort": "days"},
                ],
                "strategic_moves": [
                    {"action": f"Build a content engine to own '{industry}' informational queries",
                     "timeframe": "6 months"},
                    {"action": "Stand up a referral / loyalty program to compound brand advocacy",
                     "timeframe": "3 months"},
                ],
                "priority_focus": f"Convert {brand}'s strong brand awareness into measurable organic "
                                  f"and paid demand capture.",
                "executive_summary": f"{brand} has a strong foundation in {industry}. The biggest "
                                     f"near-term lever is search + paid demand capture; the long-term "
                                     f"play is owning category content and deepening loyalty.",
            }

        if '"strengths"' in p or ("strengths" in p and "threats" in p):
            return {
                "strengths": [
                    "Recognisable, well-regarded brand",
                    "High product quality",
                    "Loyal customer base",
                    "Clear value proposition",
                    "Solid organic search presence",
                ],
                "weaknesses": [
                    "Premium pricing limits reach",
                    "Under-invested paid acquisition",
                    "Thin presence on emerging channels",
                ],
                "opportunities": [
                    f"Growing demand in {industry}",
                    "International expansion",
                    "AI-assisted personalisation",
                ],
                "threats": [
                    "Aggressive low-cost competitors",
                    "Rising customer-acquisition costs",
                    "Platform algorithm volatility",
                ],
                "executive_summary": f"{brand} holds a defensible position in {industry} thanks to "
                                     f"brand strength and product quality, but must modernise demand "
                                     f"generation to fend off lower-priced challengers.",
            }

        # ── GEO probes (per-engine variance so the score isn't always maxed) ──
        if "top_brands" in p:
            eng_seed = _seed(brand, self.engine, "rank")
            mentioned = eng_seed.random() > 0.3  # ~70% of engines rank the brand
            others = _seed(industry, "top").sample(
                ["Apex", "Northwind", "Vanta", "Lumen", "Orbit", "Cardinal"], 4)
            top = ([brand] + others) if mentioned else others
            return {"top_brands": top[:5], "brand_mentioned": mentioned,
                    "rank_if_mentioned": eng_seed.choice([1, 2, 2, 3]) if mentioned else None}

        if "sentiment_score" in p:
            eng_seed = _seed(brand, self.engine, "sent")
            positive = eng_seed.random() > 0.25  # ~75% positive, rest neutral
            return {
                "sentiment": "positive" if positive else "neutral",
                "sentiment_score": eng_seed.choice([7, 8, 9]) if positive else eng_seed.choice([5, 6]),
                "pros": ["Strong brand reputation", "Reliable product quality",
                         "Good customer experience"],
                "cons": ["Premium pricing", "Limited budget options"],
                "recommendation": f"{brand} is well regarded within {industry}.",
            }

        if "one-sentence description" in p or "introducing it to someone" in p or '"description"' in p:
            variants = [
                f"{brand} is a respected {industry} brand known for quality and a strong, "
                f"loyal customer following.",
                f"{brand} is a leading {industry} company recognised for premium products and a "
                f"distinctive brand identity.",
                f"{brand} is a well-known name in {industry}, trusted for dependable quality and "
                f"a great customer experience.",
            ]
            return {"description": _seed(brand, self.engine).choice(variants)}

        if "brand_description" in p or "What do you know about" in p:
            return {
                "mentioned": True,
                "brand_description": f"{brand} is an established brand in {industry}, known for "
                                     f"premium quality and a loyal customer base.",
                "industry": industry,
                "confidence": _seed(brand, self.engine, "conf").choice(["high", "medium", "medium", "low"]),
            }

        return {}

    def check_health(self):
        return {"ok": True, "response": "OK"}
