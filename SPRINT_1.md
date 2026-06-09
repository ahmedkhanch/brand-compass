# Sprint 1 — Brand Compass MVP: Full Scoring Pipeline

> **Completed:** 2026-06-08
> **README version:** 3.1 (Final MVP)
> **Status:** ✅ Done
> **Next:** Sprint 2 — FastAPI Backend + PostgreSQL + Clerk Auth

---

## What Sprint 1 Delivers

A working CLI pipeline that takes a brand name + website URL and produces a comprehensive diagnostic report in under 90 seconds. All scoring engines and AI providers are built, tested, and wired together.

### Report Sections Produced

| # | Section | Provider | What It Contains |
|---|---|---|---|
| 1 | **Website Extraction** | Firecrawl | Clean markdown of homepage (title, description, body) |
| 2 | **Brand Positioning** | DeepSeek* | Archetype, value proposition, target audience, brand voice, differentiators, weaknesses |
| 3 | **SWOT Analysis** | DeepSeek* | 5 strengths, 3 weaknesses, 3 opportunities, 3 threats, executive summary |
| 4 | **Competitive Landscape** | DeepSeek* | 3 direct competitors with positioning + threat level, market position, competitive moat |
| 5 | **SEO Score (0–100)** | SerpAPI + Firecrawl | SERP ownership, keyword rankings, featured snippets, knowledge panel, negative content check |
| 6 | **GEO Score (0–100, Beta)** | DeepSeek* | AI visibility, sentiment, consistency across engines |
| 7 | **Actionable Recommendations** | DeepSeek* | Quick wins + strategic moves + priority focus |

*\*DeepSeek is temporary — Claude, Perplexity, OpenAI providers are built and ready. Swap is one config change.*

---

## APIs Tested & Status

| # | API | Provider File | Test File | Status |
|---|---|---|---|---|
| 1 | Claude (Anthropic) | `providers/claude.py` | `claude.py` | ✅ Provider ready, awaiting key |
| 2 | Perplexity | `providers/perplexity.py` | `perplexity.py` | ✅ Provider ready, awaiting key |
| 3 | OpenAI (ChatGPT) | `providers/openai.py` | — | ✅ Provider ready, awaiting key |
| 4 | DeepSeek | `providers/deepseek.py` | `deepseek.py` | ✅ Active (temporary GEO + Prompt Engine) |
| 5 | SerpAPI | `providers/serpapi.py` | `serpAPI.py` | ✅ Active (250 free calls/mo) |
| 6 | Firecrawl | `providers/firecrawl.py` | `firecrawl.py` | ✅ Active |
| 7 | Apify (Meta Ads) | `providers/apify.py` | `test_apify.py` | ✅ Validated (Growth+ tier only) |

---

## Prompt Engine (Per README §6.3)

