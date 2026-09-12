import Link from "next/link";
import styles from "./audit.module.css";

export default function AuditShell({ children, active = "wip" }: { children: React.ReactNode; active?: "wip" | "tests" }) {
  return <div className={styles.shell}>
    <aside className={styles.sidebar}>
      <Link href="/wip" className={styles.logo}><span className={styles.mark}>◎</span><span>GROWTHOS<small>RadarOS · reprise du projet</small></span></Link>
      <span className={styles.navLabel}>PILOTAGE</span>
      <Link href="/wip" aria-current={active === "wip" ? "page" : undefined}>Vue d’ensemble</Link>
      <Link href="/wip#couverture">Besoins & couverture</Link>
      <Link href="/wip#priorites">Priorités de reprise</Link>
      <Link href="/wip#relecture">Seconde analyse</Link>
      <Link href="/tests" aria-current={active === "tests" ? "page" : undefined}>Validation</Link>
      <div className={styles.sidebarFoot}>Une requête.<br />Une marque.<br /><strong>Des faits, puis des actions.</strong><p>Audit du 12 septembre 2026</p></div>
    </aside>
    <main className={styles.main}>{children}</main>
  </div>;
}
