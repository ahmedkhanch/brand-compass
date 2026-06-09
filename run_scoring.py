#!/usr/bin/env python
"""
Brand Compass — CLI Diagnostic Runner (Sprint 1)
Per README v3.1: runs Firecrawl → Prompt Engine → SEO → GEO → full report.

Usage:
  python run_scoring.py                    # Full diagnostic (all engines)
  python run_scoring.py --skip-geo         # Skip GEO scoring
  python run_scoring.py --skip-positioning # Skip Prompt Engine analysis
"""

import os
import sys
import json
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Make backend/ importable when running from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from engine.orchestrator import run_full_diagnostic


def print_divider(char: str = "─", width: int = 50):
    print(char * width)


def print_positioning(pos: dict):
    if not pos:
        return
    print(f"\n{'─' * 50}")
    print("  🎯 BRAND POSITIONING")
    print(f"{'─' * 50}")
    if pos.get("error"):
        print(f"  ❌ Error: {pos['error']}")
        return
    print(f"  Archetype       : {pos.get('archetype', 'N/A')}")
    print(f"  Value Prop      : {pos.get('value_proposition', 'N/A')}")
    print(f"  Target Audience : {pos.get('target_audience', 'N/A')}")
    print(f"  Brand Voice     : {', '.join(pos.get('brand_voice', []))}")
    print(f"  Differentiators : {', '.join(pos.get('differentiators', []))}")
    positioning = pos.get("positioning", {})
    if positioning:
        print(f"  Price Axis      : {positioning.get('price_axis', 'N/A')}")
        print(f"  Appeal Axis     : {positioning.get('appeal_axis', 'N/A')}")
    weaknesses = pos.get("weaknesses", [])
    if weaknesses:
        print(f"  Weaknesses      : {', '.join(weaknesses)}")


def print_swot(swot: dict):
    if not swot:
        return
    print(f"\n{'─' * 50}")
    print("  📋 SWOT ANALYSIS")
    print(f"{'─' * 50}")
    if swot.get("error"):
        print(f"  ❌ Error: {swot['error']}")
        return
    for item in swot.get("strengths", [])[:4]:
        print(f"  ✅ S: {item}")
    for item in swot.get("weaknesses", [])[:3]:
        print(f"  ⚠  W: {item}")
    for item in swot.get("opportunities", [])[:3]:
        print(f"  💡 O: {item}")
    for item in swot.get("threats", [])[:3]:
        print(f"  🔴 T: {item}")
    summary = swot.get("executive_summary", "")
    if summary:
        print(f"\n  Summary: {summary}")


def print_competitive(comp: dict):
    if not comp:
        return
    print(f"\n{'─' * 50}")
    print("  🏆 COMPETITIVE LANDSCAPE")
    print(f"{'─' * 50}")
    if comp.get("error"):
        print(f"  ❌ Error: {comp['error']}")
        return
    print(f"  Market Position     : {comp.get('market_position', 'N/A')}")
    print(f"  Brand Differentiator: {comp.get('brand_differentiator', 'N/A')}")
    print(f"  Competitive Advantage: {comp.get('competitive_advantage', 'N/A')}")
    print(f"  Competitive Threat  : {comp.get('competitive_threat', 'N/A')}")
    competitors = comp.get("direct_competitors", [])
    if competitors:
        print(f"\n  Direct Competitors:")
        for c in competitors:
            print(f"    • {c.get('name', '?')} — {c.get('positioning', '')} [{c.get('threat_level', '?')}]")


