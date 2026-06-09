# Sprint 3 — Frontend: React Dashboard + Clerk Auth + Stripe Checkout

> **Start:** 2026-06-09
> **Sprint 1 Status:** ✅ Complete
> **Sprint 2 Status:** ✅ Complete
> **Goal:** A working React frontend that consumes the full backend — sign up, analyze brands, view reports, upgrade tiers

---

## What Sprints 1 & 2 Delivered

A complete backend with 18 API endpoints: brand analysis pipeline (Firecrawl + DeepSeek + SerpAPI), report CRUD, SSE streaming, Stripe checkout/portal/webhooks, Clerk JWT auth, tier gating, credit system, cost tracking, PostgreSQL-ready with Alembic migrations. Everything works via Swagger.

## What Sprint 3 Adds

A React (Next.js) frontend so users don't need Swagger:

| # | Page | Description |
|---|------|-------------|
| 1 | **Landing Page** | Hero, features overview, pricing table, CTA |
| 2 | **Sign Up / Sign In** | Clerk-hosted auth pages, no custom auth code |
| 3 | **Dashboard** | Report list with status badges, scores, brand names |
| 4 | **New Analysis** | Form: brand name + website + social accounts → submit |
| 5 | **Report Detail** | Full report view: positioning, SWOT, competitive, SEO, GEO, recommendations |
| 6 | **Pricing Page** | Tier comparison + Stripe checkout buttons |
| 7 | **Settings / Billing** | Current tier, credits remaining, upgrade/downgrade |

---

## Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | **Next.js 14** (App Router) | Server components, API routes, SSR |
| Auth | **Clerk** | Zero custom auth code, pre-built UI components |
| Styling | **Tailwind CSS** | Fast, no CSS files, great with React |
| Payments | **Stripe.js** | `@stripe/stripe-js` for checkout redirects |
| SSE | **EventSource** | Native browser API for live report progress |
| HTTP | **fetch / SWR** | Data fetching with cache |

---

## Page-by-Page Design

### 1. Landing Page (`/`)

```
┌─────────────────────────────────────────────┐
│  Brand Compass                    [Sign In] │
│                                             │
│  AI-Powered Brand Intelligence              │
│  Analyze any brand in 60 seconds            │
│                                             │
│  [Get Started Free]  [View Pricing]         │
│                                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │Positioning│ │ SEO/GEO  │ │Competitors│   │
│  │ Analysis  │ │ Scoring  │ │ Landscape │   │
│  └──────────┘ └──────────┘ └──────────┘    │
└─────────────────────────────────────────────┘
```

### 2. Dashboard (`/dashboard`)

```
┌─────────────────────────────────────────────┐
│  Brand Compass      [Credits: 24] [Profile] │
│                                             │
│  [+ New Analysis]                           │
│                                             │
│  Reports                                    │
│  ┌──────────────────────────────────────┐   │
│  │ Nike       SEO: 60  GEO: 45  42 min  │   │
│  │ sportswear  Overall: 52  Complete    │   │
│  ├──────────────────────────────────────┤   │
│  │ Spotify    SEO: 40  GEO: 43  3h ago  │   │
│  │ streaming   Overall: 42  Complete    │   │
│  ├──────────────────────────────────────┤   │
│  │ Apple      ---       ---      queued │   │
│  │ tech        Running analysis...      │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

### 3. New Analysis (`/analyze`)

```
┌─────────────────────────────────────────────┐
│  New Brand Analysis                         │
│                                             │
│  Brand Name *     [___________________]     │
│  Website URL     [___________________]     │
│  Industry         [___________________]     │
│  Competitor       [___________________]     │
│  Social Accounts  [___________________]     │
│                                             │
│  [Start Analysis]                           │
│                                             │
│  ── Live Progress ──                        │
│  ████████████░░░░░░░░  queued               │
│  ████████████████████  running (45s)        │
│  ████████████████████  complete!            │
└─────────────────────────────────────────────┘
```

### 4. Report Detail (`/reports/{id}`)

```
┌─────────────────────────────────────────────┐
│  ← Back to Dashboard                        │
│                                             │
│  Nike Report — Overall Score: 52/100        │
│                                             │
│  ┌─ Positioning ──────────────────────────┐ │
│  │ Archetype: Hero                         │ │
│  │ Value Prop: "Premium athletic wear..."  │ │
│  │ Target: Athletes 18-35                  │ │
│  └────────────────────────────────────────┘ │
│                                             │
│  ┌─ SWOT ─────────────────────────────────┐ │
│  │ S: Global brand, Innovation, DTC...     │ │
│  │ W: Price premium, Labor concerns...     │ │
│  └────────────────────────────────────────┘ │
│                                             │
│  ┌─ SEO Score: 60/100 ─────────────────────┐│
│  │ SERP Ownership: 27/30                   │ │
│  │ Keyword Ranking: 28/40                  │ │
│  └────────────────────────────────────────┘ │
│                                             │
│  ┌─ GEO Score: 45/100 ─────────────────────┐│
│  │ Visibility: 18/40                        │ │
│  │ Sentiment: 20/40                         │ │
│  └────────────────────────────────────────┘ │
│                                             │
│  ┌─ Recommendations ───────────────────────┐│
│  │ Quick Wins: 3 items                     │ │
│  │ Strategic Moves: 2 items                │ │
│  └────────────────────────────────────────┘ │
│                                             │
│  ┌─ Meta Ads (Radar+) ─────────────────────┐│
│  │ 🔒 Upgrade to Radar to unlock           │ │
│  │ [Upgrade Now — $199/mo]                 │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### 5. Pricing (`/pricing`)

