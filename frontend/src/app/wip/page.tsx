import StatusChrome from "@/components/StatusChrome";

// ── Constants ───────────────────────────────────────────────────────────────
const LAST_UPDATED = "11 juin 2026";
const GLOBAL_PROGRESS = 70; // %, pipeline core 100% réel ; reste prod + GEO multi-moteur

type PhaseStatus = "done" | "progress" | "todo";
type TaskState = "ok" | "wip" | "no";

interface Phase {
  num: number;
  title: string;
  status: PhaseStatus;
  badgeLabel: string;
  tasks: { state: TaskState; text: string }[];
  meta: string;
}

const STATUS_NUM: Record<PhaseStatus, string> = {
  done: "num-done",
  progress: "num-progress",
  todo: "num-todo",
};

const KPIS = [
  { big: "4 / 7", lbl: "providers réels actifs" },
  { big: "~70%", lbl: "avancement global" },
  { big: "6", lbl: "pages frontend livrées" },
  { big: "18", lbl: "endpoints backend" },
];

const PHASES: Phase[] = [
  {
    num: 1,
    title: "🧪 Fondation — Moteur de scoring (Sprint 1)",
    status: "done",
    badgeLabel: "FAIT",
    tasks: [
      { state: "ok", text: "7 providers API : Firecrawl, SerpAPI, DeepSeek, Claude, Perplexity, OpenAI, Apify" },
      { state: "ok", text: "Prompt Engine : contenu site → LLM → positionnement, SWOT, concurrence, recommandations" },
      { state: "ok", text: "Scoring SEO (0-100) : SERP ownership, keywords, featured snippets, negative content" },
      { state: "ok", text: "Scoring GEO (0-100) : visibilité IA, sentiment, cohérence multi-moteur" },
      { state: "ok", text: "Orchestrateur : pipeline complet ~60-90s, dégradation gracieuse" },
    ],
    meta: "🎯 La fondation : le moteur qui transforme une marque + URL en diagnostic complet.",
  },
  {
    num: 2,
    title: "⚙️ Backend SaaS (Sprint 2)",
    status: "done",
    badgeLabel: "FAIT",
    tasks: [
      { state: "ok", text: "FastAPI : 18 endpoints (analyse, rapports CRUD, SSE, crédits, abonnement, checkout, webhooks)" },
      { state: "ok", text: "Base de données : SQLAlchemy async, SQLite + PostgreSQL (Alembic), 8 modèles" },
      { state: "ok", text: "Auth Clerk (JWT) avec fallback token dev, tier gating, système de crédits" },
      { state: "ok", text: "Stripe : checkout / portail / webhooks · Cost tracking par provider · ARQ worker (Redis)" },
    ],
    meta: "🎯 Transformer le prototype CLI en backend SaaS multi-utilisateurs.",
  },
  {
    num: 3,
    title: "🎨 Frontend (Sprint 3)",
    status: "done",
    badgeLabel: "FAIT",
    tasks: [
      { state: "ok", text: "6 pages Next.js : landing, dashboard, nouvelle analyse, rapport, tarifs, paramètres" },
      { state: "ok", text: "Bilingue FR / EN, thème clair, loader de progression en direct" },
      { state: "ok", text: "Rapport premium : jauges animées, 8 sections, blocs premium floutés" },
    ],
    meta: "🎯 Une interface vendable pour que l'utilisateur n'ait jamais à toucher Swagger.",
  },
  {
    num: 4,
    title: "🔌 Branchement des vrais providers",
    status: "progress",
    badgeLabel: "EN COURS",
    tasks: [
      { state: "ok", text: "Firecrawl — scraping réel du site" },
      { state: "ok", text: "DeepSeek — LLM réel (positionnement, SWOT, concurrence, reco, GEO)" },
      { state: "ok", text: "SerpAPI — SEO scoring réel sur données Google live" },
      { state: "ok", text: "Apify — Meta Ads Library réelle (pubs Facebook/Instagram)" },
      { state: "no", text: "Perplexity + OpenAI — GEO multi-moteur (passer de 1 à 3 moteurs)" },
    ],
    meta: "🎯 Pipeline core déjà 100% data-driven. Reste le GEO multi-moteur pour un score robuste.",
  },
  {
    num: 5,
    title: "🚀 Passage en production",
    status: "todo",
    badgeLabel: "À FAIRE",
    tasks: [
      { state: "no", text: "Clerk — auth réelle (remplacer les tokens dev-user-*)" },
      { state: "no", text: "Stripe live — paiements réels (clés + price IDs)" },
      { state: "no", text: "PostgreSQL — passer de SQLite à la base managée (Alembic prêt)" },
      { state: "no", text: "Redis + ARQ — queue de jobs scalable · Resend — emails transactionnels" },
    ],
    meta: "🎯 Tout le code existe déjà — il s'active par clé API, zéro ligne à écrire.",
  },
  {
    num: 6,
    title: "💼 Go-to-market",
    status: "todo",
    badgeLabel: "À FAIRE",
    tasks: [
      { state: "no", text: "Tarification affinée (Boussole 99€ / Radar 199€ / Stratège 499€)" },
      { state: "no", text: "Démo + onboarding marques & agences" },
      { state: "no", text: "Rapport stratégique hebdo automatique (tier Stratège)" },
    ],
    meta: "🎯 Vendre le diagnostic aux marques et agences.",
  },
];

