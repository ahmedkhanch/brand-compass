# Brand Compass — Launch Guide

## What You Need

- Docker Desktop installed ([download](https://www.docker.com/products/docker-desktop))
- API keys for the providers below (free tiers work for testing)

## Step 1: Get API Keys

Sign up for these free accounts. Takes ~15 minutes total.

| Provider | Sign Up | Free Tier | What It Powers |
|----------|---------|-----------|----------------|
| DeepSeek | [platform.deepseek.com](https://platform.deepseek.com) | $2 free credit | Brand analysis, SWOT, recommendations |
| SerpAPI | [serpapi.com](https://serpapi.com) | 100 searches/month | SEO scoring |
| Firecrawl | [firecrawl.dev](https://firecrawl.dev) | 500 scrapes/month | Website content extraction |
| Clerk | [clerk.com](https://clerk.com) | 10,000 users free | Authentication (sign-up, login) |
| Stripe | [dashboard.stripe.com](https://dashboard.stripe.com) | Pay-per-transaction | Payments (test mode is free) |
| Apify | [apify.com](https://apify.com) | Free tier | Meta Ads scraping (optional) |

## Step 2: Configure Environment

Copy the example file and fill in your keys:

```powershell
cp .env.example .env
```

Then open `.env` in any text editor and replace the placeholders:

```ini
# Required — the app won't work without these
DEEPSEEK_API_KEY=sk-abc123...
SERPAPI_KEY=abc123...
FIRECRAWL_API_KEY=fc-abc123...

# Required for user accounts
CLERK_SECRET_KEY=sk_test_abc123...
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_abc123...
CLERK_JWT_ISSUER=https://your-app.clerk.accounts.dev

# Required for payments (test mode)
STRIPE_SECRET_KEY=sk_test_abc123...
STRIPE_WEBHOOK_SECRET=whsec_abc123...
STRIPE_PUBLISHABLE_KEY=pk_test_abc123...

# Stripe product IDs — create these in Stripe Dashboard or leave as-is for mock mode
STRIPE_PRICE_BOUSSOLE=price_xxx
STRIPE_PRICE_RADAR=price_xxx
STRIPE_PRICE_STRATEGE=price_xxx
```

## Step 3: Launch

```powershell
docker compose up --build
```

First build takes 3-5 minutes. After that it's instant.

## Step 4: Open the App

| Service | URL |
|---------|-----|
| Frontend | [http://localhost:3000](http://localhost:3000) |
| Backend API docs | [http://localhost:8000/docs](http://localhost:8000/docs) |
| Health check | [http://localhost:8000/health](http://localhost:8000/health) |

## How to Use

1. Open `http://localhost:3000`
2. Click **Get Started** — sign up with any email (Clerk test mode, no verification)
3. Click **+ New Analysis**
4. Enter a brand name and website URL
5. Watch the SSE progress bar — report completes in 40-90 seconds
6. Click the report to see: positioning, SWOT, competitive landscape, SEO score, GEO score, recommendations
7. Meta Ads section unlocks after upgrading to Radar tier

## Tier Testing

In dev mode, upgrade to any tier instantly:

```powershell
curl -X POST "http://localhost:8000/api/v1/subscription/upgrade?tier=radar"
```

Tiers: `boussole` (free) → `radar` ($199) → `stratege` ($499)

## Stopping

```powershell
docker compose down        # Stop containers, keep data
docker compose down -v     # Stop and delete all data (fresh start)
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "DEEPSEEK_API_KEY not set" | Check `.env` file has real keys (not `sk-...`) |
| "Failed to fetch" in browser | Backend hasn't started yet — wait 10 seconds |
| Reports stuck at "queued" | Backend is healthy? Check `http://localhost:8000/health` |
| Meta Ads returns error | Apify free tier doesn't include Facebook Ads actor |
| Stripe checkout returns mock URL | STRIPE_PRICE_RADAR is still `price_xxx` — create real products |

## Project Structure

```
Brand Compass/
├── docker-compose.yml     ← One command to run everything
├── .env                    ← Your API keys (not committed to git)
├── .env.example            ← Template for new setups
├── LAUNCH.md               ← This file
├── backend/                ← Python FastAPI + SQLAlchemy + scoring engine
├── frontend/               ← Next.js 16 + Clerk + Tailwind
├── SPRINT_1.md             ← Scoring pipeline documentation
├── SPRINT_2.md             ← Backend: auth, payments, database
└── SPRINT_3.md             ← Frontend: React dashboard & report views
```
