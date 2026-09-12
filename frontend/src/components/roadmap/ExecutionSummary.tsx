import execution from "@/data/radar-execution.json";
import styles from "./audit.module.css";

const number = (value: number) => new Intl.NumberFormat("fr-FR").format(value);
export default function ExecutionSummary() {
  return <section className={styles.section} id="execution"><p className={styles.eyebrow}>MODÈLES & CONSOMMATION · {execution.cutoffLabel}</p><h2>Une estimation, puis les mesures.</h2>
    <div className={styles.checks}>{execution.phases.map(phase => <article className={styles.check} key={phase.id}>
      <h3>{phase.title}</h3><p><strong>{phase.model} · {phase.effort}</strong> — {phase.reason}</p>
      <p>Prévision : {phase.estimate}. Mesure : {Math.round(phase.elapsedSeconds)} s · {number(phase.tokens)} tokens, dont {number(phase.cachedInputTokens)} lus depuis le cache.</p>
      <small>{phase.costLabel}</small>
    </article>)}</div><p className={styles.note}>{execution.scope}</p>
  </section>;
}
