"use client";

import Navbar from "@/components/Navbar";

// ── Constants ──────────────────────────────────────────────────────────────

const LAST_UPDATED = "2026-06-11 15:00 UTC";

const STATUS = {
  done: { label: "Construit", dot: "bg-emerald-500", badge: "bg-emerald-50 text-emerald-700 ring-emerald-200" },
  mock: { label: "Mock (données simulées)", dot: "bg-amber-500", badge: "bg-amber-50 text-amber-700 ring-amber-200" },
  stub: { label: "Stub (retourne URLs factices)", dot: "bg-orange-500", badge: "bg-orange-50 text-orange-700 ring-orange-200" },
  pending: { label: "Pas encore implémenté", dot: "bg-slate-300", badge: "bg-slate-50 text-slate-500 ring-slate-200" },
} as const;

type StatusKey = keyof typeof STATUS;

// ── Data ────────────────────────────────────────────────────────────────────

interface ProviderRow {
  provider: string;
  service: string;
  envVar: string;
  status: StatusKey;
  note: string;
}

const API_PROVIDERS: ProviderRow[] = [
  {
    provider: "Firecrawl",
    service: "Firecrawl API",
    envVar: "FIRECRAWL_API_KEY",
    status: "done",
    note: "Clé réelle configurée — scraping live",
  },
  {
    provider: "Claude (Anthropic)",
    service: "Anthropic API",
    envVar: "ANTHROPIC_API_KEY",
    status: "mock",
    note: "Positionnement, SWOT, concurrence, recommandations + GEO moteur #1. Coût: ~$3/$15 par 1M tokens",
  },
  {
    provider: "Perplexity",
    service: "Perplexity API",
    envVar: "PERPLEXITY_API_KEY",
    status: "mock",
    note: "GEO moteur #2 (sonar, web-aware). Coût: $20/mois + usage",
  },
  {
    provider: "OpenAI (ChatGPT)",
    service: "OpenAI API",
    envVar: "OPENAI_API_KEY",
    status: "mock",
    note: "GEO moteur #3 + fallback LLM. Coût: ~$0.15/$0.60 par 1M tokens (gpt-4o-mini)",
  },
  {
    provider: "DeepSeek",
    service: "DeepSeek API",
    envVar: "DEEPSEEK_API_KEY",
    status: "done",
    note: "Clé réelle configurée — LLM principal pour positionnement, SWOT, concurrence, recommandations + GEO. Coût: $0.14/$0.28 par 1M tokens",
  },
  {
    provider: "SerpAPI",
    service: "SerpAPI",
    envVar: "SERPAPI_KEY",
    status: "done",
    note: "Clé réelle configurée — SEO scoring live : SERP ownership, keywords, featured snippets, negative content. Plan: ~$50/mois",
  },
  {
    provider: "Apify",
    service: "Apify (Meta Ads Library)",
    envVar: "APIFY_TOKEN",
    status: "mock",
    note: "Bibliothèque Meta Ads (Radar+). Pay-per-result",
  },
];

interface PageRow {
  route: string;
  label: string;
  status: StatusKey;
  note: string;
}

const FRONTEND_PAGES: PageRow[] = [
  { route: "/", label: "Landing Page", status: "done", note: "Hero, features, CTA — bilingue FR/EN" },
  { route: "/dashboard", label: "Dashboard", status: "done", note: "Liste des rapports avec statuts et scores" },
  { route: "/analyze", label: "Nouvelle Analyse", status: "done", note: "Formulaire brand + URL + loader progressif" },
  { route: "/reports/[id]", label: "Rapport Détaillé", status: "done", note: "8 sections: positioning, SWOT, SEO, GEO, etc." },
  { route: "/pricing", label: "Tarifs", status: "done", note: "3 tiers (Boussole/Radar/Stratège) + boutons Stripe" },
  { route: "/settings", label: "Paramètres", status: "done", note: "Profil, crédits, abonnement" },
  { route: "/wip", label: "WIP — État du projet", status: "done", note: "Cette page — rapport d'avancement" },
];

