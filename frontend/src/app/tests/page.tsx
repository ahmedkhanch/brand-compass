import type { Metadata } from "next";
import AuditShell from "@/components/roadmap/AuditShell";
import CapabilityValidation from "@/components/roadmap/CapabilityValidation";
import pipeline from "@/data/radar-pipeline-validation.json";
import security from "@/data/radar-security-validation.json";
import validation from "@/data/radar-validation.json";
import styles from "@/components/roadmap/audit.module.css";

export const metadata: Metadata = { title: "RadarOS — validation fonctionnelle" };

export default function TestsPage() {
  return <AuditShell active="tests">
    <div className={styles.topline}><span>VALIDATION FONCTIONNELLE</span><span>{validation.date}</span></div>
    <header className={styles.hero}><p className={styles.eyebrow}>PREUVES DE LIVRAISON</p><h1>Page de validation</h1><p>{validation.scope}</p></header>
    <section className={styles.section} id="suivi-radaros"><h2>Suivi RadarOS V2 · /wip</h2><div className={styles.checks}>{validation.checks.map(check => <article className={styles.check} key={check.id}>
      <span className={`${styles.validationBadge} ${check.status === "passed" ? "" : styles.validationPending}`}>{check.id} · {check.status === "passed" ? "Vérifié" : "À vérifier"}</span><h3>{check.title}</h3><p>{check.procedure}</p><small>{check.evidence}</small>
    </article>)}</div></section>
    <CapabilityValidation capability={security} />
    <CapabilityValidation capability={pipeline} />
    <section className={styles.section}><h2>Validation du produit RadarOS</h2><div className={styles.card}><p>Les contrôles de sécurité et de frontière du pipeline ci-dessus sont validés en environnement isolé. Les analyses réelles, la facturation, les collecteurs et les scores V2 restent à valider. Leurs critères d’acceptation sont suivis dans chaque besoin de la matrice et dans les tickets P0/P1/P2.</p><a href="/wip#couverture">Consulter les validations attendues par capacité →</a></div></section>
    <footer className={styles.footer}>Cette page est dédiée à la validation fonctionnelle. Le catalogue API canonique reste Swagger /docs, lorsqu’un backend opérationnel est disponible.</footer>
  </AuditShell>;
}
