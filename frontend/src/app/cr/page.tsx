"use client";

import { useState } from "react";
import StatusChrome from "@/components/StatusChrome";

// ── Real data, derived from git history + SPRINT_1/2/3.md ─────────────────────
// Project initiated by Ahmed Khanchouch <ahmedkhanchouch95@gmail.com>.
// Initial push 2026-06-09 15:57→16:05 (4 commits, 119 files, 16 199 insertions).
// Work spanned 2 days: Sprint 1 (8 juin) then Sprint 2 + 3 (9 juin).
const AUTHOR = "Ahmed Khanchouch";
// 1 June 2026 is a Monday → in a Monday-first grid there are 0 empty cells before day 1.
const EMPTY_BEFORE = 0;
const DAYS_IN_JUNE = 30;
const WEEKDAYS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"];

interface Entry {
  when: string;
  title: string;
  items: string[];
}
interface Day {
  day: number;
  badge: "full" | "half";
  badgeLabel: string;
  title: string;
  meta: string;
  entries: Entry[];
}

const DAYS: Record<number, Day> = {
  8: {
    day: 8,
    badge: "full",
    badgeLabel: "complète",
    title: "Lun. 8 juin — Sprint 1 : Moteur de scoring (CLI)",
    meta: `${AUTHOR} · Sprint 1 livré · pipeline CLI complet, 7 providers + 3 scorers`,
    entries: [
      {
        when: "Cadrage & architecture",
        title: "7 providers API découplés",
        items: [
          "Conception des wrappers Firecrawl, SerpAPI, DeepSeek, Claude, Perplexity, OpenAI, Apify.",
          "Principe : les providers renvoient des dicts (aucun effet de bord), chacun a un check_health().",
          "Dégradation gracieuse : si un scorer échoue, les autres produisent quand même le rapport.",
        ],
      },
      {
        when: "Prompt Engine",
        title: "Contenu du site → analyse structurée",
        items: [
          "Firecrawl scrape la home → markdown propre, injecté dans le LLM.",
          "4 sorties JSON validées : positionnement, SWOT, paysage concurrentiel, recommandations.",
          "Prompts pensés pour être extraits en templates YAML (fait au Sprint 2).",
        ],
      },
      {
        when: "Scoring",
        title: "SEO (0-100) + GEO (0-100, beta)",
        items: [
          "SEO via SerpAPI : SERP ownership (0-30), keyword ranking (0-40), SERP features (0-20), negative content (0-10).",
          "GEO 3-moteurs (Claude + Perplexity + OpenAI) : visibilité, sentiment, cohérence inter-moteurs.",
          "Extraction de keywords ancrée secteur, blacklist nav/CTA.",
        ],
      },
      {
        when: "Orchestrateur",
        title: "Pipeline de bout en bout",
        items: [
          "run_scoring.py : diagnostic complet en ~60-90s (12-18 appels API).",
          "Flags --skip-geo / --skip-positioning pour tester par bloc.",
        ],
      },
    ],
  },
  9: {
    day: 9,
    badge: "full",
    badgeLabel: "complète",
    title: "Mar. 9 juin — Sprint 2 + 3 : SaaS complet + push GitHub",
    meta: `${AUTHOR} · push initial 15:57→16:05 · 119 fichiers, 16 199 lignes, 4 commits`,
    entries: [
      {
        when: "Backend — Sprint 2",
        title: "FastAPI : 18 endpoints",
        items: [
          "Analyse de marque (background), rapports CRUD, SSE de progression, crédits, abonnement, checkout, webhooks.",
          "SQLAlchemy async : SQLite en dev, PostgreSQL en prod (Alembic), 8 modèles, auto-détection via DATABASE_URL.",
          "Auth Clerk (JWT) avec fallback token dev-user-*, tier gating, système de crédits débité avant analyse.",
        ],
      },
      {
        when: "Paiements & infra",
        title: "Stripe, cost tracking, ARQ",
        items: [
          "Stripe : checkout, portail client, webhooks (upgrade/downgrade selon abonnement).",
          "Cost tracking par provider (tokens in/out, coût en cents, durée).",
          "ARQ worker (Redis) avec fallback threading en dev · prompts extraits en YAML.",
        ],
      },
      {
        when: "Frontend — Sprint 3",
        title: "6 pages Next.js",
        items: [
          "Landing, dashboard, nouvelle analyse, rapport détaillé, tarifs, paramètres.",
          "Clerk auth, Tailwind, progression live via EventSource, blocs Meta Ads floutés (upgrade CTA).",
          "Rapport : 6+ sections (positionnement, SWOT, concurrence, SEO, GEO, recommandations).",
        ],
      },
      {
        when: "Mise en ligne",
        title: "Push initial sur GitHub",
        items: [
          "Commit initial Brand Compass v1.0 : 119 fichiers, 16 199 lignes.",
          "Nettoyage des scripts CLI Sprint 1 (les providers vivent dans backend/engine/providers/).",
          "Prompt Engine : bascule auto vers Claude/OpenAI dès que les clés sont ajoutées.",
        ],
      },
    ],
  },
};

const CRA_DAYS = Object.keys(DAYS).map(Number).sort((a, b) => a - b);

const STATS = [
  { n: "2", l: "journées de travail" },
  { n: "119", l: "fichiers produits" },
  { n: "16 199", l: "lignes de code" },
  { n: "4", l: "commits (push initial)" },
];

