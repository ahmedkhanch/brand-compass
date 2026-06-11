"""
SEO Scoring Engine
Per README §6.4 — scores brand search engine performance 0–100.

Formula:
  1. Brand SERP ownership (0–30 pts)
  2. Keyword ranking average (0–40 pts)
  3. SERP feature presence (0–20 pts)
  4. Negative content check (0–10 pts, inverted)
"""

import re
import os
from ..providers.serpapi import SerpAPIProvider
from ..providers.firecrawl import FirecrawlProvider


def _extract_domain(url: str) -> str:
    """Extract bare domain from a URL."""
    return url.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]


# Keyword generation constants
# For MVP, we use industry-anchored keywords + page signals, not random nav links.

INDUSTRY_KEYWORD_MAP: dict[str, list[str]] = {
    "sportswear": [
        "athletic wear", "running shoes", "sports apparel",
        "gym clothes", "workout gear", "athletic footwear",
    ],
    "tech": [
        "consumer electronics", "smartphones", "laptops",
        "software", "tech innovation", "best tech products",
    ],
    "travel": [
        "vacation rentals", "travel booking", "holiday stays",
        "best travel deals", "online travel platform",
    ],
    "fmcg": [
        "coffee machines", "coffee pods", "espresso at home",
        "best coffee brands", "premium coffee",
    ],
    "retail": [
        "online shopping", "ecommerce platform", "best deals online",
        "retail store", "shop online",
    ],
    "finance": [
        "banking services", "credit cards", "investment platform",
        "personal finance", "online banking",
    ],
    "healthcare": [
        "health services", "medical care", "healthcare provider",
        "telehealth", "patient care",
    ],
    "automotive": [
        "car manufacturer", "electric vehicles", "auto industry",
        "best cars", "vehicle safety",
    ],
}

# Words that indicate a nav/CTA element, not a keyword
NAV_BLACKLIST = {
    "shop", "buy", "cart", "menu", "search", "close", "open",
    "sign in", "log in", "register", "subscribe", "join", "follow",
    "learn more", "read more", "view all", "see all", "get started",
    "contact", "support", "help", "faq", "about us", "privacy",
    "terms", "shipping", "returns", "size guide", "store locator",
}


def _is_nav_or_cta(text: str) -> bool:
    """Check if a candidate is a navigation link or CTA, not a real keyword."""
    text_lower = text.strip().lower()
    # Exact blacklist match
    if text_lower in NAV_BLACKLIST:
        return True
    # Starts with shop/buy pattern
    if re.match(r'^(shop|buy|get|find|browse|explore|discover)\s', text_lower):
        return True
    # Very short (1-2 chars)
    if len(text_lower) <= 2:
        return True
    # Pure numbers or symbols
    if re.match(r'^[\d\s\.\,\;\:\!\?\-]+$', text_lower):
        return True
    return False


def _get_industry_keywords(industry: str, max_count: int = 4) -> list[str]:
    """Return pre-built keyword list for a given industry."""
    industry_lower = industry.lower().strip()

    # Direct match
    for key, keywords in INDUSTRY_KEYWORD_MAP.items():
        if key in industry_lower or industry_lower in key:
            return keywords[:max_count]

    # Partial match
    for key, keywords in INDUSTRY_KEYWORD_MAP.items():
        if any(word in industry_lower for word in key.split()):
            return keywords[:max_count]

    # Generic fallback
    return [f"{industry} brands", f"best {industry} products", f"{industry} services"]