```
┌─────────────────────────────────────────────┐
│  Plans                                      │
│                                             │
│  ┌─ Boussole ──┐ ┌─ Radar ──┐ ┌─ Stratège ┐│
│  │ $99/mo       │ │ $199/mo   │ │ $499/mo   ││
│  │ 25 reports   │ │ 100 rep.  │ │ 500 rep.  ││
│  │ SEO + GEO    │ │ + Meta Ads│ │ + Alerts  ││
│  │              │ │ + History │ │ + API     ││
│  │ [Current]    │ │ [Upgrade] │ │ [Upgrade] ││
│  └─────────────┘ └──────────┘ └──────────┘ │
└─────────────────────────────────────────────┘
```

---

## How to Build (Order)

| # | Step | Files Created | Effort |
|---|------|--------------|--------|
| 1 | **Scaffold Next.js + install deps** | `package.json`, `tailwind.config.ts` | 15 min |
| 2 | **Clerk auth wrapper** | `middleware.ts`, `app/layout.tsx` | 15 min |
| 3 | **API client layer** | `lib/api.ts` | 20 min |
| 4 | **Landing page** | `app/page.tsx` | 30 min |
| 5 | **Dashboard page** | `app/dashboard/page.tsx` | 45 min |
| 6 | **New Analysis form + SSE** | `app/analyze/page.tsx` | 45 min |
| 7 | **Report detail page** | `app/reports/[id]/page.tsx` | 45 min |
| 8 | **Pricing page + Stripe checkout** | `app/pricing/page.tsx` | 30 min |
| 9 | **Settings/Billing page** | `app/settings/page.tsx` | 20 min |
| **Total** | | | **~4.5 hours** |

---

## API Endpoints Used

| Frontend Action | Method | Endpoint |
|----------------|--------|----------|
| Submit brand for analysis | `POST` | `/api/v1/brands/analyze` |
| Watch live progress | `GET` (SSE) | `/sse/reports/{id}` |
| List all reports | `GET` | `/api/v1/reports` |
| View report detail | `GET` | `/api/v1/reports/{id}` |
| Delete report | `DELETE` | `/api/v1/reports/{id}` |
| Get user profile + tier | `GET` | `/api/v1/auth/me` |
| Get subscription | `GET` | `/api/v1/subscription` |
| Create Stripe checkout | `POST` | `/api/v1/checkout?tier=radar` |
| Stripe billing portal | `POST` | `/api/v1/checkout/portal` |
| Get credits balance | `GET` | `/api/v1/credits` |
| Meta Ads (Radar+) | `GET` | `/api/v1/reports/{id}/meta-ads` |

---

## Key Design Decisions

1. **No custom auth forms** — Clerk's `<SignIn>` and `<SignUp>` components handle everything
2. **SSE for live progress** — `EventSource` in the browser connects to `/sse/reports/{id}`, updates the progress bar in real-time
3. **Blurred premium content** — Meta Ads section shows a blur overlay with upgrade CTA for Boussole users (per product brief §workflow)
4. **Stripe redirect flow** — Checkout redirects to Stripe-hosted page, success URL brings user back to `/dashboard?checkout=success`
5. **Backend unchanged** — Zero backend changes needed; all 18 endpoints already return exactly what the frontend needs

---

## Acceptance Criteria

- [ ] User lands on `/`, clicks "Get Started" → Clerk sign-up modal
- [ ] After sign-up, redirected to `/dashboard` (empty state)
- [ ] User clicks "New Analysis", fills form, submits
- [ ] SSE progress bar shows `queued → running → complete`
- [ ] Report detail page renders all 6 sections
- [ ] Meta Ads section shows blur overlay for Boussole tier
- [ ] Pricing page shows 3 tiers, current tier highlighted
- [ ] Clicking "Upgrade to Radar" → Stripe checkout → pay → webhook upgrades tier
- [ ] Report detail now shows Meta Ads section (no blur)
- [ ] Sign out works, different users see different reports