const DELIVERABLES = [
  ["run_scoring.py", "pipeline CLI"],
  ["orchestrator.py", "coordinateur"],
  ["providers/ (×7)", "wrappers API"],
  ["scorers/ (×3)", "SEO · GEO · positioning"],
  ["FastAPI app", "18 endpoints"],
  ["8 modèles SQLAlchemy", "DB async"],
  ["Frontend Next.js", "6 pages"],
  ["Clerk + Stripe", "auth & paiements"],
  ["prompts YAML", "5 templates"],
  ["SPRINT_1/2/3.md", "docs sprints"],
  ["README", "architecture v3.1"],
  ["alembic", "migrations DB"],
];

export default function CompteRenduPage() {
  const [openDay, setOpenDay] = useState<number | null>(null);

  const idx = openDay !== null ? CRA_DAYS.indexOf(openDay) : -1;
  const prevDay = idx > 0 ? CRA_DAYS[idx - 1] : null;
  const nextDay = idx >= 0 && idx < CRA_DAYS.length - 1 ? CRA_DAYS[idx + 1] : null;
  const current = openDay !== null ? DAYS[openDay] : null;

  // Monday-first grid: empty cells before day 1.
  const cells = [
    ...Array.from({ length: EMPTY_BEFORE }, () => null),
    ...Array.from({ length: DAYS_IN_JUNE }, (_, i) => i + 1),
  ];

  return (
    <StatusChrome
      active="cr"
      title="📋 Brand Compass — Compte-rendu des travaux"
      sub="Agenda des sessions de travail · clique un jour bleu pour voir le détail"
    >
      <div className="summary">
        <h2>📌 Synthèse</h2>
        <p>
          Projet <strong>initié et construit par {AUTHOR}</strong> sur 2 journées de travail
          (8-9 juin 2026). De la conception du moteur de scoring (Sprint 1) au SaaS complet —
          backend FastAPI 18 endpoints (Sprint 2) + frontend Next.js 6 pages (Sprint 3) — déployable
          et prêt à brancher les vraies clés API.
        </p>
        <div className="stat-row">
          {STATS.map((s) => (
            <div className="stat" key={s.l}>
              <div className="n">{s.n}</div>
              <div className="l">{s.l}</div>
            </div>
          ))}
        </div>
        <p style={{ marginTop: 16 }}>
          📅 <strong>2 journées de travail</strong> condensées, push initial sur GitHub le 9 juin 2026
          (4 commits, <code>ahmedkhanch</code>). Chiffres tirés de l&apos;historique git réel.
        </p>
      </div>

      <h2 className="section">🗓️ Agenda — Juin 2026</h2>
      <div className="cal-wrap">
        <div className="cal-month-title">Juin 2026</div>
        <div className="cal-days">
          {WEEKDAYS.map((d) => (
            <div className="cal-day-header" key={d}>
              {d}
            </div>
          ))}
          {cells.map((d, i) => {
            if (d === null) return <div className="cal-day empty" key={`e${i}`} />;
            const day = DAYS[d];
            if (!day)
              return (
                <div className="cal-day" key={d}>
                  {d}
                </div>
              );
            return (
              <div
                className={`cal-day has-cra${day.badge === "half" ? " partial" : ""}`}
                key={d}
                onClick={() => setOpenDay(d)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === "Enter" && setOpenDay(d)}
              >
                {d}
              </div>
            );
          })}
        </div>
        <div className="cal-legend">
          <span>
            <span className="sw full" /> Journée complète (~5-6h)
          </span>
          <span>
            <span className="sw half" /> Session courte (~1-2h)
          </span>
        </div>
        <div className="hint-click">👆 Clique un jour bleu pour voir le détail des travaux</div>
      </div>

      <h2 className="section">📦 Livrables produits ({DELIVERABLES.length})</h2>
      <div className="summary">
        <div className="stat-row">
          {DELIVERABLES.map(([name, desc]) => (
            <div className="stat" key={name} style={{ textAlign: "left" }}>
              <b>{name}</b> — {desc}
            </div>
          ))}
        </div>
      </div>

      {/* ── Modal ── */}
      <div
        className={`modal-overlay${current ? " open" : ""}`}
        onClick={(e) => {
          if (e.target === e.currentTarget) setOpenDay(null);
        }}
      >
        {current && (
          <div className="modal">
            <div className="modal-head">
              <h3>{current.title}</h3>
              <span className={`day-badge ${current.badge}`}>{current.badgeLabel}</span>
              <button className="modal-close" onClick={() => setOpenDay(null)} aria-label="Fermer">
                &times;
              </button>
            </div>
            <div className="modal-body">
              {current.entries.map((en, i) => (
                <div className="entry" key={i}>
                  <div className="when">{en.when}</div>
                  <h4>{en.title}</h4>
                  <ul>
                    {en.items.map((it, j) => (
                      <li key={j}>{it}</li>
                    ))}
                  </ul>
                </div>
              ))}
              <div className="meta-line">{current.meta}</div>
            </div>
            <div className="modal-foot">
              <button
                className="mbtn"
                disabled={prevDay === null}
                onClick={() => prevDay !== null && setOpenDay(prevDay)}
              >
                &larr; Jour précédent
              </button>
              <button
                className="mbtn"
                disabled={nextDay === null}
                onClick={() => nextDay !== null && setOpenDay(nextDay)}
              >
                Jour suivant &rarr;
              </button>
            </div>
          </div>
        )}
      </div>
    </StatusChrome>
  );
}