const SET_ASIDE = [
  {
    title: "Claude (Anthropic) comme LLM principal",
    detail:
      "DeepSeek fait le job à coût quasi nul (~$0.14/$0.28 par 1M tokens) et la qualité est suffisante pour le diagnostic. Claude mis de côté volontairement — réactivable en une clé si besoin d'un cran de qualité.",
  },
];

export default function RoadmapPage() {
  return (
    <StatusChrome
      active="roadmap"
      title="🗺️ Brand Compass — Roadmap & État du projet"
      sub={`Diagnostic de marque par IA · positionnement, SEO, GEO, concurrence, Meta Ads · mise à jour ${LAST_UPDATED}`}
    >
      <div className="vision">
        <h2>🎯 La vision</h2>
        <p>
          <strong>Un SaaS vendable aux marques & agences.</strong> On entre un nom de marque + une URL,
          le moteur IA produit un diagnostic complet — positionnement, SWOT, concurrence, SEO, GEO,
          recommandations, bibliothèque Meta Ads — en moins de 60 secondes.
        </p>
        <p>
          Architecture <strong>providers découplés + scoring déterministe</strong> : chaque service externe
          s&apos;active indépendamment dès que sa clé arrive. Les blocs premium sont floutés pour pousser à l&apos;upgrade.
        </p>
      </div>

      <div className="kpi-row">
        {KPIS.map((k) => (
          <div className="kpi" key={k.lbl}>
            <div className="big">{k.big}</div>
            <div className="lbl">{k.lbl}</div>
          </div>
        ))}
      </div>

      <h2 className="section">📊 Avancement global</h2>
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${GLOBAL_PROGRESS}%` }}>
          {GLOBAL_PROGRESS}%
        </div>
      </div>
      <div className="legend">
        <span>✅ Fait</span>
        <span>🔄 En cours</span>
        <span>⬜ À faire</span>
      </div>

      <h2 className="section">🚀 Les étapes produit</h2>
      {PHASES.map((p) => (
        <div className="phase" key={p.num}>
          <div className="phase-head">
            <div className={`phase-num ${STATUS_NUM[p.status]}`}>{p.num}</div>
            <div className="phase-title">{p.title}</div>
            <span className={`badge ${p.status}`}>{p.badgeLabel}</span>
          </div>
          <div className="phase-body">
            <ul className="tasks">
              {p.tasks.map((t, i) => (
                <li key={i} className={t.state}>
                  {t.text}
                </li>
              ))}
            </ul>
            <div className="meta">{p.meta}</div>
          </div>
        </div>
      ))}

      <h2 className="section">⏸️ Mis de côté (volontairement)</h2>
      <div className="phase">
        <div className="phase-body" style={{ padding: "18px 22px" }}>
          <ul className="tasks">
            {SET_ASIDE.map((s, i) => (
              <li key={i} className="no">
                <strong>{s.title}</strong> — {s.detail}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </StatusChrome>
  );
}