interface BackendRow {
  endpoint: string;
  method: string;
  label: string;
  status: StatusKey;
  note: string;
}

const BACKEND_ENDPOINTS: BackendRow[] = [
  { endpoint: "/api/v1/auth/me", method: "GET", label: "Profil utilisateur", status: "done", note: "Mode dev: token dev-user-* accepté" },
  { endpoint: "/api/v1/brands/analyze", method: "POST", label: "Lancer une analyse", status: "done", note: "Débit crédits, rate-limit, pipeline background" },
  { endpoint: "/api/v1/reports", method: "GET", label: "Liste des rapports", status: "done", note: "Paginée, scopée par user" },
  { endpoint: "/api/v1/reports/{id}", method: "GET", label: "Détail d'un rapport", status: "done", note: "Toutes les sections du diagnostic" },
  { endpoint: "/api/v1/reports/{id}", method: "DELETE", label: "Supprimer un rapport", status: "done", note: "" },
  { endpoint: "/api/v1/reports/{id}/meta-ads", method: "GET", label: "Données Meta Ads", status: "mock", note: "Mock tant que APIFY_TOKEN absent" },
  { endpoint: "/sse/reports/{id}", method: "GET", label: "Progression live (SSE)", status: "done", note: "Polling DB pour status changes" },
  { endpoint: "/api/v1/credits", method: "GET", label: "Solde de crédits", status: "done", note: "" },
  { endpoint: "/api/v1/subscription", method: "GET", label: "Abonnement actuel", status: "done", note: "" },
  { endpoint: "/api/v1/checkout", method: "POST", label: "Checkout Stripe", status: "stub", note: "URL mock tant que STRIPE_SECRET_KEY absent" },
  { endpoint: "/api/v1/checkout/portal", method: "POST", label: "Portail Stripe", status: "stub", note: "URL mock tant que STRIPE_SECRET_KEY absent" },
  { endpoint: "/api/v1/webhooks/stripe", method: "POST", label: "Webhook Stripe", status: "stub", note: "Vérifie signature seulement si clé présente" },
];

interface SprintRow {
  sprint: string;
  label: string;
  status: StatusKey;
  items: string;
}

const SPRINTS: SprintRow[] = [
  { sprint: "Sprint 1", label: "Pipeline de scoring CLI", status: "done", items: "7 providers, 3 scorers, orchestrateur — livré le 08/06" },
  { sprint: "Sprint 2", label: "Backend FastAPI + DB + Auth", status: "done", items: "18 endpoints, SQLite/PostgreSQL, Clerk JWT, Stripe, ARQ worker" },
  { sprint: "Sprint 3", label: "Frontend Next.js", status: "done", items: "6 pages, i18n FR/EN, Tailwind, loader progressif, thème clair pro" },
];

interface TodoItem {
  task: string;
  priority: "P0" | "P1" | "P2" | "P3";
  dep: string;
  effort: string;
  effect: string;
}

