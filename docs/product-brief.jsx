import { useState } from "react";

const SECTIONS = [
  {
    id: "product",
    label: "Le Produit",
    icon: "◈",
  },
  {
    id: "features",
    label: "Features",
    icon: "◎",
  },
  {
    id: "offres",
    label: "Offres & Prix",
    icon: "◐",
  },
  {
    id: "faisabilite",
    label: "Faisabilité 2K",
    icon: "◉",
  },
];

const data = {
  product: {
    title: "Brand Compass",
    subtitle: "Outil de veille & diagnostic de marque",
    description:
      "Une plateforme SaaS permettant à n'importe quelle marque d'analyser instantanément sa position marché, ses concurrents et sa stratégie digitale — le tout alimenté par l'IA.",
    workflow: [
      "L'utilisateur entre un nom de marque + URL + réseaux sociaux",
      "Le moteur IA lance l'analyse (quelques secondes)",
      "Un rapport complet est généré automatiquement",
      "Des blocs premium sont floutés pour inciter à l'upgrade",
    ],
  },
  features: [
    {
      tier: "Core",
      color: "#C8F2A0",
      items: [
        {
          name: "Analyse de positionnement",
          detail:
            "Angle marketing, proposition de valeur, place dans le marché — enrichie de l'expertise de Sarah (KPIs métier, signaux clés du secteur)",
          feasible: true,
        },
        {
          name: "Analyse stratégie de communication",
          detail:
            "Lecture du LinkedIn, du site et des RS pour déduire les axes de communication actuels",
          feasible: true,
        },
        {
          name: "Scoring SEO & GEO",
          detail:
            "Référencement classique (SEO) + positionnement dans les IA génératives (ChatGPT, Claude, Perplexity) — le GEO",
          feasible: true,
        },
      ],
    },
    {
      tier: "Growth",
      color: "#A0D4F2",
      items: [
        {
          name: "Bibliothèque Meta Ads",
          detail:
            "Connexion à l'API Meta Ads Library pour récupérer les créas concurrentes, identifier les angles qui performent, estimer les budgets",
          feasible: "à vérifier",
        },
        {
          name: "Historique & alertes",
          detail:
            "Suivi dans le temps : détection de changements d'offre, nouvelles campagnes, évolution du positionnement par événement marketing (fêtes, soldes…)",
          feasible: true,
        },
      ],
    },
    {
      tier: "Premium",
      color: "#F2C4A0",
      items: [
        {
          name: "Rapport stratégique automatisé",
          detail:
            "Envoi hebdomadaire automatique d'un audit : tendances, recommandations créa, plan d'action — généré par IA à partir des données collectées",
          feasible: true,
        },
      ],
    },
  ],
  offres: [
    {
      name: "Boussole",
      price: "99€/mois",
      color: "#C8F2A0",
      desc: "Analyse instantanée à la demande",
      inclus: [
        "Diagnostic à l'instant T",
        "Positionnement + angle marketing",
        "Score SEO/GEO basique",
        "Requêtes illimitées",
        "Blocs premium floutés",
      ],
    },
    {
      name: "Radar",
      price: "199€/mois",
      color: "#A0D4F2",
      desc: "Veille avec historique",
      inclus: [
        "Tout Boussole +",
        "Historique N-1 par événement",
        "Alertes changements d'offre",
        "Accès bibliothèque Meta Ads",
        "Export de 10 visuels/mois",
      ],
    },
    {
      name: "Stratège",
      price: "499€/mois",
      color: "#F2C4A0",
      desc: "Audit automatisé chaque semaine",
      inclus: [
        "Tout Radar +",
        "Rapport hebdo automatique par email",
        "Recommandations créa & stratégiques",
        "KPIs à suivre personnalisés",
        "Porte d'entrée vers du conseil sur mesure",
      ],
    },
  ],
  faisabilite: {
    verdict: "OUI, faisable à ~2 000€",
    condition:
      "À condition de scoper le MVP sur les features Core + offre Boussole uniquement, avec une intégration Meta Ads en V2.",
    breakdown: [
      {
        poste: "Setup backend + API orchestration",
        detail: "Connexion APIs : Perplexity/Claude, SerpAPI, LinkedIn scraping basique",
        effort: "3–4j",
        risk: "faible",
      },
      {
        poste: "Moteur de prompts métier",
        detail:
          "Prompt engineering avec l'expertise de Sarah (les capillaires, les KPIs clés) — c'est ici que la valeur différenciante est créée",
        effort: "2j",
        risk: "faible",
      },
      {
        poste: "Scoring SEO / GEO",
        detail:
          "SEO via SerpAPI ou Semrush API. GEO : requêtes directes à ChatGPT/Claude pour voir si la marque est citée",
        effort: "2j",
        risk: "faible",
      },
      {
        poste: "Frontend (Lovable ou custom)",
        detail:
          "Landing page + formulaire d'input + affichage du rapport + blocs floutés + Stripe",
        effort: "2–3j",
        risk: "faible",
      },
      {
        poste: "Bibliothèque Meta Ads",
        detail:
          "API publique Meta Ad Library — accès sans token pour les publicités actives. À tester/valider avec Abraham",
        effort: "1–2j",
        risk: "moyen",
      },
    ],
    totalDev: "~10–13 jours homme",
    note: "À 150–200€/j (tarif junior/mid), on est dans l'enveloppe 2K. Abraham devra confirmer les contraintes Meta API.",
    risques: [
      "Meta Ad Library API : accès limité selon les pays/secteurs depuis les changements de politique 2024",
      "LinkedIn scraping : instable sans API officielle — alternative : analyse manuelle du profil public ou Phantombuster",
      "GEO scoring : pas de standard établi, il faudra concevoir la méthodologie avec Sarah",
    ],
  },
};