def print_recommendations(recs: dict):
    if not recs:
        return
    print(f"\n{'─' * 50}")
    print("  💡 ACTIONABLE RECOMMENDATIONS")
    print(f"{'─' * 50}")
    if recs.get("error"):
        print(f"  ❌ Error: {recs['error']}")
        return
    print(f"  Priority: {recs.get('priority_focus', 'N/A')}")
    qw = recs.get("quick_wins", [])
    if qw:
        print(f"\n  Quick Wins:")
        for w in qw:
            print(f"    ⚡ {w.get('action', '')} [impact: {w.get('impact', '?')}, effort: {w.get('effort', '?')}]")
    sm = recs.get("strategic_moves", [])
    if sm:
        print(f"\n  Strategic Moves:")
        for m in sm:
            print(f"    🎯 {m.get('action', '')} [timeframe: {m.get('timeframe', '?')}]")
    summary = recs.get("executive_summary", "")
    if summary:
        print(f"\n  Assessment: {summary}")


def print_seo(seo: dict):
    if not seo:
        return
    print(f"\n{'─' * 50}")
    print("  📊 SEO SCORE")
    print(f"{'─' * 50}")
    if seo.get("error"):
        print(f"  ❌ Error: {seo['error']}")
        return
    bd = seo.get("breakdown", {})
    dt = seo.get("details", {})
    print(f"  Score: {seo['score']}/100 — {seo['label']}")
    print(f"\n  Breakdown:")
    print(f"    Brand SERP ownership  : {bd.get('serp_ownership', 0):>3}/30")
    print(f"    Keyword ranking       : {bd.get('keyword_ranking', 0):>3}/40")
    print(f"    SERP features         : {bd.get('serp_features', 0):>3}/20")
    print(f"    Negative content check: {bd.get('negative_content', 0):>3}/10")
    print(f"\n  Details:")
    print(f"    Domain           : {dt.get('brand_domain', 'N/A')}")
    print(f"    Ranks #1         : {'✅ YES' if dt.get('rank1_owned') else '❌ NO'}")
    print(f"    Featured snippet : {'✅ YES' if dt.get('featured_snippet') else '❌ NO'}")
    print(f"    Knowledge panel  : {'✅ YES' if dt.get('knowledge_panel') else '❌ NO'}")
    keywords = dt.get("keywords_tested", [])
    if keywords:
        print(f"\n  Keywords tested:")
        for kw in keywords:
            pos = kw.get("brand_position")
            pos_str = f"#{pos}" if pos else "not found"
            print(f"    \"{kw['keyword'][:60]}\" → {pos_str} ({kw['points']}/10 pts)")


def print_geo(geo: dict):
    if not geo:
        return
    print(f"\n{'─' * 50}")
    print("  🤖 GEO SCORE [Beta]")
    print(f"{'─' * 50}")
    if geo.get("error"):
        print(f"  ❌ Error: {geo['error']}")
        return
    bd = geo.get("breakdown", {})
    dt = geo.get("details", {})
    engines = dt.get("engines_used", [])
    unavailable = dt.get("engines_unavailable", [])
    print(f"  Engines : {', '.join(engines) if engines else 'none'}")
    if unavailable:
        print(f"  Pending : {', '.join(unavailable)} (keys not yet available)")
    print(f"  Score   : {geo['score']}/100 — {geo['label']}")
    print(f"\n  Breakdown:")
    print(f"    Visibility  : {bd.get('visibility', 0):>3}/40")
    print(f"    Sentiment   : {bd.get('sentiment', 0):>3}/40")
    print(f"    Consistency : {bd.get('consistency', 0):>3}/20")

    for eng in dt.get("engine_results", []):
        if not eng.get("available"):
            continue
        print(f"\n  [{eng['engine']}]")
        vis = eng.get("visibility", {})
        if vis.get("mentioned"):
            print(f"    Visibility: ✅ mentioned — {vis.get('description', '')[:120]}...")
        ind = eng.get("industry_ranking", {})
        if ind.get("brand_mentioned"):
            brands = ind.get("top_brands", [])
            print(f"    Industry ranking: #{ind.get('rank', '?')} — {', '.join(brands[:5])}")
        sent = eng.get("sentiment", {})
        print(f"    Sentiment: {sent.get('sentiment', '?').upper()} ({sent.get('raw_score', '?')}/10)")
        if sent.get("pros"):
            print(f"    Pros: {sent['pros'][0]}")
        if sent.get("cons"):
            print(f"    Cons: {sent['cons'][0]}")


