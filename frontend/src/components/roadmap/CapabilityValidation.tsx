import styles from "./audit.module.css";

type Check = { id: string; title: string; status: string; procedure: string; evidence: string };
type Capability = { id: string; title: string; summary: string; environment: string; checks: Check[]; limitations: string[] };

export default function CapabilityValidation({ capability }: { capability: Capability }) {
  return <section className={styles.section} id={capability.id}>
    <p className={styles.eyebrow}>{capability.environment}</p><h2>{capability.title}</h2><p>{capability.summary}</p>
    <div className={styles.checks}>{capability.checks.map(check => <article className={styles.check} key={check.id}>
      <span className={`${styles.validationBadge} ${check.status === "passed" ? "" : styles.validationPending}`}>{check.id} · {check.status === "passed" ? "Vérifié" : "À vérifier"}</span>
      <h3>{check.title}</h3><p>{check.procedure}</p><small>{check.evidence}</small>
    </article>)}</div>
    <div className={styles.note}><strong>Portée des preuves</strong><ul>{capability.limitations.map(item => <li key={item}>{item}</li>)}</ul></div>
  </section>;
}
