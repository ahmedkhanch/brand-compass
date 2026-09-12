import type { Metadata } from "next";
import audit from "@/data/radar-audit.json";
import AuditShell from "@/components/roadmap/AuditShell";
import AuditExplorer from "@/components/roadmap/AuditExplorer";
import styles from "@/components/roadmap/audit.module.css";

export const metadata: Metadata = { title: "RadarOS — état du projet & feuille de route" };

export default function RoadmapPage() {
  const partial = audit.items.filter(x => x.status === "partial").length;
  const missing = audit.items.filter(x => x.status === "missing").length;
  return <AuditShell>
    <div className={styles.topline}><span>BRAND COMPASS → RADAROS V2</span><span>{audit.date} · référence {audit.baseline}</span></div>
    <header className={styles.hero}>
      <p className={styles.eyebrow}>REPRENDRE SUR DES FAITS</p>
      <h1>Un socle existe.<br /><span>Le produit RadarOS reste à construire.</span></h1>
      <p>Brand Compass sait déjà orchestrer un diagnostic de marque, du SEO, du GEO et une bibliothèque Meta Ads. Le brief V2 demande un moteur d’observation : produits, offres, contenus, stratégies et preuves — puis trois actions utiles.</p>
      <div className={styles.actions}><a className={styles.primary} href="#couverture">Explorer les 30 besoins ↓</a>{audit.boardUrl && <a className={styles.secondary} href={audit.boardUrl} target="_blank" rel="noreferrer">Ouvrir le board Forgejo ↗</a>}</div>
    </header>
    <div className={styles.metrics}>
      {[['30','sections du brief analysées'],[String(partial),'sections avec un socle partiel'],[String(missing),'sections à construire'],['0','section V2 validée de bout en bout']].map(([n,label]) => <div key={label}><strong>{n}</strong><span>{label}</span></div>)}
    </div>
    <p className={styles.note}>L’ancien « 70 % » décrivait les sprints Brand Compass de juin. Il est remplacé par une couverture du brief, sans pourcentage d’avancement artificiel. Les sections n’ont pas toutes la même taille.</p>
    <section className={styles.section}>
      <div className={styles.sectionHeading}><div><p className={styles.eyebrow}>CE QUI EST VÉRIFIÉ</p><h2>État de reprise</h2></div><a href={audit.repository} target="_blank" rel="noreferrer">Code sur GitHub ↗</a></div>
      <div className={styles.runtimeGrid}>
        <article className={styles.card}><h3>Application & accès</h3><p>{audit.runtime.frontend}</p><p>{audit.runtime.backend}</p><small>{audit.runtime.auth}</small></article>
        <article className={styles.card}><h3>Données & fournisseurs</h3><p>{audit.runtime.providers}</p><p>Les tests de démonstration ne prouvent ni une collecte réelle ni la conformité RadarOS V2.</p></article>
        <article className={styles.card}><h3>Sources de l’audit</h3><p>{audit.brief}, texte intégral et visuel embarqué examinés. Code de la branche {audit.branch}, état initial {audit.baseline}.</p><p>Les tickets sont suivis dans Forgejo. Le code reste dans le dépôt GitHub privé existant.</p><a href="/tests">Voir les validations de cette livraison →</a></article>
      </div>
    </section>
    <section id="priorites" className={styles.section}>
      <div className={styles.sectionHeading}><div><p className={styles.eyebrow}>ORDRE DE REPRISE</p><h2>Fiabiliser, observer, puis interpréter.</h2></div></div>
      <div className={styles.phases}>
        <article><span>01 · P0</span><h3>Fiabilité du socle</h3><p>Authentification, isolation, crédits, jobs, schéma de preuves, distinction réel/simulé et progression honnête.</p></article>
        <article><span>02 · P1</span><h3>RadarOS utilisable</h3><p>Collecteurs produits/social/Ads/site, sept scores, fiche sourcée, trois actions, historique et offres Radar 10/20.</p></article>
        <article><span>03 · P2</span><h3>Passerelle MarketOS</h3><p>Teasings contextuels et offre à 99 €. Les vrais connecteurs Shopify/Klaviyo et le suivi continu forment un chantier distinct.</p></article>
      </div>
      <div className={styles.risks}>{audit.risks.map(risk => <details className={styles.risk} key={risk.id} id={risk.id}><summary><span className={styles.p0}>{risk.priority}</span><strong>{risk.title}</strong><span>+</span></summary><div><p>{risk.detail}</p><ul>{risk.acceptance.map(x => <li key={x}>{x}</li>)}</ul>{"issueUrl" in risk && <a href={String(risk.issueUrl)} target="_blank" rel="noreferrer">Ticket {risk.id} ↗</a>}</div></details>)}</div>
    </section>
    <AuditExplorer />
    <section id="relecture" className={styles.section}>
      <p className={styles.eyebrow}>REGARD CROISÉ</p><h2>Analyse Codex & relecture AskClaude high</h2>
      <div className={styles.card}><p className={styles.reviewStatus}>{audit.review.status}</p><ul>{audit.review.summary.map(x => <li key={x}>{x}</li>)}</ul><p>Décision retenue : conserver les adaptateurs et l’interface utiles, construire d’abord des observations normalisées et traçables, puis adapter le scoring et les recommandations. L’ajout de clés API ne suffit pas à livrer V2.</p></div>
    </section>
    <section className={styles.section}><p className={styles.eyebrow}>DÉCISIONS À PRENDRE</p><h2>Les arbitrages encore ouverts</h2><div className={styles.card}><ol>{audit.decisions.map(x => <li key={x}>{x}</li>)}</ol></div></section>
    <footer className={styles.footer}>Source de vérité : matrice versionnée dans le code · preuves au commit audité · avancement de réalisation dans les tickets.<br />Les accès et mots de passe ne sont pas publiés dans cette page.</footer>
  </AuditShell>;
}
