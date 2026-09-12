import audit from "@/data/radar-audit.json";

export function auditMarkdown() {
  const statusLabel: Record<string, string> = { partial: "Partiel", missing: "À construire", verified: "Validé" };
  return [
    "# RadarOS V2 — état du projet et couverture du brief",
    `Audit : ${audit.date} · code ${audit.baseline}`, `Source : ${audit.repository}`, `Board : ${audit.boardUrl}`,
    "", "## État de reprise", ...Object.values(audit.runtime),
    "", "## Fondations prioritaires", ...audit.risks.flatMap(item => [
      `### ${item.id} — ${item.title}`, item.priority, item.detail, ...item.acceptance.map(x => `- [ ] ${x}`), `Ticket : ${item.issueUrl}`, ""
    ]),
    ...audit.items.flatMap(item => [
      `## ${item.id} — ${item.title}`, `${statusLabel[item.status]} · ${item.priority} · §${item.section}`,
      `Existant : ${item.existing}`, "", "À compléter :", ...item.missing.map(x => `- ${x}`), "",
      "Acceptation :", ...item.acceptance.map(x => `- [ ] ${x}`), `Dépendances : ${item.dependencies}`,
      "Preuves code :", ...item.evidence.map(path => `- [${path}](${audit.repository}/tree/${audit.baseline}/${path})`),
      `Ticket : ${item.issueUrl}`, ""
    ]),
    "## Regard croisé", audit.review.status, ...audit.review.summary.map(x => `- ${x}`),
    "", "## Arbitrages ouverts", ...audit.decisions.map(x => `- ${x}`)
  ].join("\n");
}