export default function ProductBrief() {
  const [active, setActive] = useState("product");
  const [aiQuery, setAiQuery] = useState("");
  const [aiResponse, setAiResponse] = useState("");
  const [aiLoading, setAiLoading] = useState(false);

  const askAI = async () => {
    if (!aiQuery.trim()) return;
    setAiLoading(true);
    setAiResponse("");
    try {
      const context = JSON.stringify(data, null, 2);
      const res = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1000,
          system: `Tu es un expert produit et tech. Tu aides à analyser la faisabilité et la stratégie d'un produit SaaS de veille de marque.
Voici le brief complet du produit :
${context}
Réponds de manière concise, directe et opérationnelle. Tu parles à des entrepreneurs francophones.`,
          messages: [{ role: "user", content: aiQuery }],
        }),
      });
      const json = await res.json();
      const text = json.content?.find((b) => b.type === "text")?.text || "Pas de réponse.";
      setAiResponse(text);
    } catch (e) {
      setAiResponse("Erreur lors de la requête IA.");
    }
    setAiLoading(false);
  };

  return (
    <div style={styles.root}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.badge}>BRIEF PRODUIT</div>
        <h1 style={styles.title}>Brand Compass</h1>
        <p style={styles.tagline}>
          Outil de veille & diagnostic de marque alimenté par l'IA
        </p>
        <div style={styles.meta}>
          <span style={styles.metaTag}>Sarah × Abdelhay × Abraham</span>
          <span style={styles.metaTag}>Budget cible : 2 000 €</span>
          <span style={styles.metaTag}>MVP · été 2025</span>
        </div>
      </div>

      {/* Nav */}
      <nav style={styles.nav}>
        {SECTIONS.map((s) => (
          <button
            key={s.id}
            onClick={() => setActive(s.id)}
            style={{
              ...styles.navBtn,
              ...(active === s.id ? styles.navBtnActive : {}),
            }}
          >
            <span style={styles.navIcon}>{s.icon}</span> {s.label}
          </button>
        ))}
      </nav>

      {/* Content */}
      <div style={styles.content}>
        {active === "product" && (
          <div style={styles.section}>
            <h2 style={styles.sectionTitle}>Vue d'ensemble du produit</h2>
            <div style={styles.card}>
              <p style={styles.bigDesc}>{data.product.description}</p>
            </div>
            <h3 style={styles.subTitle}>Comment ça marche</h3>
            <div style={styles.workflowGrid}>
              {data.product.workflow.map((step, i) => (
                <div key={i} style={styles.workflowStep}>
                  <div style={styles.stepNum}>{i + 1}</div>
                  <p style={styles.stepText}>{step}</p>
                </div>
              ))}
            </div>
            <div style={styles.callout}>
              <strong>💡 Modèle économique clé :</strong> L'outil est un produit
              d'appel (freemium/boussole), mais la vraie valeur se monétise sur
              l'abonnement premium à 499€/mois — un rapport hebdo automatisé
              qui se vend comme de la "prestation" sans en être une.
            </div>
          </div>
        )}

        {active === "features" && (
          <div style={styles.section}>
            <h2 style={styles.sectionTitle}>Features par niveau</h2>
            {data.features.map((tier) => (
              <div key={tier.tier} style={styles.tierBlock}>
                <div
                  style={{
                    ...styles.tierLabel,
                    background: tier.color,
                  }}
                >
                  {tier.tier}
                </div>
                {tier.items.map((item) => (
                  <div key={item.name} style={styles.featureCard}>
                    <div style={styles.featureHeader}>
                      <span style={styles.featureName}>{item.name}</span>
                      <span
                        style={{
                          ...styles.feasBadge,
                          background:
                            item.feasible === true
                              ? "#C8F2A0"
                              : item.feasible === "à vérifier"
                              ? "#FFE4A0"
                              : "#F2A0A0",
                          color: "#1a1a1a",
                        }}
                      >
                        {item.feasible === true
                          ? "✓ faisable"
                          : item.feasible === "à vérifier"
                          ? "⚠ à vérifier"
                          : "✗ risqué"}
                      </span>
                    </div>
                    <p style={styles.featureDetail}>{item.detail}</p>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}

        {active === "offres" && (
          <div style={styles.section}>
            <h2 style={styles.sectionTitle}>Structure des offres</h2>
            <div style={styles.offresGrid}>
              {data.offres.map((o) => (
                <div
                  key={o.name}
                  style={{
                    ...styles.offreCard,
                    borderTop: `4px solid ${o.color}`,
                  }}
                >
                  <div
                    style={{
                      ...styles.offreName,
                      color: "#1a1a1a",
                    }}
                  >
                    {o.name}
                  </div>
                  <div style={styles.offrePrice}>{o.price}</div>
                  <p style={styles.offreDesc}>{o.desc}</p>
                  <ul style={styles.offreList}>
                    {o.inclus.map((item, i) => (
                      <li key={i} style={styles.offreItem}>
                        <span style={{ color: o.color === "#C8F2A0" ? "#5a9e3a" : o.color === "#A0D4F2" ? "#2a7ab5" : "#c07020" }}>▸</span> {item}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        )}

        {active === "faisabilite" && (
          <div style={styles.section}>
            <h2 style={styles.sectionTitle}>Analyse de faisabilité à 2 000 €</h2>
            <div
              style={{
                ...styles.verdictBox,
                background: "#C8F2A0",
              }}
            >
              <div style={styles.verdictTitle}>{data.faisabilite.verdict}</div>
              <p style={styles.verdictCondition}>{data.faisabilite.condition}</p>
            </div>

            <h3 style={styles.subTitle}>Décomposition du chiffrage</h3>
            <div style={styles.tableWrap}>
              <table style={styles.table}>
                <thead>
                  <tr>
                    <th style={styles.th}>Poste</th>
                    <th style={styles.th}>Détail</th>
                    <th style={styles.th}>Effort</th>
                    <th style={styles.th}>Risque</th>
                  </tr>
                </thead>
                <tbody>
                  {data.faisabilite.breakdown.map((row, i) => (
                    <tr
                      key={i}
                      style={{ background: i % 2 === 0 ? "#f8f8f6" : "#fff" }}
                    >
                      <td style={styles.td}>
                        <strong>{row.poste}</strong>
                      </td>
                      <td style={{ ...styles.td, color: "#555" }}>
                        {row.detail}
                      </td>
                      <td style={{ ...styles.td, fontWeight: 700 }}>
                        {row.effort}
                      </td>
                      <td style={styles.td}>
                        <span
                          style={{
                            ...styles.riskBadge,
                            background:
                              row.risk === "faible"
                                ? "#C8F2A0"
                                : row.risk === "moyen"
                                ? "#FFE4A0"
                                : "#F2A0A0",
                          }}
                        >
                          {row.risk}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div style={styles.totalRow}>
              <span>Total estimé :</span>
              <strong>{data.faisabilite.totalDev}</strong>
            </div>
            <p style={styles.noteText}>{data.faisabilite.note}</p>

            <h3 style={styles.subTitle}>Points de vigilance</h3>
            {data.faisabilite.risques.map((r, i) => (
              <div key={i} style={styles.riskCard}>
                <span style={styles.riskIcon}>⚠</span>
                <p style={styles.riskText}>{r}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* AI Ask Section */}
      <div style={styles.aiSection}>
        <div style={styles.aiHeader}>
          <span style={styles.aiIcon}>✦</span>
          <span style={styles.aiTitle}>Pose une question sur ce brief</span>
        </div>
        <div style={styles.aiInputRow}>
          <input
            style={styles.aiInput}
            placeholder='Ex: "Quelle feature prioriser en V1 ?" ou "Quel est le vrai risque Meta Ads ?"'
            value={aiQuery}
            onChange={(e) => setAiQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && askAI()}
          />
          <button
            style={{
              ...styles.aiBtn,
              opacity: aiLoading ? 0.6 : 1,
              cursor: aiLoading ? "not-allowed" : "pointer",
            }}
            onClick={askAI}
            disabled={aiLoading}
          >
            {aiLoading ? "…" : "Envoyer"}
          </button>
        </div>
        {aiResponse && (
          <div style={styles.aiResponse}>
            <div style={styles.aiResponseLabel}>Réponse IA</div>
            <p style={styles.aiResponseText}>{aiResponse}</p>
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  root: {
    fontFamily: "'Georgia', 'Times New Roman', serif",
    background: "#FAFAF7",
    minHeight: "100vh",
    color: "#1a1a1a",
    maxWidth: 900,
    margin: "0 auto",
    padding: "0 0 60px 0",
  },
  header: {
    background: "#1a1a1a",
    color: "#FAFAF7",
    padding: "48px 40px 36px",
    textAlign: "center",
  },
  badge: {
    display: "inline-block",
    fontSize: 10,
    letterSpacing: 4,
    fontFamily: "monospace",
    background: "#C8F2A0",
    color: "#1a1a1a",
    padding: "4px 12px",
    marginBottom: 16,
    fontWeight: 700,
  },
  title: {
    fontSize: 52,
    fontWeight: 700,
    margin: "0 0 8px",
    letterSpacing: -1,
  },
  tagline: {
    fontSize: 16,
    opacity: 0.6,
    margin: "0 0 20px",
    fontStyle: "italic",
  },
  meta: {
    display: "flex",
    gap: 10,
    justifyContent: "center",
    flexWrap: "wrap",
  },
  metaTag: {
    fontSize: 11,
    letterSpacing: 1,
    fontFamily: "monospace",
    border: "1px solid rgba(255,255,255,0.3)",
    padding: "3px 10px",
    color: "rgba(255,255,255,0.7)",
  },
  nav: {
    display: "flex",
    borderBottom: "2px solid #1a1a1a",
    background: "#fff",
    position: "sticky",
    top: 0,
    zIndex: 10,
    flexWrap: "wrap",
  },
  navBtn: {
    flex: "1 1 auto",
    background: "none",
    border: "none",
    padding: "16px 20px",
    fontSize: 13,
    fontFamily: "monospace",
    letterSpacing: 0.5,
    cursor: "pointer",
    color: "#888",
    borderBottom: "3px solid transparent",
    transition: "all 0.15s",
  },
  navBtnActive: {
    color: "#1a1a1a",
    borderBottom: "3px solid #1a1a1a",
    fontWeight: 700,
  },
  navIcon: {
    marginRight: 6,
  },
  content: {
    padding: "40px",
  },
  section: {
    maxWidth: 820,
  },
  sectionTitle: {
    fontSize: 28,
    fontWeight: 700,
    marginBottom: 24,
    letterSpacing: -0.5,
  },
  subTitle: {
    fontSize: 16,
    fontWeight: 700,
    marginTop: 32,
    marginBottom: 16,
    textTransform: "uppercase",
    letterSpacing: 2,
    fontFamily: "monospace",
    color: "#555",
  },
  card: {
    background: "#fff",
    border: "1.5px solid #e0e0d8",
    padding: "24px 28px",
    marginBottom: 8,
  },
  bigDesc: {
    fontSize: 17,
    lineHeight: 1.7,
    margin: 0,
  },
  workflowGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 16,
    marginBottom: 24,
  },
  workflowStep: {
    display: "flex",
    gap: 16,
    alignItems: "flex-start",
    background: "#fff",
    border: "1.5px solid #e0e0d8",
    padding: "16px 20px",
  },
  stepNum: {
    width: 28,
    height: 28,
    background: "#1a1a1a",
    color: "#C8F2A0",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontFamily: "monospace",
    fontWeight: 700,
    fontSize: 12,
    flexShrink: 0,
  },
  stepText: {
    margin: 0,
    fontSize: 14,
    lineHeight: 1.5,
    color: "#333",
  },
  callout: {
    background: "#FFF8E8",
    border: "1.5px solid #E8D090",
    padding: "16px 20px",
    fontSize: 14,
    lineHeight: 1.6,
    color: "#5a4a10",
  },
  tierBlock: {
    marginBottom: 28,
  },
  tierLabel: {
    display: "inline-block",
    fontFamily: "monospace",
    fontWeight: 700,
    fontSize: 11,
    letterSpacing: 3,
    padding: "4px 12px",
    marginBottom: 12,
    textTransform: "uppercase",
  },
  featureCard: {
    background: "#fff",
    border: "1.5px solid #e0e0d8",
    padding: "16px 20px",
    marginBottom: 8,
  },
  featureHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 6,
    gap: 12,
    flexWrap: "wrap",
  },
  featureName: {
    fontWeight: 700,
    fontSize: 15,
  },
  feasBadge: {
    fontSize: 11,
    fontFamily: "monospace",
    padding: "3px 10px",
    fontWeight: 700,
    letterSpacing: 0.5,
    flexShrink: 0,
  },
  featureDetail: {
    margin: 0,
    fontSize: 13,
    color: "#555",
    lineHeight: 1.6,
  },
  offresGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: 16,
  },
  offreCard: {
    background: "#fff",
    border: "1.5px solid #e0e0d8",
    padding: "24px 20px",
  },
  offreName: {
    fontFamily: "monospace",
    fontWeight: 700,
    fontSize: 13,
    letterSpacing: 2,
    textTransform: "uppercase",
    marginBottom: 8,
  },
  offrePrice: {
    fontSize: 28,
    fontWeight: 700,
    marginBottom: 4,
    letterSpacing: -0.5,
  },
  offreDesc: {
    fontSize: 12,
    color: "#888",
    marginBottom: 16,
    fontStyle: "italic",
  },
  offreList: {
    listStyle: "none",
    padding: 0,
    margin: 0,
  },
  offreItem: {
    fontSize: 13,
    padding: "5px 0",
    borderTop: "1px solid #f0f0e8",
    color: "#333",
    display: "flex",
    gap: 8,
    alignItems: "flex-start",
    lineHeight: 1.4,
  },
  verdictBox: {
    padding: "20px 24px",
    marginBottom: 28,
    borderLeft: "5px solid #5a9e3a",
  },
  verdictTitle: {
    fontSize: 20,
    fontWeight: 700,
    marginBottom: 8,
  },
  verdictCondition: {
    margin: 0,
    fontSize: 14,
    lineHeight: 1.6,
    color: "#3a5a2a",
  },
  tableWrap: {
    overflowX: "auto",
    marginBottom: 8,
  },
  table: {
    width: "100%",
    borderCollapse: "collapse",
    fontSize: 13,
  },
  th: {
    textAlign: "left",
    padding: "10px 14px",
    background: "#1a1a1a",
    color: "#C8F2A0",
    fontFamily: "monospace",
    fontWeight: 700,
    letterSpacing: 0.5,
    fontSize: 11,
    textTransform: "uppercase",
  },
  td: {
    padding: "10px 14px",
    verticalAlign: "top",
    lineHeight: 1.5,
    borderBottom: "1px solid #e0e0d8",
  },
  riskBadge: {
    fontSize: 11,
    fontFamily: "monospace",
    padding: "2px 8px",
    fontWeight: 700,
  },
  totalRow: {
    display: "flex",
    justifyContent: "space-between",
    background: "#1a1a1a",
    color: "#C8F2A0",
    padding: "12px 14px",
    fontFamily: "monospace",
    fontSize: 14,
    marginBottom: 8,
  },
  noteText: {
    fontSize: 13,
    color: "#666",
    fontStyle: "italic",
    marginBottom: 28,
    lineHeight: 1.6,
  },
  riskCard: {
    display: "flex",
    gap: 12,
    background: "#FFF4E8",
    border: "1px solid #E8C080",
    padding: "12px 16px",
    marginBottom: 8,
    alignItems: "flex-start",
  },
  riskIcon: {
    fontSize: 16,
    flexShrink: 0,
    marginTop: 1,
  },
  riskText: {
    margin: 0,
    fontSize: 13,
    lineHeight: 1.6,
    color: "#5a3a10",
  },
  aiSection: {
    margin: "0 40px",
    border: "2px solid #1a1a1a",
    background: "#fff",
    padding: "28px",
  },
  aiHeader: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    marginBottom: 16,
  },
  aiIcon: {
    fontSize: 20,
    color: "#C8F2A0",
    background: "#1a1a1a",
    width: 32,
    height: 32,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
    lineHeight: 1,
    paddingTop: 2,
  },
  aiTitle: {
    fontFamily: "monospace",
    fontWeight: 700,
    fontSize: 13,
    letterSpacing: 1,
    textTransform: "uppercase",
  },
  aiInputRow: {
    display: "flex",
    gap: 10,
  },
  aiInput: {
    flex: 1,
    border: "1.5px solid #ccc",
    padding: "10px 14px",
    fontSize: 14,
    fontFamily: "Georgia, serif",
    outline: "none",
    background: "#FAFAF7",
  },
  aiBtn: {
    background: "#1a1a1a",
    color: "#C8F2A0",
    border: "none",
    padding: "10px 24px",
    fontFamily: "monospace",
    fontWeight: 700,
    fontSize: 13,
    letterSpacing: 1,
    cursor: "pointer",
    textTransform: "uppercase",
    flexShrink: 0,
  },
  aiResponse: {
    marginTop: 20,
    background: "#F5F5F0",
    border: "1px solid #e0e0d8",
    padding: "16px 20px",
  },
  aiResponseLabel: {
    fontFamily: "monospace",
    fontSize: 10,
    letterSpacing: 3,
    color: "#888",
    textTransform: "uppercase",
    marginBottom: 10,
  },
  aiResponseText: {
    margin: 0,
    fontSize: 14,
    lineHeight: 1.8,
    color: "#333",
    whiteSpace: "pre-wrap",
  },
};
