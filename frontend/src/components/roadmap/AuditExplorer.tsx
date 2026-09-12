"use client";

import { useState } from "react";
import audit from "@/data/radar-audit.json";
import { auditMarkdown } from "@/lib/radar-audit-export";
import styles from "./audit.module.css";

const statusLabel: Record<string, string> = { partial: "Partiel", missing: "À construire", verified: "Validé" };

export default function AuditExplorer() {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const [priority, setPriority] = useState("all");
  const [openIds, setOpenIds] = useState<Set<string>>(new Set());
  const normalized = query.toLocaleLowerCase("fr");
  const items = audit.items.filter(item => (status === "all" || item.status === status) &&
    (priority === "all" || item.priority === priority) &&
    `${item.id} ${item.title} ${item.existing} ${item.missing.join(" ")}`.toLocaleLowerCase("fr").includes(normalized));

  const expanded = items.length > 0 && items.every(item => openIds.has(item.id));

  function download() {
    const text = auditMarkdown();
    const url = URL.createObjectURL(new Blob([text], { type: "text/markdown;charset=utf-8" }));
    const a = document.createElement("a"); a.href = url; a.download = "radaros-v2-couverture-20260912.md"; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  return <section id="couverture" className={styles.section}>
    <div className={styles.sectionHeading}><div><p className={styles.eyebrow}>LE BRIEF, POINT PAR POINT</p><h2>Ce que nous avons. Ce qu’il reste à faire.</h2></div><button onClick={download} className={styles.secondary}>Exporter le listing ↓</button></div>
    <p className={styles.muted}>« Partiel » signifie qu’un socle existe dans le code, avec des écarts à V2. Aucun statut ne constitue une validation de collecte réelle. Ouvre une ligne pour consulter les preuves et les critères de fin.</p>
    <div className={styles.filters}>
      <label>Rechercher<input type="search" value={query} onChange={e => setQuery(e.target.value)} placeholder="Produits, crédits, Shopify…" /></label>
      <label>Couverture<select aria-label="Couverture" value={status} onChange={e => setStatus(e.target.value)}><option value="all">Tous les statuts</option><option value="partial">Partiel</option><option value="missing">À construire</option><option value="verified">Validé</option></select></label>
      <label>Priorité<select aria-label="Priorité" value={priority} onChange={e => setPriority(e.target.value)}><option value="all">Toutes les priorités</option><option value="P0">P0</option><option value="P1">P1</option><option value="P2">P2</option></select></label>
      <button className={styles.secondary} onClick={() => setOpenIds(expanded ? new Set() : new Set(items.map(item => item.id)))}>{expanded ? "Tout replier" : "Tout déplier"}</button>
    </div>
    <p className={styles.resultCount} role="status">{items.length} / {audit.items.length} sections affichées</p>
    {items.length === 0 && <div className={styles.empty}>Aucune section ne correspond à ces filtres.<button onClick={() => { setQuery(""); setStatus("all"); setPriority("all"); }}>Réinitialiser les filtres</button></div>}
    <div className={styles.requirements}>
      {items.map(item => <details key={item.id} open={openIds.has(item.id)} onToggle={event => {
        const isOpen = event.currentTarget.open;
        setOpenIds(previous => {
          if (previous.has(item.id) === isOpen) return previous;
          const next = new Set(previous);
          if (isOpen) next.add(item.id); else next.delete(item.id);
          return next;
        });
      }} id={item.id} className={styles.requirement}>
        <summary><span className={styles.itemId}>{item.id}</span><span className={styles.itemTitle}>{item.title}</span><span className={`${styles.badge} ${item.status === "partial" ? styles.partial : styles.missing}`}>{statusLabel[item.status]}</span><span className={styles.priority}>{item.priority}</span><span className={styles.chevron} aria-hidden="true">+</span></summary>
        <div className={styles.requirementBody}>
          <div className={styles.existing}><h3>Socle existant</h3><p>{item.existing}</p></div>
          <div className={styles.twoColumns}><div><h3>Besoin à compléter</h3><ul>{item.missing.map(x => <li key={x}>{x}</li>)}</ul></div><div><h3>Critères d’acceptation</h3><ul>{item.acceptance.map(x => <li key={x}>{x}</li>)}</ul></div></div>
          <p className={styles.dependencies}><strong>Dépendances :</strong> {item.dependencies}</p>
          <div className={styles.evidence}><strong>Preuves dans le code audité</strong>{item.evidence.map(path => <a key={path} href={`${audit.repository}/tree/${audit.baseline}/${path}`} target="_blank" rel="noreferrer">{path} ↗</a>)}</div>
          {"issueUrl" in item && <a className={styles.ticket} href={String(item.issueUrl)} target="_blank" rel="noreferrer">Ouvrir le ticket de travail ↗</a>}
        </div>
      </details>)}
    </div>
  </section>;
}
