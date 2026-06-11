"use client";
/**
 * Lightweight FR/EN i18n — no external dependency.
 *
 * A React context exposes { lang, setLang, t }. `t(key)` looks the key up in the
 * dictionary below and returns the string for the active language. The choice is
 * persisted to localStorage and defaults to French. Server and first client
 * render both use the default language, so there is no hydration mismatch; the
 * stored preference is applied in an effect after mount.
 *
 * Scope: UI chrome only (labels, titles, buttons). The AI-generated report
 * CONTENT (SWOT items, positioning text…) is intentionally left as produced by
 * the backend.
 */
import React, { createContext, useContext, useEffect, useState, useCallback } from "react";

export type Lang = "fr" | "en";

const STORAGE_KEY = "bc-lang";
const DEFAULT_LANG: Lang = "fr";

type Entry = { fr: string; en: string };

const MESSAGES: Record<string, Entry> = {
  // ── Navbar ──
  "nav.dashboard": { fr: "Tableau de bord", en: "Dashboard" },
  "nav.pricing": { fr: "Tarifs", en: "Pricing" },
  "nav.signin": { fr: "Se connecter", en: "Sign In" },
  "nav.getstarted": { fr: "Commencer", en: "Get Started" },

  // ── Landing ──
  "home.heroTitle": { fr: "Intelligence de marque par IA", en: "AI-Powered Brand Intelligence" },
  "home.heroSubtitle": {
    fr: "Entrez un nom de marque et une URL. Obtenez un rapport de diagnostic complet — positionnement, SWOT, analyse concurrentielle, SEO, GEO et recommandations — en moins de 60 secondes.",
    en: "Enter a brand name and website URL. Get a complete diagnostic report — positioning, SWOT, competitive analysis, SEO, GEO, and recommendations — in under 60 seconds.",
  },
  "home.ctaStart": { fr: "Commencer gratuitement", en: "Get Started Free" },
  "home.ctaPricing": { fr: "Voir les tarifs", en: "View Pricing" },
  "feat.positioning.t": { fr: "Positionnement de marque", en: "Brand Positioning" },
  "feat.positioning.d": {
    fr: "Archétype, proposition de valeur, cible, voix de marque — extraits de votre site par l'IA.",
    en: "Archetype, value proposition, target audience, brand voice — extracted from your website by AI.",
  },
  "feat.scoring.t": { fr: "Scoring SEO & GEO", en: "SEO & GEO Scoring" },
  "feat.scoring.d": {
    fr: "Présence dans les SERP Google + visibilité dans les moteurs IA. Sachez où vous en êtes.",
    en: "Google SERP ownership + AI engine visibility. Know where you stand in search and generative AI.",
  },
  "feat.competitive.t": { fr: "Paysage concurrentiel", en: "Competitive Landscape" },
  "feat.competitive.d": {
    fr: "Concurrents directs cartographiés avec niveaux de menace. Sachez qui gagne et pourquoi.",
    en: "Direct competitors mapped with threat levels. Know who's winning and why.",
  },
  "feat.swot.t": { fr: "Analyse SWOT", en: "SWOT Analysis" },
  "feat.swot.d": {
    fr: "Forces, faiblesses, opportunités, menaces — générées à partir du contenu réel du site.",
    en: "Strengths, weaknesses, opportunities, threats — generated from real website content.",
  },
  "feat.reco.t": { fr: "Recommandations actionnables", en: "Actionable Recommendations" },
  "feat.reco.d": {
    fr: "Quick wins et mouvements stratégiques priorisés par impact. Arrêtez de deviner.",
    en: "Quick wins and strategic moves prioritized by impact. Stop guessing.",
  },
  "feat.progress.t": { fr: "Progression en direct", en: "Live Progress" },
  "feat.progress.d": {
    fr: "Regardez votre rapport se construire étape par étape, en temps réel.",
    en: "Watch your report build step by step in real-time. No waiting in the dark.",
  },

  // ── Dashboard ──
  "dash.title": { fr: "Tableau de bord", en: "Dashboard" },
  "dash.credits": { fr: "{n} crédits restants", en: "{n} credits remaining" },
  "dash.new": { fr: "+ Nouvelle analyse", en: "+ New Analysis" },
  "dash.loading": { fr: "Chargement des rapports…", en: "Loading reports..." },
  "dash.empty": { fr: "Aucun rapport pour l'instant", en: "No reports yet" },
  "dash.emptyCta": { fr: "Lancez votre première analyse de marque →", en: "Run your first brand analysis →" },
  "dash.signinTitle": { fr: "Connectez-vous pour voir votre tableau de bord", en: "Sign in to view your dashboard" },
  "dash.signinSub": { fr: "Créez un compte pour commencer à analyser des marques.", en: "Create an account to start analyzing brands." },
  "dash.untitled": { fr: "Sans titre", en: "Untitled" },
  "dash.upgraded": { fr: "Mise à niveau vers {tier} réussie !", en: "Successfully upgraded to {tier}!" },
  "common.loading": { fr: "Chargement…", en: "Loading..." },

  // ── Analyze ──
  "an.title": { fr: "Nouvelle analyse de marque", en: "New Brand Analysis" },
  "an.brand": { fr: "Nom de la marque *", en: "Brand Name *" },
  "an.website": { fr: "URL du site web", en: "Website URL" },
  "an.industry": { fr: "Secteur", en: "Industry" },
  "an.competitor": { fr: "Concurrent", en: "Competitor" },
  "an.start": { fr: "Lancer l'analyse", en: "Start Analysis" },
  "an.running": { fr: "Analyse en cours…", en: "Analyzing…" },
  "an.step": { fr: "Étape {i} / {n}", en: "Step {i} / {n}" },
  "an.doneShort": { fr: "Terminé", en: "Done" },
  "an.ready": { fr: "Rapport prêt ✓", en: "Report ready ✓" },
  "an.errNoId": { fr: "Aucun identifiant de rapport renvoyé", en: "No report ID returned" },
  "an.errFailed": { fr: "L'analyse a échoué côté serveur", en: "Analysis failed on the server" },
  "an.errTimeout": { fr: "Le rapport a mis trop de temps à se générer", en: "The report took too long to generate" },
  "an.errUnknown": { fr: "Erreur inconnue", en: "Unknown error" },
  "an.stage1": { fr: "Extraction du contenu du site web…", en: "Extracting website content…" },
  "an.stage2": { fr: "Analyse du positionnement de marque…", en: "Analyzing brand positioning…" },
  "an.stage3": { fr: "Génération de l'analyse SWOT…", en: "Generating SWOT analysis…" },
  "an.stage4": { fr: "Cartographie du paysage concurrentiel…", en: "Mapping the competitive landscape…" },
  "an.stage5": { fr: "Calcul du score SEO…", en: "Computing SEO score…" },
  "an.stage6": { fr: "Évaluation de la visibilité GEO (IA générative)…", en: "Evaluating GEO visibility (generative AI)…" },
  "an.stage7": { fr: "Rédaction des recommandations stratégiques…", en: "Writing strategic recommendations…" },
  "an.stage8": { fr: "Assemblage du rapport final…", en: "Assembling the final report…" },

  // ── Pricing ──
  "price.title": { fr: "Tarifs simples", en: "Simple Pricing" },
  "price.subtitle": { fr: "Choisissez le plan adapté à vos besoins d'intelligence de marque", en: "Choose the plan that fits your brand intelligence needs" },
  "price.popular": { fr: "Le plus populaire", en: "Most Popular" },
  "price.perMonth": { fr: "/mois", en: "/month" },
  "price.reports": { fr: "{n}/mois", en: "{n}/month" },
  "price.redirecting": { fr: "Redirection…", en: "Redirecting..." },
  "price.upgrade": { fr: "Mettre à niveau", en: "Upgrade" },
  "price.signinUpgrade": { fr: "Se connecter pour mettre à niveau", en: "Sign In to Upgrade" },
  "price.checkoutErr": { fr: "Erreur de paiement : ", en: "Checkout error: " },
  "feat.everythingBoussole": { fr: "Tout Boussole", en: "Everything in Boussole" },
  "feat.everythingRadar": { fr: "Tout Radar", en: "Everything in Radar" },
  "feat.metaAds": { fr: "Analyse Meta Ads", en: "Meta Ads Analysis" },
  "feat.history": { fr: "Historique des rapports", en: "Report History" },
  "feat.pdf": { fr: "Export PDF", en: "Export to PDF" },
  "feat.prioritySupport": { fr: "Support prioritaire", en: "Priority Support" },
  "feat.alerts": { fr: "Alertes concurrentielles", en: "Competitive Alerts" },
  "feat.api": { fr: "Accès API", en: "API Access" },
  "feat.whiteLabel": { fr: "Rapports en marque blanche", en: "White-Label Reports" },
  "feat.analyst": { fr: "Analyste dédié", en: "Dedicated Analyst" },
  "feat.seoScore": { fr: "Score SEO", en: "SEO Score" },
  "feat.geoScore": { fr: "Score GEO", en: "GEO Score" },
  "feat.reco": { fr: "Recommandations", en: "Recommendations" },

  // ── Settings ──
  "set.title": { fr: "Paramètres", en: "Settings" },
  "set.signin": { fr: "Connectez-vous pour voir les paramètres.", en: "Sign in to view settings." },
  "set.subscription": { fr: "Abonnement", en: "Subscription" },
  "set.planSuffix": { fr: "Plan", en: "Plan" },
  "set.manage": { fr: "Gérer la facturation", en: "Manage Billing" },
  "set.credits": { fr: "Crédits", en: "Credits" },
  "set.creditsSub": { fr: "rapports restants ce mois-ci", en: "reports remaining this month" },
  "set.upgrade": { fr: "Changer de plan →", en: "Upgrade Plan →" },
  "status.active": { fr: "actif", en: "active" },

  // ── Status badge ──
  "status.queued": { fr: "en file", en: "queued" },
  "status.running": { fr: "en cours", en: "running" },
  "status.complete": { fr: "terminé", en: "complete" },
  "status.failed": { fr: "échoué", en: "failed" },

  // ── Report ──
  "r.eyebrow": { fr: "BRAND COMPASS · RAPPORT DE DIAGNOSTIC", en: "BRAND COMPASS · DIAGNOSTIC REPORT" },
  "r.titleSuffix": { fr: "Rapport d'intelligence de marque", en: "Brand Intelligence Report" },
  "r.back": { fr: "Retour", en: "Back" },
  "r.overall": { fr: "Score global", en: "Overall score" },
  "r.industry": { fr: "Secteur", en: "Industry" },
  "r.marketPosition": { fr: "Position marché", en: "Market position" },
  "r.runningBanner": { fr: "Pipeline en cours… Actualisez pour suivre la progression.", en: "Pipeline running… Refresh to check progress." },
  "r.loading": { fr: "Chargement du rapport…", en: "Loading report..." },
  "r.notFound": { fr: "Rapport introuvable", en: "Report not found" },
  "r.generatedOn": { fr: "Généré le", en: "Generated on" },
  "r.poweredBy": { fr: "Propulsé par Brand Compass", en: "Powered by Brand Compass" },

  "sec.positioning": { fr: "Positionnement de marque", en: "Brand Positioning" },
  "pos.archetype": { fr: "Archétype", en: "Archetype" },
  "pos.valueProp": { fr: "Proposition de valeur", en: "Value proposition" },
  "pos.audience": { fr: "Cible", en: "Target audience" },
  "pos.voice": { fr: "Voix de marque", en: "Brand voice" },
  "pos.diff": { fr: "Différenciateurs", en: "Differentiators" },
  "pos.mapTitle": { fr: "Carte de positionnement", en: "Positioning map" },
  "pos.premium": { fr: "Premium", en: "Premium" },
  "pos.value": { fr: "Accessible", en: "Value" },
  "pos.emotional": { fr: "Émotionnel", en: "Emotional" },
  "pos.rational": { fr: "Rationnel", en: "Rational" },

  "sec.swot": { fr: "Analyse SWOT", en: "SWOT Analysis" },
  "swot.s": { fr: "Forces", en: "Strengths" },
  "swot.w": { fr: "Faiblesses", en: "Weaknesses" },
  "swot.o": { fr: "Opportunités", en: "Opportunities" },
  "swot.t": { fr: "Menaces", en: "Threats" },
  "label.summary": { fr: "Synthèse", en: "Executive summary" },

  "sec.competitive": { fr: "Paysage concurrentiel", en: "Competitive Landscape" },
  "comp.differentiator": { fr: "Différenciateur", en: "Differentiator" },
  "comp.advantage": { fr: "Avantage concurrentiel", en: "Competitive advantage" },
  "comp.directCompetitors": { fr: "Concurrents directs", en: "Direct competitors" },
  "threat.high": { fr: "Élevé", en: "High" },
  "threat.medium": { fr: "Moyen", en: "Medium" },
  "threat.low": { fr: "Faible", en: "Low" },

  "sec.seo": { fr: "Score SEO", en: "SEO Score" },
  "sec.geo": { fr: "Score GEO", en: "GEO Score" },
  "r.breakdown": { fr: "Détail du score", en: "Score breakdown" },
  "bk.serp_ownership": { fr: "Présence SERP", en: "SERP ownership" },
  "bk.keyword_ranking": { fr: "Positionnement mots-clés", en: "Keyword ranking" },
  "bk.serp_features": { fr: "Fonctionnalités SERP", en: "SERP features" },
  "bk.negative_content": { fr: "Contenu négatif", en: "Negative content" },
  "bk.visibility": { fr: "Visibilité", en: "Visibility" },
  "bk.sentiment": { fr: "Sentiment", en: "Sentiment" },
  "bk.consistency": { fr: "Cohérence", en: "Consistency" },

  "sec.reco": { fr: "Recommandations actionnables", en: "Actionable Recommendations" },
  "reco.priority": { fr: "Priorité", en: "Priority focus" },
  "reco.quickWins": { fr: "Quick wins", en: "Quick wins" },
  "reco.strategic": { fr: "Mouvements stratégiques", en: "Strategic moves" },
  "reco.impact": { fr: "Impact", en: "Impact" },
  "reco.effort": { fr: "Effort", en: "Effort" },

  "sec.metaads": { fr: "Analyse Meta Ads", en: "Meta Ads Analysis" },
  "meta.locked": { fr: "Les données Meta Ads sont disponibles à partir de l'offre Radar.", en: "Meta Ads data is available on Radar tier and above." },
  "meta.lockedSub": { fr: "Inclut l'analyse de la bibliothèque publicitaire Facebook & Instagram.", en: "Includes Facebook & Instagram ad library analysis." },
  "meta.upgradeTitle": { fr: "Passer à Radar", en: "Upgrade to Radar" },
  "meta.upgradePrice": { fr: "199 $/mois — 100 rapports, Meta Ads, historique", en: "$199/mo — 100 reports, Meta Ads, history" },
  "meta.upgradeNow": { fr: "Mettre à niveau", en: "Upgrade Now" },
  "meta.adsFound": { fr: "{n} publicités actives trouvées pour {brand}", en: "{n} active ads found for {brand}" },
  "meta.loading": { fr: "Chargement des données Meta Ads…", en: "Loading Meta Ads data..." },
};