The **Prompt Engine** is the largest new piece in Sprint 1. It takes Firecrawl output (clean markdown of the brand's homepage) and feeds it to an LLM to produce four structured analysis sections:

```
Firecrawl → website markdown
                │
                ▼
          DeepSeek (temp) / Claude (planned)
                │
    ┌───────────┼──────────────┬──────────────────┐
    ▼           ▼              ▼                  ▼
Positioning   SWOT      Competitive      Recommendations
```

**Prompts** are crafted per the README's YAML template structure and return validated JSON. They are ready to extract to YAML files when the prompt loader is built (Sprint 2).

---

## SEO Scoring (Per README §6.5)

| Component | Weight | Source |
|---|---|---|
| Brand SERP ownership | 0–30 pts | SerpAPI |
| Keyword ranking | 0–40 pts | SerpAPI + Firecrawl (keyword extraction) |
| SERP features | 0–20 pts | SerpAPI (PAA, related searches) |
| Negative content | 0–10 pts | SerpAPI (inverted) |

**Keyword extraction** uses industry-anchored keywords plus page content signals, with nav/CTA blacklisting.

---

## GEO Scoring (Per README §6.6)

3-engine architecture: Claude + Perplexity + OpenAI (ChatGPT). Currently DeepSeek is the sole active engine until primary keys arrive.

| Component | Weight | Method |
|---|---|---|
| Visibility | 0–40 pts | Per-engine probe: "What do you know about {brand}?" + industry ranking |
| Sentiment | 0–40 pts | Per-engine: "Pros and cons of {brand}?" + recommendation |
| Consistency | 0–20 pts | Cross-engine description overlap |

**Models per README §6.6:**
- Claude: `claude-sonnet-4-5` — $3/M input, $15/M output
- Perplexity: `sonar` — web-aware research
- OpenAI: `gpt-4o-mini` — ~$0.15/1M input (cheapest capable)

---

## Project Structure (After Sprint 1)

```
Brand Compass/
├── .env                              # All API keys + test brand config
├── requirements.txt                  # requests, python-dotenv, anthropic, openai
├── run_scoring.py                    # ← CLI entry point: full diagnostic
├── report_output.json                # Last run's full report (auto-generated)
├── SPRINT_1.md                       # ← This file
├── README (1).md                     # Architecture v3.1 reference
│
├── test_apify.py                     # Standalone tests (keep for debugging)
├── claude.py
├── perplexity.py
├── firecrawl.py
├── serpAPI.py                        # Mock + real modes
├── deepseek.py                       # Mock + real modes
│
├── backend/
│   └── engine/
│       ├── providers/                # Clean API wrappers (7 providers)
│       │   ├── claude.py             #   Anthropic Claude
│       │   ├── perplexity.py         #   Perplexity
│       │   ├── openai.py             #   OpenAI ChatGPT (gpt-4o-mini)
│       │   ├── deepseek.py           #   DeepSeek (temporary)
│       │   ├── serpapi.py            #   Google SERP data
│       │   ├── firecrawl.py          #   Website → clean markdown
│       │   └── apify.py              #   Meta Ads scraper
│       ├── scorers/                  # Scoring engines
│       │   ├── positioning.py        #   Prompt Engine — positioning/SWOT/competitive/recommendations
│       │   ├── seo.py                #   SEO score (0–100)
│       │   └── geo.py                #   GEO score (0–100, 3-engine)
│       └── orchestrator.py           #   Pipeline coordinator
```

### Design Principles

1. **Providers return dicts, not print** — Library code has no side effects. Test files are for printing.
2. **Every provider has `check_health()`** — quick validation before running expensive operations.
3. **Graceful degradation** — if one scorer fails, the rest still produce output. Errors are captured, not thrown.
4. **3-engine GEO ready** — Claude, Perplexity, and OpenAI providers are built. When keys arrive, they auto-activate.
5. **Prompt-as-configuration** — Analysis prompts are clean Python functions with clear JSON schemas. Ready to extract to YAML.

---

## How to Run

```powershell
# Full diagnostic (all sections, ~12-18 API calls, 60-90 seconds)
python run_scoring.py

# Skip GEO (if no LLM key)
python run_scoring.py --skip-geo

# Skip Prompt Engine (SEO + GEO only)
python run_scoring.py --skip-positioning

# Individual API tests
python serpAPI.py --real       # 3 SerpAPI calls
python deepseek.py --real      # 4 DeepSeek calls
python firecrawl.py            # 2 Firecrawl scrapes
python test_apify.py           # 5 Apify actor runs
```

---

## When Claude/Perplexity/OpenAI Keys Arrive

The swap from DeepSeek to the primary engines requires **zero code changes** in the scorers:

1. Replace `sk-...` in `.env` with real keys:
   - `ANTHROPIC_API_KEY=sk-ant-...` → actual key
   - `PERPLEXITY_API_KEY=pplx-...` → actual key
   - `OPENAI_API_KEY=sk-...` → actual key

2. The GEO scorer will auto-detect available engines and use them. The Prompt Engine stays on DeepSeek until `ANTHROPIC_API_KEY` is set, then swaps to Claude.

3. Once all 3 GEO engines are live, the score becomes a true multi-engine measurement per README §6.6.

---

## Sprint 2 — Planned: FastAPI Backend

Per README §6.2 + §15 Roadmap (Phase 1–2):

| Deliverable | Details |
|---|---|
| **FastAPI app** | `backend/app/main.py`, CORS, config, middleware |
| **PostgreSQL** | Railway managed, SQLAlchemy 2.0 async, Alembic migrations |
| **Redis + ARQ** | Task queue + brand cache (24h TTL) + rate limiting |
| **Clerk auth** | JWT verification middleware, zero custom auth code |
| **Credit system** | Deduct before queuing, Stripe-managed subscriptions |
| **API routes** | `POST /brands/analyze`, `GET /reports/{id}`, SSE streaming |
| **Wire orchestrator** | Plug existing `engine/orchestrator.py` into ARQ worker |
| **Cost tracking** | `report_costs` table per README §11 |

Estimated: 3–4 days for core backend.
