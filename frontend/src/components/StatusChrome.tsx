"use client";

import Link from "next/link";

// Shared "paper" theme for the status pages (/wip roadmap + /cr compte-rendu).
// Ported from the opti-mutuelle wip/cr format the project owner asked to match:
// warm off-white, blue accent, numbered phase cards, clickable agenda.
// All selectors are scoped under `.paper` so the app's global Tailwind base
// (body.bg-transparent) never clobbers the theme and vice-versa.
export const STATUS_CSS = `
.paper {
  --bg:#f5f3f0; --panel:#ffffff; --border:#d4d0ca; --txt:#1a1a1a;
  --muted:#5e5a55; --accent:#1a6fd4; --accent-light:#8fbdf0; --green:#1b7a30;
  --red:#c72e2e; --amber:#b07d10; --done-bg:#e7f5ea; --todo-bg:#fff7e6; --next-bg:#e8f0fb;
  background:var(--bg); color:var(--txt); min-height:100vh;
  font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; font-size:17px; line-height:1.65;
}
.paper * { box-sizing:border-box; }
.paper header { padding:26px 32px; border-bottom:2px solid var(--border); background:var(--panel); }
.paper header h1 { font-size:26px; margin:0 0 6px; font-weight:800; }
.paper header .sub { color:var(--muted); font-size:16px; }
.paper nav { display:flex; gap:10px; padding:16px 32px 0; flex-wrap:wrap; max-width:1100px; margin:0 auto; }
.paper nav a { padding:9px 18px; border:2px solid var(--border); border-radius:9px; text-decoration:none;
  color:var(--txt); font-weight:600; font-size:15px; background:var(--panel); transition:border-color .12s,color .12s; }
.paper nav a:hover { border-color:var(--accent); color:var(--accent); }
.paper nav a.active { background:var(--accent); color:#fff; border-color:var(--accent); }
.paper main { padding:28px 32px; max-width:1100px; margin:0 auto; }
.paper h2.section { font-size:22px; margin:36px 0 16px; padding-bottom:8px; border-bottom:3px solid var(--accent); }

/* vision */
.paper .vision { background:linear-gradient(135deg,#1a6fd4,#1558a8); color:#fff; padding:28px 32px;
  border-radius:14px; margin-bottom:32px; box-shadow:0 4px 16px rgba(26,111,212,.25); }
.paper .vision h2 { margin:0 0 10px; font-size:22px; }
.paper .vision p { margin:6px 0; font-size:17px; opacity:.96; }

/* kpis */
.paper .kpi-row { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:16px; margin:24px 0; }
.paper .kpi { background:var(--panel); border:2px solid var(--border); border-radius:12px; padding:18px 20px; text-align:center; }
.paper .kpi .big { font-size:30px; font-weight:800; color:var(--accent); }
.paper .kpi .lbl { font-size:14px; color:var(--muted); margin-top:4px; }

/* progress */
.paper .progress-bar { background:#e0ddd7; border-radius:20px; height:28px; overflow:hidden; margin:8px 0 4px; border:1px solid var(--border); }
.paper .progress-fill { background:linear-gradient(90deg,#1b7a30,#27a345); height:100%; display:flex;
  align-items:center; justify-content:flex-end; padding-right:14px; color:#fff; font-weight:700; font-size:14px; }
.paper .legend { display:flex; gap:20px; flex-wrap:wrap; margin:10px 0 0; font-size:15px; color:var(--muted); }

/* phase cards */
.paper .phase { background:var(--panel); border:2px solid var(--border); border-radius:12px; padding:0;
  margin-bottom:18px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,.05); }
.paper .phase-head { display:flex; align-items:center; gap:14px; padding:18px 22px; }
.paper .phase-num { width:40px; height:40px; border-radius:50%; display:flex; align-items:center;
  justify-content:center; font-weight:800; font-size:18px; flex-shrink:0; color:#fff; }
.paper .phase-title { font-size:19px; font-weight:700; flex:1; }
.paper .num-done { background:var(--green); }
.paper .num-progress { background:var(--accent); }
.paper .num-todo { background:#bdb8b0; }
.paper .badge { font-size:13px; font-weight:700; padding:5px 13px; border-radius:20px; white-space:nowrap; }
.paper .badge.done { background:var(--done-bg); color:var(--green); border:1px solid #b6e0c0; }
.paper .badge.progress { background:var(--next-bg); color:var(--accent); border:1px solid #b9d3f5; }
.paper .badge.todo { background:var(--todo-bg); color:var(--amber); border:1px solid #ecd9a8; }
.paper .phase-body { padding:0 22px 18px 76px; }
.paper ul.tasks { list-style:none; padding:0; margin:0; }
.paper ul.tasks li { padding:7px 0 7px 30px; position:relative; font-size:16px; line-height:1.5; }
.paper ul.tasks li::before { position:absolute; left:0; top:6px; font-size:17px; }
.paper li.ok::before { content:"✅"; }
.paper li.wip::before { content:"🔄"; }
.paper li.no::before { content:"⬜"; }
.paper li.no { color:var(--muted); }
.paper .meta { font-size:14px; color:var(--muted); margin-top:10px; padding-left:30px; }

/* compte-rendu: summary + stats */
.paper .summary { background:var(--panel); border:2px solid var(--border); border-radius:14px; padding:24px 28px; margin-bottom:30px; box-shadow:0 2px 8px rgba(0,0,0,.05); }
.paper .summary h2 { margin:0 0 12px; font-size:21px; }
.paper .stat-row { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:14px; margin-top:18px; }
.paper .stat { text-align:center; padding:14px; background:#faf9f7; border:1px solid var(--border); border-radius:10px; }
.paper .stat .n { font-size:24px; font-weight:800; color:var(--accent); }
.paper .stat .l { font-size:13px; color:var(--muted); }

/* agenda */
.paper .cal-wrap { background:var(--panel); border:2px solid var(--border); border-radius:14px; padding:22px 26px; box-shadow:0 2px 8px rgba(0,0,0,.05); }
.paper .cal-month-title { font-size:19px; font-weight:700; margin-bottom:14px; text-align:center; }
.paper .cal-days { display:grid; grid-template-columns:repeat(7,1fr); gap:8px; }
.paper .cal-day-header { text-align:center; font-size:13px; font-weight:700; color:var(--muted); padding-bottom:6px; text-transform:uppercase; letter-spacing:.03em; }
.paper .cal-day { aspect-ratio:1; display:flex; align-items:center; justify-content:center; border-radius:10px;
  font-size:16px; font-weight:600; color:var(--muted); background:#faf9f7; border:1px solid #eee; }
.paper .cal-day.empty { background:transparent; border:none; }
.paper .cal-day.has-cra { cursor:pointer; color:#fff; background:var(--accent); border-color:var(--accent);
  box-shadow:0 2px 6px rgba(26,111,212,.3); transition:transform .12s,box-shadow .12s; position:relative; }
.paper .cal-day.has-cra:hover { transform:translateY(-2px); box-shadow:0 5px 14px rgba(26,111,212,.4); }
.paper .cal-day.has-cra.partial { background:var(--accent-light); border-color:var(--accent-light); color:#0d3a6b; box-shadow:0 2px 6px rgba(143,189,240,.4); }
.paper .cal-day.has-cra::after { content:"●"; position:absolute; bottom:3px; font-size:8px; opacity:.85; }
.paper .cal-legend { display:flex; gap:22px; flex-wrap:wrap; margin-top:20px; font-size:14px; color:var(--muted); align-items:center; }
.paper .cal-legend .sw { display:inline-block; width:16px; height:16px; border-radius:5px; vertical-align:middle; margin-right:6px; }
.paper .sw.full { background:var(--accent); }
.paper .sw.half { background:var(--accent-light); }
.paper .hint-click { text-align:center; color:var(--muted); font-size:14px; margin-top:14px; font-style:italic; }

/* modal */
.paper .modal-overlay { position:fixed; inset:0; background:rgba(20,18,16,.55); display:none; align-items:center; justify-content:center; z-index:1000; padding:20px; }
.paper .modal-overlay.open { display:flex; }
.paper .modal { background:var(--bg); border-radius:16px; max-width:760px; width:100%; max-height:88vh; overflow:hidden; display:flex; flex-direction:column; box-shadow:0 20px 60px rgba(0,0,0,.4); }
.paper .modal-head { display:flex; align-items:center; gap:14px; padding:20px 26px; background:var(--panel); border-bottom:2px solid var(--border); }
.paper .modal-head h3 { margin:0; font-size:20px; font-weight:800; flex:1; }
.paper .modal-close { background:none; border:none; font-size:28px; cursor:pointer; color:var(--muted); line-height:1; padding:0 6px; }
.paper .modal-close:hover { color:var(--txt); }
.paper .modal-body { padding:24px 28px; overflow-y:auto; }
.paper .modal-foot { display:flex; justify-content:space-between; padding:14px 26px; background:var(--panel); border-top:1px solid var(--border); }
.paper .mbtn { padding:9px 18px; border:2px solid var(--border); border-radius:9px; background:#fff; cursor:pointer; font-weight:600; font-size:15px; color:var(--txt); }
.paper .mbtn:hover:not(:disabled) { border-color:var(--accent); color:var(--accent); }
.paper .mbtn:disabled { opacity:.35; cursor:not-allowed; }
.paper .day-badge { font-size:13px; font-weight:700; padding:5px 13px; border-radius:20px; }
.paper .day-badge.full { background:#e8f0fb; color:var(--accent); border:1px solid #b9d3f5; }
.paper .entry { position:relative; padding-left:26px; margin-bottom:22px; }
.paper .entry::before { content:""; position:absolute; left:0; top:8px; width:12px; height:12px; border-radius:50%; background:var(--accent); }
.paper .entry h4 { margin:0 0 4px; font-size:17px; font-weight:700; }
.paper .entry .when { font-size:12px; color:var(--muted); font-weight:600; text-transform:uppercase; letter-spacing:.04em; }
.paper .entry ul { margin:8px 0 0; padding-left:20px; }
.paper .entry li { margin:4px 0; font-size:15.5px; }
.paper .meta-line { font-size:14px; color:var(--muted); margin-top:10px; background:#faf9f7; padding:8px 12px; border-radius:8px; border:1px solid var(--border); }
.paper code { background:#f0ede9; padding:2px 7px; border-radius:5px; border:1px solid var(--border); font-size:14px; }
.paper footer { padding:30px 32px; text-align:center; color:var(--muted); font-size:14px; border-top:1px solid var(--border); margin-top:30px; }
`;

const TABS = [
  { href: "/wip", label: "🗺️ Roadmap", key: "roadmap" },
  { href: "/cr", label: "📋 Compte-rendu", key: "cr" },
] as const;

export default function StatusChrome({
  active,
  title,
  sub,
  children,
}: {
  active: "roadmap" | "cr";
  title: string;
  sub: string;
  children: React.ReactNode;
}) {
  return (
    <div className="paper">
      <style dangerouslySetInnerHTML={{ __html: STATUS_CSS }} />
      <header>
        <h1>{title}</h1>
        <div className="sub">{sub}</div>
      </header>
      <nav>
        {TABS.map((tab) => (
          <Link key={tab.key} href={tab.href} className={active === tab.key ? "active" : ""}>
            {tab.label}
          </Link>
        ))}
      </nav>
      <main>{children}</main>
      <footer>
        Brand Compass · document vivant · généré depuis <code>ahmedkhanch/brand-compass</code>
      </footer>
    </div>
  );
}