def main():
    brand      = os.getenv("TEST_BRAND_NAME", "Nike")
    url        = os.getenv("TEST_BRAND_URL", "https://www.nike.com")
    industry   = os.getenv("TEST_BRAND_INDUSTRY", "sportswear")
    competitor = os.getenv("TEST_COMPETITOR", "Adidas")
    skip_geo   = "--skip-geo" in sys.argv
    skip_pos   = "--skip-positioning" in sys.argv

    print_divider("=")
    print("  BRAND COMPASS — Full Diagnostic (Sprint 1)")
    print(f"  Brand: {brand} | URL: {url}")
    print(f"  Industry: {industry} | Competitor: {competitor}")
    print(f"  README v3.1 — Firecrawl → Prompt Engine → SEO → GEO")
    print_divider("=")

    # ── Check keys ───────────────────────────────────────
    missing = []
    if not os.getenv("SERPAPI_KEY") or os.getenv("SERPAPI_KEY") == "...":
        missing.append("SERPAPI_KEY")
    if not os.getenv("FIRECRAWL_API_KEY") or os.getenv("FIRECRAWL_API_KEY") == "fc-...":
        missing.append("FIRECRAWL_API_KEY")
    if not skip_geo:
        dsk = os.getenv("DEEPSEEK_API_KEY", "")
        if not dsk or dsk == "sk-...":
            missing.append("DEEPSEEK_API_KEY (or use --skip-geo)")
    if missing:
        print(f"\n  ❌ Missing API keys: {', '.join(missing)}")
        print(f"  Check your .env file.\n")
        return

    include_geo = not skip_geo
    include_pos = not skip_pos

    print(f"\n  Running full diagnostic pipeline...")
    print(f"  This will make ~10-15 API calls and may take 60–90 seconds.\n")
    print(f"  Steps:")
    print(f"    1. Firecrawl → scrape {url}")
    print(f"    2. Prompt Engine → brand positioning + SWOT + competitive analysis")
    print(f"    3. SEO Engine → SerpAPI SERP data + keyword rankings")
    print(f"    4. GEO Engine → AI visibility + sentiment probes")
    print(f"    5. Recommendations → actionable next steps")
    print()

    report = run_full_diagnostic(
        brand_name=brand,
        website_url=url,
        industry=industry,
        competitor=competitor,
        include_geo=include_geo,
        include_positioning=include_pos,
    )

    # ── Print results ────────────────────────────────────
    wc = report.get("website_content", {})
    if wc and "error" not in wc:
        print(f"\n{'─' * 50}")
        print("  🌐 WEBSITE EXTRACTION (Firecrawl)")
        print(f"{'─' * 50}")
        print(f"  Title  : {wc.get('title', 'N/A')}")
        print(f"  Desc   : {wc.get('description', 'N/A')[:120]}")
        print(f"  Length : {wc.get('length_chars', 0):,} chars")

    print_positioning(report.get("positioning"))
    print_swot(report.get("swot"))
    print_competitive(report.get("competitive"))
    print_seo(report.get("seo"))
    print_geo(report.get("geo"))
    print_recommendations(report.get("recommendations"))

    # ── Overall ──────────────────────────────────────────
    print(f"\n{'═' * 50}")
    print(f"  OVERALL SCORE: {report['overall_score']}/100")
    print(f"  Completed at: {report['completed_at'][:19]}")
    print(f"{'═' * 50}\n")

    # ── Save JSON ────────────────────────────────────────
    output_path = os.path.join(os.path.dirname(__file__), "report_output.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    print(f"  📄 Full JSON report saved to: {output_path}\n")


if __name__ == "__main__":
    main()