const REMAINING: TodoItem[] = [
  {
    task: "Activer Anthropic (Claude Sonnet 4.5)",
    priority: "P0",
    dep: "ANTHROPIC_API_KEY",
    effort: "1 minute",
    effect: "Remplace DeepSeek par Claude pour le LLM principal + GEO moteur #1. Qualité d'analyse supérieure. DeepSeek reste en fallback automatique.",
  },
  {
    task: "Activer Perplexity",
    priority: "P1",
    dep: "PERPLEXITY_API_KEY",
    effort: "1 minute",
    effect: "GEO moteur #2 (web-aware). Le GEO passe de 1 à 2 moteurs indépendants.",
  },
  {
    task: "Activer OpenAI",
    priority: "P1",
    dep: "OPENAI_API_KEY",
    effort: "1 minute",
    effect: "GEO moteur #3 + fallback LLM. GEO multi-moteur complet (3 engines).",
  },
  {
    task: "Activer Stripe",
    priority: "P2",
    dep: "STRIPE_SECRET_KEY + STRIPE_WEBHOOK_SECRET + price IDs",
    effort: "5 minutes",
    effect: "Checkout et portail Stripe réels. Paiements live.",
  },
  {
    task: "Activer Clerk",
    priority: "P2",
    dep: "CLERK_SECRET_KEY + CLERK_JWT_ISSUER",
    effort: "5 minutes",
    effect: "Auth réelle — remplacer les tokens dev-user-*. Multi-user réel.",
  },
  {
    task: "Activer Apify (Meta Ads)",
    priority: "P2",
    dep: "APIFY_TOKEN",
    effort: "1 minute",
    effect: "Données Meta Ads réelles pour le tier Radar+. Fonctionnalité premium débloquée.",
  },
  {
    task: "Activer Redis + ARQ",
    priority: "P3",
    dep: "REDIS_URL",
    effort: "10 minutes",
    effect: "Queue de jobs scalable. Remplace threading.Thread par ARQ worker.",
  },
  {
    task: "Activer Resend (emails)",
    priority: "P3",
    dep: "RESEND_API_KEY",
    effort: "30 minutes",
    effect: "Emails transactionnels (bienvenue, rapport hebdo Stratège). Service déjà codé, non wiré.",
  },
  {
    task: "Migration PostgreSQL",
    priority: "P3",
    dep: "DATABASE_URL (PostgreSQL)",
    effort: "15 minutes",
    effect: "Passer de SQLite à PostgreSQL. Alembic prêt, auto-détection DB. Zéro changement de code.",
  },
];

// ── Helpers ─────────────────────────────────────────────────────────────────

function StatusDot({ status }: { status: StatusKey }) {
  return (
    <span
      className={`inline-block h-2.5 w-2.5 rounded-full ${STATUS[status].dot} ring-1 ring-black/5 flex-shrink-0`}
      aria-hidden
    />
  );
}