interface I18nValue {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
}

const I18nContext = createContext<I18nValue>({
  lang: DEFAULT_LANG,
  setLang: () => {},
  t: (k) => k,
});

function interpolate(s: string, vars?: Record<string, string | number>): string {
  if (!vars) return s;
  return s.replace(/\{(\w+)\}/g, (_, k) => (k in vars ? String(vars[k]) : `{${k}}`));
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>(DEFAULT_LANG);

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (stored === "fr" || stored === "en") setLangState(stored);
    } catch {
      /* localStorage unavailable (private mode) — keep default */
    }
  }, []);

  const setLang = useCallback((l: Lang) => {
    setLangState(l);
    try {
      window.localStorage.setItem(STORAGE_KEY, l);
    } catch {
      /* localStorage unavailable — selection still applies for this session */
    }
  }, []);

  const t = useCallback(
    (key: string, vars?: Record<string, string | number>) => {
      const entry = MESSAGES[key];
      if (!entry) return key;
      return interpolate(entry[lang] ?? entry.en ?? key, vars);
    },
    [lang]
  );

  return <I18nContext.Provider value={{ lang, setLang, t }}>{children}</I18nContext.Provider>;
}

export const useI18n = () => useContext(I18nContext);

export function LangToggle({ variant = "dark" }: { variant?: "dark" | "light" }) {
  const { lang, setLang } = useI18n();
  const base = variant === "light" ? "border-slate-300" : "border-zinc-700";
  const idle = variant === "light" ? "text-slate-500 hover:text-slate-900" : "text-zinc-400 hover:text-white";
  const langs: Lang[] = ["fr", "en"];
  return (
    <div className={`flex items-center rounded-lg border ${base} overflow-hidden text-xs select-none`}>
      {langs.map((l) => (
        <button
          key={l}
          type="button"
          onClick={() => setLang(l)}
          aria-pressed={lang === l}
          className={`px-2 py-1 font-semibold uppercase transition ${
            lang === l ? "bg-emerald-500 text-black" : idle
          }`}
        >
          {l}
        </button>
      ))}
    </div>
  );
}
