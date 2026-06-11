"use client";

import { useState } from "react";
import StatusChrome from "@/components/StatusChrome";

// ── Real data, derived from git history + SPRINT_1/2/3.md ─────────────────────
// Two contributors:
//  • Ahmed Khanchouch <ahmedkhanchouch95@gmail.com> — initiated the project,
//    Sprint 1 (8 juin) + Sprint 2/3 + initial push (9 juin, 4 commits, 119 files).
//  • Ousama Ben Younes <benyounes.ousama@gmail.com> — took over (11 juin, 21
//    commits 08:34→22:23): keyless demo, real providers, UI refonte, roadmap/CR.
const AHMED = "Ahmed Khanchouch";
const OUSAMA = "Ousama Ben Younes";
// 1 June 2026 is a Monday → in a Monday-first grid there are 0 empty cells before day 1.
const EMPTY_BEFORE = 0;
const DAYS_IN_JUNE = 30;
const WEEKDAYS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"];

// Contributors — Ousama on top, then Ahmed.
const CONTRIBUTORS = [
  { name: OUSAMA, role: "Démo keyless · vrais providers · refonte UI · roadmap/CR", days: "11 juin", commits: 21 },
  { name: AHMED, role: "Initiateur · moteur de scoring · backend + frontend", days: "8-9 juin", commits: 4 },
];

interface Entry {
  when: string;
  title: string;
  items: string[];
}
interface Day {
  day: number;
  author: string;
  title: string;
  meta: string;
  entries: Entry[];
}

const DAYS: Record<number, Day> = {
  8: {
    day: 8,
    author: AHMED,
    title: "Lun. 8 juin — Sprint 1 : Moteur de scoring (CLI)",
    meta: `${AHMED} · Sprint 1 livré · pipeline CLI complet, 7 providers + 3 scorers`,
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
    author: AHMED,
    title: "Mar. 9 juin — Sprint 2 + 3 : SaaS complet + push GitHub",
    meta: `${AHMED} · push initial 15:57→16:05 · 119 fichiers, 16 199 lignes, 4 commits`,
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
  11: {
    day: 11,
    author: OUSAMA,
    title: "Jeu. 11 juin — Démo keyless → 4 providers réels → roadmap",
    meta: `${OUSAMA} · 21 commits · 08:34→22:23 · démo keyless → pipeline 4 providers réels → refonte UI → roadmap/CR`,
    entries: [
      {
        when: "Matin · 08:34→09:59",
        title: "Mode démo keyless + refonte UI",
        items: [
          "DEMO_MODE : mocks déterministes seedés par marque + bypass Clerk → démo sans aucune clé.",
          "Fix résolution du package app sous pytest (suppression d'un __init__.py parasite).",
          "Loader de progression réaliste pour l'analyse · rapport premium (charts + parallax) FR/EN, fix hydration.",
          "Thème clair professionnel sur toute l'app + menu de sections du rapport.",
        ],
      },
      {
        when: "Midi · 11:07→12:07",
        title: "Auto-switch des providers + page WIP",
        items: [
          "Auto-switch par clé : chaque provider passe en réel dès que sa clé apparaît dans .env.",
          "GEO : fallback propre vers MockLLM quand aucun moteur réel n'a de clé.",
          "Fix texte d'input invisible (blanc sur blanc) en thème clair.",
          "Création de la page d'état /wip (mock → réel, ce qui reste à faire).",
        ],
      },
      {
        when: "Après-midi · 13:10→14:02",
        title: "Vrais providers + chasse aux bugs",
        items: [
          "Branchement DeepSeek puis SerpAPI : SEO scoring réel (Nike 83/100 sur données Google live).",
          "Fix spinner infini de la page rapport · fix re-render loop du dashboard (getToken instable).",
          "Fix suppression de rapport (cascade delete report_costs) · dépôt des fichiers brief + devis.",
          "Analyse complète mock → réel de chaque provider (sous-agent).",
        ],
      },
      {
        when: "Soir · 18:49→22:23",
        title: "Apify (Meta Ads) + roadmap & compte-rendu",
        items: [
          "Apify branché : Meta Ads Library réelle → 4e provider réel (pubs Facebook/Instagram).",
          "Fix du parcours run asynchrone pour le plan gratuit Apify (create → poll → dataset).",
          "Retrait de Claude de la roadmap (DeepSeek suffit à coût quasi nul).",
          "Refonte /wip + nouvelle page /cr au format papier (roadmap + compte-rendu cliquable).",
        ],
      },
    ],
  },
};

const CRA_DAYS = Object.keys(DAYS).map(Number).sort((a, b) => a - b);

const STATS = [
  { n: "3", l: "journées de travail" },
  { n: "2", l: "contributeurs" },
  { n: "25", l: "commits" },
  { n: "4 / 7", l: "providers réels" },
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
          <strong>{OUSAMA}</strong> a repris le projet le 11 juin et l&apos;a mené au{" "}
          <strong>pipeline 100% réel</strong> : mode démo keyless, branchement des 4 providers
          (Firecrawl, DeepSeek, SerpAPI, Apify), refonte UI complète, chasse aux bugs et roadmap/CR —
          21 commits sur la journée (08:34→22:23).
        </p>
        <p>
          Projet <strong>initié par {AHMED}</strong> les 8-9 juin : moteur de scoring (Sprint 1),
          puis backend FastAPI 18 endpoints + frontend Next.js 6 pages (Sprints 2-3), push initial
          sur GitHub (119 fichiers, 16 199 lignes).
        </p>
        <div className="stat-row">
          {STATS.map((s) => (
            <div className="stat" key={s.l}>
              <div className="n">{s.n}</div>
              <div className="l">{s.l}</div>
            </div>
          ))}
        </div>
        <div className="stat-row" style={{ marginTop: 14 }}>
          {CONTRIBUTORS.map((c) => (
            <div className="stat" key={c.name} style={{ textAlign: "left" }}>
              <b>{c.name}</b>
              <div className="l" style={{ marginTop: 4 }}>
                {c.days} · {c.commits} commits — {c.role}
              </div>
            </div>
          ))}
        </div>
        <p style={{ marginTop: 16 }}>
          📅 <strong>3 journées de travail</strong> sur 2 contributeurs. Chiffres et dates tirés
          de l&apos;historique git réel (<code>ahmedkhanch</code> + <code>Ousama Ben Younes</code>).
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
                className={`cal-day has-cra${day.author === OUSAMA ? "" : " partial"}`}
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
            <span className="sw full" /> {OUSAMA} (11 juin)
          </span>
          <span>
            <span className="sw half" /> {AHMED} (8-9 juin)
          </span>
        </div>
        <div className="hint-click">👆 Clique un jour pour voir le détail des travaux</div>
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
              <span className="day-badge full">{current.author}</span>
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