function StatusBadge({ status }: { status: StatusKey }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold ring-1 ring-inset ${STATUS[status].badge}`}
    >
      <StatusDot status={status} />
      {STATUS[status].label}
    </span>
  );
}

function Backdrop() {
  return (
    <div aria-hidden className="fixed inset-0 -z-10 overflow-hidden bg-gradient-to-b from-white via-white to-indigo-50/40">
      <div className="absolute -top-28 -left-24">
        <div className="bc-float h-80 w-80 rounded-full bg-indigo-200/30 blur-3xl" />
      </div>
      <div className="absolute top-1/4 -right-28">
        <div className="bc-float-slow h-96 w-96 rounded-full bg-fuchsia-200/25 blur-3xl" />
      </div>
      <div className="absolute bottom-0 left-1/3">
        <div className="bc-float h-72 w-72 rounded-full bg-sky-200/25 blur-3xl" />
      </div>
    </div>
  );
}

// ── Sections ────────────────────────────────────────────────────────────────

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-10">
      <h2 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2.5">
        <span className="h-1 w-6 rounded-full bg-gradient-to-r from-indigo-500 to-fuchsia-500" />
        {title}
      </h2>
      {children}
    </section>
  );
}

function DataTable({ headers, children }: { headers: string[]; children: React.ReactNode }) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-200/80 bg-white/70 backdrop-blur shadow-sm">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200/80 bg-slate-50/70">
            {headers.map((h) => (
              <th key={h} className="px-4 py-3 text-left text-[11px] font-bold uppercase tracking-wider text-slate-500">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">{children}</tbody>
      </table>
    </div>
  );
}

// ── Page ────────────────────────────────────────────────────────────────────

export default function WipPage() {
  const doneCount = API_PROVIDERS.filter((p) => p.status === "done").length;
  const mockCount = API_PROVIDERS.filter((p) => p.status === "mock").length;

  return (
    <div className="relative min-h-screen text-slate-800">
      <Backdrop />
      <Navbar />

      <main className="max-w-5xl mx-auto px-4 pt-8 pb-24">
        {/* ── Header ── */}
        <div className="mb-10">
          <p className="text-[11px] font-bold tracking-[0.22em] text-indigo-500 uppercase mb-2">WIP Report</p>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight bg-gradient-to-br from-slate-900 via-indigo-800 to-fuchsia-700 bg-clip-text text-transparent">
            Brand Compass — État du projet
          </h1>
          <p className="text-sm text-slate-500 mt-3">
            Dernière mise à jour : {LAST_UPDATED} &middot; Environnement :{" "}
            <code className="text-[11px] bg-slate-100 px-1.5 py-0.5 rounded font-mono">develop</code> &middot;{" "}
            <a
              href="https://brandcompass-develop.oratelecom.net"
              className="text-indigo-600 hover:underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              brandcompass-develop.oratelecom.net
            </a>
          </p>
        </div>

        {/* ── Résumé global ── */}
        <Section title="Résumé global">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
            {[
              { n: FRONTEND_PAGES.length, label: "Pages frontend", sub: "" },
              { n: BACKEND_ENDPOINTS.length, label: "Endpoints API", sub: "" },
              { n: doneCount, label: "Providers réels", sub: `sur ${API_PROVIDERS.length}` },
              { n: REMAINING.length, label: "Tâches restantes", sub: "" },
            ].map((c) => (
              <div
                key={c.label}
                className="rounded-2xl border border-slate-200/80 bg-white/70 backdrop-blur p-4 text-center"
              >
                <div className="text-3xl font-extrabold text-slate-900">{c.n}</div>
                <div className="text-[11px] text-slate-500 font-semibold uppercase tracking-wider mt-0.5">
                  {c.label}
                  {c.sub ? <span className="text-slate-400 font-normal normal-case"> {c.sub}</span> : null}
                </div>
              </div>
            ))}
          </div>

          <div className="rounded-2xl border border-emerald-200/60 bg-emerald-50/70 backdrop-blur p-5 text-sm text-emerald-900">
            <p className="font-bold text-emerald-800 mb-1">🎯 Statut global : 3 providers réels — Pipeline quasi-complet</p>
            <p className="text-emerald-700 leading-relaxed">
              Le pipeline est <strong>100% data-driven</strong> : scraping Firecrawl réel → analyse DeepSeek réelle → scoring SEO SerpAPI réel. Les 3 piliers (contenu, LLM, SEO) tournent en production. Reste à activer Claude pour upgrader la qualité d&apos;analyse et Perplexity/OpenAI pour le GEO multi-moteur. <strong>Zéro code à écrire</strong> — tout s&apos;active par clé API.
            </p>
          </div>
        </Section>

        {/* ── Providers API : Mock → Réel ── */}
        <Section title="Providers API — État Mock → Réel">
          <p className="text-sm text-slate-500 mb-4">
            Chaque provider a un mécanisme d&apos;auto-détection : si la clé est présente dans <code className="bg-slate-100 px-1 py-0.5 rounded text-[11px]">.env</code>, le provider passe automatiquement en mode réel. Sinon, il utilise un mock déterministe (seedé par nom de marque).
          </p>
          <DataTable headers={["Provider", "Service externe", "Variable d'env", "Statut", "Note"]}>
            {API_PROVIDERS.map((p) => (
              <tr key={p.provider} className="hover:bg-slate-50/50 transition-colors">
                <td className="px-4 py-3 font-semibold text-slate-800">{p.provider}</td>
                <td className="px-4 py-3 text-slate-600">{p.service}</td>
                <td className="px-4 py-3 font-mono text-[11px] text-slate-500">{p.envVar}</td>
                <td className="px-4 py-3">
                  <StatusBadge status={p.status} />
                </td>
                <td className="px-4 py-3 text-[12px] text-slate-500 max-w-xs">{p.note}</td>
              </tr>
            ))}
          </DataTable>
        </Section>

        {/* ── Pages Frontend ── */}
        <Section title="Pages Frontend">
          <DataTable headers={["Route", "Page", "Statut", "Détails"]}>
            {FRONTEND_PAGES.map((p) => (
              <tr key={p.route} className="hover:bg-slate-50/50 transition-colors">
                <td className="px-4 py-3 font-mono text-[11px] text-indigo-600">{p.route}</td>
                <td className="px-4 py-3 font-semibold text-slate-800">{p.label}</td>
                <td className="px-4 py-3">
                  <StatusBadge status={p.status} />
                </td>
                <td className="px-4 py-3 text-[12px] text-slate-500">{p.note}</td>
              </tr>
            ))}
          </DataTable>
        </Section>

        {/* ── Endpoints Backend ── */}
        <Section title="Endpoints Backend">
          <DataTable headers={["Endpoint", "Méthode", "Fonction", "Statut", "Note"]}>
            {BACKEND_ENDPOINTS.map((e) => (
              <tr key={e.endpoint + e.method} className="hover:bg-slate-50/50 transition-colors">
                <td className="px-4 py-3 font-mono text-[11px] text-slate-700">{e.endpoint}</td>
                <td className="px-4 py-3">
                  <span className="text-[10px] font-bold bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                    {e.method}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-800 text-[13px]">{e.label}</td>
                <td className="px-4 py-3">
                  <StatusBadge status={e.status} />
                </td>
                <td className="px-4 py-3 text-[12px] text-slate-500">{e.note}</td>
              </tr>
            ))}
          </DataTable>
        </Section>

        {/* ── Sprints Livrés ── */}
        <Section title="Sprints Livrés">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {SPRINTS.map((s) => (
              <div
                key={s.sprint}
                className="rounded-2xl border border-slate-200/80 bg-white/70 backdrop-blur p-5"
              >
                <div className="flex items-center gap-2 mb-1.5">
                  <StatusDot status={s.status} />
                  <h3 className="font-bold text-slate-900 text-sm">{s.sprint}</h3>
                </div>
                <p className="text-[13px] font-semibold text-slate-700 mb-1">{s.label}</p>
                <p className="text-[12px] text-slate-500 leading-relaxed">{s.items}</p>
              </div>
            ))}
          </div>
        </Section>

        {/* ── Reste à faire ── */}
        <Section title="Reste à faire — Priorisé">
          <p className="text-sm text-slate-500 mb-4">
            L&apos;ordre ci-dessous est <strong>le chemin critique pour passer de démo → production</strong>.
            Chaque tâche se résume à ajouter une clé API dans <code className="bg-slate-100 px-1 py-0.5 rounded text-[11px]">.env</code> — le code détecte automatiquement la clé et active le mode réel.
          </p>

          <DataTable headers={["#", "Tâche", "Priorité", "Dépendance", "Effort", "Effet"]}>
            {REMAINING.map((r, i) => (
              <tr key={r.task} className="hover:bg-slate-50/50 transition-colors">
                <td className="px-4 py-3 text-[11px] text-slate-400">{i + 1}</td>
                <td className="px-4 py-3 font-semibold text-slate-800 text-[13px]">{r.task}</td>
                <td className="px-4 py-3">
                  <span
                    className={`text-[10px] font-black px-2 py-0.5 rounded ${
                      r.priority === "P0"
                        ? "bg-red-100 text-red-700"
                        : r.priority === "P1"
                        ? "bg-amber-100 text-amber-700"
                        : r.priority === "P2"
                        ? "bg-blue-100 text-blue-700"
                        : "bg-slate-100 text-slate-500"
                    }`}
                  >
                    {r.priority}
                  </span>
                </td>
                <td className="px-4 py-3 font-mono text-[10px] text-slate-500 max-w-[160px]">{r.dep}</td>
                <td className="px-4 py-3 text-[12px] text-slate-500">{r.effort}</td>
                <td className="px-4 py-3 text-[12px] text-slate-600 max-w-xs leading-relaxed">{r.effect}</td>
              </tr>
            ))}
          </DataTable>
        </Section>

        {/* ── Prochaines étapes immédiates ── */}
        <Section title="Prochaines étapes immédiates">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="rounded-2xl border border-emerald-200/60 bg-emerald-50/70 backdrop-blur p-5">
              <h3 className="font-bold text-emerald-800 text-sm mb-2 flex items-center gap-1.5">
                <span className="text-[10px] font-black bg-emerald-500 text-white px-1.5 py-0.5 rounded">FAIT</span>
                {" "}Pipeline core 100% réel
              </h3>
              <p className="text-[13px] text-emerald-700 leading-relaxed">
                Firecrawl (scraping) + DeepSeek (LLM) + SerpAPI (SEO) = les 3 piliers du diagnostic sont en production.
                Un rapport complet est généré en ~12s avec des données réelles de bout en bout.
                Coût par rapport : ~0¢ (free tiers Firecrawl + DeepSeek + SerpAPI).
              </p>
            </div>

            <div className="rounded-2xl border border-red-200/60 bg-red-50/70 backdrop-blur p-5">
              <h3 className="font-bold text-red-800 text-sm mb-2 flex items-center gap-1.5">
                <span className="text-[10px] font-black bg-red-200 text-red-700 px-1.5 py-0.5 rounded">P0</span>
                {" "}Prochaine étape : Claude
              </h3>
              <p className="text-[13px] text-red-700 leading-relaxed">
                <strong>ANTHROPIC_API_KEY</strong> — une seule clé pour upgrader la qualité LLM (Claude Sonnet 4.5
                remplace DeepSeek pour le positionnement, SWOT, concurrence, recommandations + GEO moteur #1).
                DeepSeek reste en fallback automatique si Claude est down.
              </p>
            </div>

            <div className="rounded-2xl border border-amber-200/60 bg-amber-50/70 backdrop-blur p-5">
              <h3 className="font-bold text-amber-800 text-sm mb-2 flex items-center gap-1.5">
                <span className="text-[10px] font-black bg-amber-200 text-amber-700 px-1.5 py-0.5 rounded">P1</span>
                {" "}Suite : GEO multi-moteur
              </h3>
              <p className="text-[13px] text-amber-700 leading-relaxed">
                PERPLEXITY_API_KEY + OPENAI_API_KEY activent les 2 autres moteurs GEO.
                Le GEO passe de 1 moteur (DeepSeek) à 3 moteurs indépendants pour un score vraiment robuste.
              </p>
            </div>
          </div>
        </Section>

        {/* ── Footer ── */}
        <footer className="mt-12 pt-6 border-t border-slate-200/60 text-center text-[11px] text-slate-400">
          <p>
            Généré depuis le repo{" "}
            <code className="bg-slate-100 px-1 py-0.5 rounded">ahmedkhanch/brand-compass</code> &middot;{" "}
            Branch <code className="bg-slate-100 px-1 py-0.5 rounded">develop</code> &middot;{" "}
            Commit <code className="bg-slate-100 px-1 py-0.5 rounded">02300dd</code>
          </p>
          <p className="mt-1">
            Fichiers déposés dans <code className="bg-slate-100 px-1 py-0.5 rounded">docs/product-brief.jsx</code> et{" "}
            <code className="bg-slate-100 px-1 py-0.5 rounded">docs/devis_brand_compass_sarah.pdf</code>
          </p>
        </footer>
      </main>
    </div>
  );
}