def _extract_content_phrases(markdown: str) -> list[str]:
    """
    Extract meaningful content phrases from markdown by stripping out
    navigation, boilerplate, and formatting noise.
    Returns clean text blocks that might contain keywords.
    """
    # Remove markdown links — keep the text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', markdown)
    # Remove images
    text = re.sub(r'!\[.*?\]\([^\)]+\)', '', text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove markdown formatting symbols
    text = re.sub(r'[\*\_\#\>\|\`\~]+', ' ', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text)

    # Split into lines, keep non-empty ones
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    # Filter out nav/CTA lines
    lines = [l for l in lines if not _is_nav_or_cta(l) and len(l) > 10]
    return lines


def _score_keyword_quality(text: str, brand_name: str) -> int:
    """
    Score a candidate keyword for SEO relevance. Higher = better keyword.
    Penalize: nav patterns, ALL CAPS, full sentences, brand mentions.
    """
    score = 0
    text = text.strip()
    words = text.split()
    word_count = len(words)

    # Reject outright: nav/CTA patterns
    if _is_nav_or_cta(text):
        return -10

    # Ideal keyword length: 2-5 words
    if 2 <= word_count <= 5:
        score += 4
    elif word_count == 1:
        score += 2
    elif 5 < word_count <= 8:
        score += 1
    else:
        score -= 3  # too long

    # Penalize ALL CAPS (marketing tagline)
    if text.isupper():
        score -= 4

    # Penalize if it ends with punctuation (sentence-like)
    if text.endswith((".", "!", "?")):
        score -= 2

    # Penalize if it contains the brand name
    if brand_name.lower() in text.lower():
        score -= 3

    # Bonus for product/category words
    product_indicators = [
        "shoe", "shoes", "shirt", "jacket", "pant", "gear", "equipment", "wear",
        "running", "training", "basketball", "soccer", "football", "gym", "fitness",
        "collection", "sale", "new", "best", "top", "latest",
        "men", "women", "kids", "accessories", "clothing", "apparel", "footwear",
        "phone", "laptop", "computer", "tablet", "watch", "device",
        "software", "service", "platform", "solution", "tool", "product",
        "brand", "store", "online", "official", "shop", "quality", "premium",
    ]
    text_lower = text.lower()
    bonus = 0
    for indicator in product_indicators:
        if indicator in text_lower:
            bonus = 3
            break
    score += bonus

    return score


def _extract_keywords_from_markdown(markdown: str, brand_name: str, industry: str = "",
                                     max_keywords: int = 4) -> list[str]:
    """
    Extract SEO-relevant keywords using industry knowledge + page content.

    Strategy (MVP):
    1. Start with industry-anchored keywords (most reliable signal)
    2. Scan page content for product/category terms
    3. Always include the brand name
    4. Fall back to brand + industry combos
    """
    candidates: list[tuple[str, int]] = []

    # ── Source 1: Industry-anchored keywords (highest quality) ──
    industry_keywords = _get_industry_keywords(industry, max_count=6)
    for kw in industry_keywords:
        candidates.append((kw, 8))  # high baseline quality

    # ── Source 2: Content phrases from page ──
    phrases = _extract_content_phrases(markdown)
    for phrase in phrases:
        quality = _score_keyword_quality(phrase, brand_name)
        if quality >= 2:  # stricter threshold — only good candidates
            candidates.append((phrase, quality))

    # ── Source 3: Brand name ──
    candidates.append((brand_name, 10))

    # ── Source 4: Brand + industry combo ──
    if industry:
        candidates.append((f"{brand_name} {industry}", 7))

    # Deduplicate by lowercase, keep highest quality
    seen: dict[str, tuple[str, int]] = {}
    for text, quality in candidates:
        key = text.lower()
        if key not in seen or quality > seen[key][1]:
            seen[key] = (text, quality)

    # Sort by quality descending
    sorted_candidates = sorted(seen.values(), key=lambda x: x[1], reverse=True)

    # Take top N, always including brand name
    result = []
    has_brand = False
    for text, _ in sorted_candidates:
        if text.lower() == brand_name.lower():
            has_brand = True
        result.append(text)
        if len(result) >= max_keywords:
            break

    if not has_brand:
        result.insert(0, brand_name)
        result = result[:max_keywords]

    return result[:max_keywords]


def _score_position(position: int) -> int:
    """Convert a SERP position to points (out of 12). Calibrated for realistic brand scoring."""
    if position == 1:
        return 12
    elif position in (2, 3):
        return 9
    elif position in (4, 5):
        return 7
    elif 6 <= position <= 10:
        return 4
    return 0


def score_seo(brand_name: str, website_url: str, industry: str = "",
              serpapi_key: str = None, firecrawl_key: str = None) -> dict:
    """
    Compute the SEO score (0–100) for a brand.

    Returns:
        {
            "score": 72,
            "label": "Strong",
            "breakdown": {
                "serp_ownership": 27,
                "keyword_ranking": 28,
                "serp_features": 12,
                "negative_content": 5
            },
            "details": {...}
        }
    """
    brand_domain = _extract_domain(website_url)
    from .. providers.mock import demo_enabled, MockSerp, MockFirecrawl
    if demo_enabled():
        serpapi = MockSerp(brand_name=brand_name, brand_domain=brand_domain)
        firecrawl = MockFirecrawl(brand_name=brand_name, industry=industry)
    else:
        serpapi = SerpAPIProvider(api_key=serpapi_key)
        firecrawl = FirecrawlProvider(api_key=firecrawl_key)

    # ── 1. Brand SERP Ownership (0–35) ──────────────────
    brand_serp = serpapi.search(brand_name, num=10)
    organic = brand_serp.get("organic_results", [])

    rank1_owned = False
    serp_ownership = 0

    if organic:
        # Check top 3 for brand domain ownership (not just #1)
        for i, result in enumerate(organic[:3]):
            link = result.get("link", "")
            if brand_domain in link:
                if i == 0:
                    serp_ownership += 22  # #1 position
                    rank1_owned = True
                elif i == 1:
                    serp_ownership += 8   # #2 position
                else:
                    serp_ownership += 5   # #3 position

        # Bonus: count additional top-10 brand appearances
        owned_count = sum(1 for r in organic if brand_domain in r.get("link", ""))
        if owned_count >= 3:
            serp_ownership += 5  # dominates SERP
        elif owned_count >= 2:
            serp_ownership += 3  # strong presence

    # Featured snippet
    featured = brand_serp.get("answer_box") or {}
    if featured:
        serp_ownership += 8

    # Knowledge panel (major brands almost always have one)
    knowledge = brand_serp.get("knowledge_graph") or {}
    if knowledge:
        serp_ownership += 5

    serp_ownership = min(serp_ownership, 35)

    # ── 2. Keyword Ranking (0–40) ───────────────────────
    keyword_score = 0
    keyword_details = []

    try:
        homepage_md, _ = firecrawl.extract_text(website_url)
        keywords = _extract_keywords_from_markdown(homepage_md, brand_name, industry)
    except Exception:
        keywords = [brand_name, f"{brand_name} {industry}".strip()]

    for kw in keywords:
        if not kw or len(kw) < 2:
            continue
        try:
            kw_data = serpapi.search(kw, num=10)
            kw_organic = kw_data.get("organic_results", [])
            position_found = None
            for i, r in enumerate(kw_organic, 1):
                if brand_domain in r.get("link", ""):
                    position_found = i
                    break
            pts = _score_position(position_found) if position_found else 0
            keyword_score += pts
            keyword_details.append({
                "keyword": kw,
                "brand_position": position_found,
                "points": pts,
            })
        except Exception:
            keyword_details.append({"keyword": kw, "brand_position": None, "points": 0})

    # Scale to 45 max: if 4 keywords × 12pts each = max 48 → cap at 45
    keyword_score = min(keyword_score, 45)

    # ── 3. SERP Feature Presence (0–25) ──────────────────
    serp_features = 0

    paa = brand_serp.get("related_questions", [])
    if len(paa) >= 5:
        serp_features += 14
    elif len(paa) >= 3:
        serp_features += 10
    elif len(paa) >= 1:
        serp_features += 5

    related = brand_serp.get("related_searches", [])
    if len(related) >= 5:
        serp_features += 11
    elif len(related) >= 3:
        serp_features += 7
    elif len(related) >= 1:
        serp_features += 3

    serp_features = min(serp_features, 25)

    # ── 4. Negative Content Check (0–15, inverted) ───────
    negative_score = 15  # start at full, deduct per negative hit

    try:
        neg_data = serpapi.search(f"{brand_name} reviews complaints", num=5)
        neg_organic = neg_data.get("organic_results", [])
        negative_triggers = [
            "scam", "complaint", "lawsuit", "controversy", "boycott",
            "worst", "terrible", "avoid", "fraud", "rip off",
        ]
        deductions = 0
        for r in neg_organic:
            text = (r.get("title", "") + " " + r.get("snippet", "")).lower()
            if any(t in text for t in negative_triggers):
                deductions += 2  # reduced from 3 — less harsh
        negative_score = max(0, 15 - deductions)
    except Exception:
        negative_score = 12  # can't check = slight penalty for uncertainty

    # ── Assemble ─────────────────────────────────────────
    total = serp_ownership + keyword_score + serp_features + negative_score
    total = min(total, 100)

    # Label — calibrated against benchmark brands
    if total >= 85:
        label = "Excellent"
    elif total >= 70:
        label = "Strong"
    elif total >= 50:
        label = "Average"
    elif total >= 30:
        label = "Weak"
    else:
        label = "Critical"

    return {
        "score": total,
        "label": label,
        "breakdown": {
            "serp_ownership": serp_ownership,
            "keyword_ranking": keyword_score,
            "serp_features": serp_features,
            "negative_content": negative_score,
        },
        "details": {
            "brand_domain": brand_domain,
            "rank1_owned": rank1_owned,
            "featured_snippet": bool(featured),
            "knowledge_panel": bool(knowledge),
            "keywords_tested": keyword_details,
            "paa_count": len(paa),
            "related_searches_count": len(related),
        },
    }
