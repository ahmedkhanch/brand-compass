"use client";

import { useEffect, useRef, useState } from "react";
import { useAuth } from "@/lib/clerk-shim";
import { useI18n, LangToggle } from "@/lib/i18n";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { getReport, getMetaAds, getSubscription } from "@/lib/api";

interface ReportData {
  id: string;
  status: string;
  scores: { seo: number; geo: number; overall: number } | null;
  payload: any;
  error_message: string | null;
  created_at: string;
  generated_at: string | null;
}

// Brand-themed accent gradients used across gauges and bars.
const ACCENT: Record<string, [string, string]> = {
  overall: ["#6366f1", "#d946ef"],
  seo: ["#10b981", "#06b6d4"],
  geo: ["#f59e0b", "#ec4899"],
};
const COUNT_MS = 1300;
const GAUGE_MAIN = 168;
const GAUGE_SUB = 116;

// ── Animation helpers ──────────────────────────────────────────────
function useInView<T extends HTMLElement>(threshold = 0.2) {
  const ref = useRef<T>(null);
  const [inView, setInView] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      ([e]) => {
        if (e.isIntersecting) {
          setInView(true);
          io.disconnect();
        }
      },
      { threshold }
    );
    io.observe(el);
    return () => io.disconnect();
  }, [threshold]);
  return [ref, inView] as const;
}

function useCountUp(target: number, run: boolean, ms = COUNT_MS) {
  const [v, setV] = useState(0);
  useEffect(() => {
    if (!run) return;
    let raf = 0;
    let start = 0;
    const tick = (ts: number) => {
      if (!start) start = ts;
      const k = Math.min(1, (ts - start) / ms);
      setV(Math.round(target * (1 - Math.pow(1 - k, 3))));
      if (k < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, run, ms]);
  return v;
}

function Reveal({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  const [ref, inView] = useInView<HTMLDivElement>(0.12);
  return (
    <div
      ref={ref}
      style={{
        opacity: inView ? 1 : 0,
        transform: inView ? "none" : "translateY(28px)",
        transition: `opacity .7s ease ${delay}ms, transform .7s cubic-bezier(.22,1,.36,1) ${delay}ms`,
      }}
    >
      {children}
    </div>
  );
}

// ── Charts ─────────────────────────────────────────────────────────
function Gauge({ value, label, accent, size = GAUGE_SUB }: { value: number; label: string; accent: [string, string]; size?: number }) {
  const [ref, inView] = useInView<HTMLDivElement>(0.4);
  const n = useCountUp(value, inView);
  const stroke = size > 140 ? 13 : 10;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - (inView ? value : 0) / 100);
  const gid = `grad-${label.replace(/\W/g, "")}-${size}`;
  return (
    <div ref={ref} className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <defs>
            <linearGradient id={gid} x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor={accent[0]} />
              <stop offset="100%" stopColor={accent[1]} />
            </linearGradient>
          </defs>
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#e2e8f0" strokeWidth={stroke} />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={`url(#${gid})`}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={c}
            strokeDashoffset={offset}
            style={{ transition: "stroke-dashoffset 1.4s cubic-bezier(.22,1,.36,1)" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`${size > 140 ? "text-5xl" : "text-3xl"} font-extrabold tabular-nums text-slate-900`}>{n}</span>
          <span className="text-[10px] font-medium text-slate-400">/ 100</span>
        </div>
      </div>
      <span className="mt-2 text-sm font-semibold text-slate-600">{label}</span>
    </div>
  );
}

function BarRow({ label, value, max, accent }: { label: string; value: number; max: number; accent: [string, string] }) {
  const [ref, inView] = useInView<HTMLDivElement>(0.3);
  const w = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div ref={ref}>
      <div className="flex justify-between text-sm mb-1.5">
        <span className="text-slate-600">{label}</span>
        <span className="font-semibold text-slate-900 tabular-nums">{value}</span>
      </div>
      <div className="h-2.5 rounded-full bg-slate-200/70 overflow-hidden">
        <div
          className="h-full rounded-full"
          style={{
            width: inView ? `${w}%` : 0,
            background: `linear-gradient(90deg, ${accent[0]}, ${accent[1]})`,
            transition: "width 1.1s cubic-bezier(.22,1,.36,1)",
          }}
        />
      </div>
    </div>
  );
}

function CompassRose({ size = 420 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" fill="none" stroke="currentColor" className="text-indigo-700">
      <circle cx="50" cy="50" r="47" strokeWidth="0.5" />
      <circle cx="50" cy="50" r="37" strokeWidth="0.4" />
      <polygon points="50,5 55.5,44.5 94,50 55.5,55.5 50,95 44.5,55.5 6,50 44.5,44.5" strokeWidth="0.6" />
      <polygon points="50,17 52.5,47.5 83,50 52.5,52.5 50,83 47.5,52.5 17,50 47.5,47.5" strokeWidth="0.4" />
      <line x1="50" y1="2" x2="50" y2="98" strokeWidth="0.3" />
      <line x1="2" y1="50" x2="98" y2="50" strokeWidth="0.3" />
    </svg>
  );
}

function Glyph({ depth, className, label }: { depth: string; className: string; label: string }) {
  return (
    <div data-depth={depth} className={`absolute ${className}`}>
      <div className="bc-float text-4xl font-black text-slate-300/60 select-none">{label}</div>
    </div>
  );
}

function ParallaxBackdrop() {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    let raf = 0;
    const onScroll = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const y = window.scrollY;
        const root = ref.current;
        if (!root) return;
        root.querySelectorAll<HTMLElement>("[data-depth]").forEach((node) => {
          const d = parseFloat(node.getAttribute("data-depth") || "0");
          node.style.transform = `translate3d(0, ${(y * d).toFixed(1)}px, 0)`;
        });
      });
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      cancelAnimationFrame(raf);
    };
  }, []);
  return (
    <div ref={ref} aria-hidden className="fixed inset-0 -z-10 overflow-hidden bg-gradient-to-b from-slate-50 via-indigo-50/70 to-fuchsia-50/50">
      <div data-depth="0.15" className="absolute -top-24 -left-24"><div className="bc-float h-80 w-80 rounded-full bg-indigo-300/30 blur-3xl" /></div>
      <div data-depth="0.28" className="absolute top-1/3 -right-28"><div className="bc-float-slow h-96 w-96 rounded-full bg-fuchsia-300/25 blur-3xl" /></div>
      <div data-depth="0.2" className="absolute bottom-0 left-1/4"><div className="bc-float h-72 w-72 rounded-full bg-emerald-300/25 blur-3xl" /></div>
      <div data-depth="0.4" className="absolute top-20 right-[6%] opacity-[0.07]"><div className="bc-spin-slow"><CompassRose size={460} /></div></div>
      <Glyph depth="0.55" className="top-[18%] left-[11%]" label="Aa" />
      <Glyph depth="0.7" className="top-[55%] left-[7%]" label="#" />
      <Glyph depth="0.5" className="top-[40%] right-[13%]" label="“ ”" />
      <div data-depth="0.62" className="absolute bottom-[15%] right-[9%]">
        <div className="bc-float-slow flex gap-1.5">
          <span className="h-5 w-5 rounded bg-indigo-400/50" />
          <span className="h-5 w-5 rounded bg-fuchsia-400/50" />
          <span className="h-5 w-5 rounded bg-emerald-400/50" />
        </div>
      </div>
    </div>
  );
}

// ── Layout primitives ──────────────────────────────────────────────
function Card({ title, children }: { title?: string; children: React.ReactNode }) {
  return (
    <section className="rounded-3xl border border-white/70 bg-white/75 backdrop-blur-xl shadow-[0_14px_50px_-18px_rgba(30,41,59,0.35)] p-6 sm:p-8">
      {title && <h2 className="text-lg font-bold text-slate-900 mb-5">{title}</h2>}
      {children}
    </section>
  );
}

function InfoRow({ label, value }: { label: string; value?: string | null }) {
  if (!value) return null;
  return (
    <div className="flex justify-between gap-4 border-b border-slate-200/70 py-2.5 text-sm">
      <span className="text-slate-500 shrink-0">{label}</span>
      <span className="text-right text-slate-800">{value}</span>
    </div>
  );
}

function Chips({ items, accent }: { items?: string[]; accent: string }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((it, i) => (
        <span key={i} className={`text-xs px-2.5 py-1 rounded-full border ${accent}`}>{it}</span>
      ))}
    </div>
  );
}

function humanize(s: string) {
  return s.replace(/_/g, " ");
}

// ── Page ───────────────────────────────────────────────────────────
export default function ReportPage() {
  const { id } = useParams<{ id: string }>();
  const { getToken, isSignedIn } = useAuth();
  const { t } = useI18n();
  const router = useRouter();
  const [report, setReport] = useState<ReportData | null>(null);
  const [metaAds, setMetaAds] = useState<any>(null);
  const [tier, setTier] = useState<string>("boussole");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isSignedIn) return;
    const load = async () => {
      const token = await getToken();
      const [res, subRes] = await Promise.all([
        getReport(id, token),
        getSubscription(token).catch(() => ({ data: { tier: "boussole" } })),
      ]);
      setReport(res.data);
      setTier(subRes?.data?.tier || "boussole");
      setLoading(false);
      if (subRes?.data?.tier !== "boussole") {
        getMetaAds(id, token).then((mr) => setMetaAds(mr?.data || null)).catch(() => {});
      }
    };
    load();
  }, [id, isSignedIn, getToken]);

  if (loading) {
    return (
      <>
        <ParallaxBackdrop />
        <div className="min-h-screen flex items-center justify-center text-slate-500">
          <span className="h-5 w-5 mr-3 rounded-full border-2 border-slate-300 border-t-indigo-500 animate-spin" />
          {t("r.loading")}
        </div>
      </>
    );
  }
  if (!report) {
    return (
      <>
        <ParallaxBackdrop />
        <div className="min-h-screen flex items-center justify-center text-rose-500">{t("r.notFound")}</div>
      </>
    );
  }

  const p = report.payload || {};
  const scores = report.scores;
  const brand = (p.brand || "Brand") as string;
  const brandTitle = brand.charAt(0).toUpperCase() + brand.slice(1);
  const pos = p.positioning?.positioning || {};

  const seoBreak = (p.seo?.breakdown || {}) as Record<string, number>;
  const geoBreak = (p.geo?.breakdown || {}) as Record<string, number>;
  const seoMax = Math.max(1, ...Object.values(seoBreak));
  const geoMax = Math.max(1, ...Object.values(geoBreak));

  const swotQuads = [
    { key: "swot.s", items: p.swot?.strengths, box: "from-emerald-50 to-emerald-100/30 border-emerald-200", dot: "bg-emerald-500", head: "text-emerald-800" },
    { key: "swot.w", items: p.swot?.weaknesses, box: "from-rose-50 to-rose-100/30 border-rose-200", dot: "bg-rose-500", head: "text-rose-800" },
    { key: "swot.o", items: p.swot?.opportunities, box: "from-sky-50 to-sky-100/30 border-sky-200", dot: "bg-sky-500", head: "text-sky-800" },
    { key: "swot.t", items: p.swot?.threats, box: "from-amber-50 to-amber-100/30 border-amber-200", dot: "bg-amber-500", head: "text-amber-800" },
  ];

  const threatStyle: Record<string, string> = {
    high: "bg-rose-100 text-rose-700 border-rose-200",
    medium: "bg-amber-100 text-amber-700 border-amber-200",
    low: "bg-emerald-100 text-emerald-700 border-emerald-200",
  };
  const tagStyle: Record<string, string> = {
    high: "bg-emerald-100 text-emerald-700 border-emerald-200",
    medium: "bg-amber-100 text-amber-700 border-amber-200",
    low: "bg-slate-100 text-slate-600 border-slate-200",
    days: "bg-emerald-100 text-emerald-700 border-emerald-200",
    weeks: "bg-amber-100 text-amber-700 border-amber-200",
  };

  return (
    <div className="relative min-h-screen text-slate-800">
      <ParallaxBackdrop />

      {/* Sticky light header */}
      <header className="sticky top-0 z-40 border-b border-white/60 bg-white/70 backdrop-blur-xl">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
          <button onClick={() => router.back()} className="text-sm text-slate-500 hover:text-slate-900 transition flex items-center gap-1">
            ← {t("r.back")}
          </button>
          <Link href="/" className="text-base font-bold tracking-tight text-slate-900">
            Brand<span className="text-indigo-600">Compass</span>
          </Link>
          <LangToggle variant="light" />
        </div>
      </header>

      <main className="relative z-0 max-w-5xl mx-auto px-4 py-10 space-y-7">
        {/* Hero */}
        <Reveal>
          <section className="rounded-3xl border border-white/70 bg-white/75 backdrop-blur-xl shadow-[0_20px_60px_-20px_rgba(30,41,59,0.4)] p-6 sm:p-10">
            <div className="flex flex-col md:flex-row md:items-center gap-8">
              <div className="flex-1">
                <p className="text-[11px] font-bold tracking-[0.18em] text-indigo-500 mb-3">{t("r.eyebrow")}</p>
                <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-slate-900 capitalize">{brandTitle}</h1>
                <p className="mt-1 text-slate-500 font-medium">{t("r.titleSuffix")}</p>
                {p.positioning?.value_proposition && (
                  <p className="mt-4 max-w-xl text-slate-600">{p.positioning.value_proposition}</p>
                )}
                <div className="mt-5 flex flex-wrap gap-2">
                  {p.positioning?.archetype && (
                    <span className="text-xs font-semibold px-3 py-1 rounded-full bg-indigo-100 text-indigo-700 border border-indigo-200">{t("pos.archetype")}: {p.positioning.archetype}</span>
                  )}
                  {p.industry && (
                    <span className="text-xs font-semibold px-3 py-1 rounded-full bg-slate-100 text-slate-600 border border-slate-200 capitalize">{t("r.industry")}: {p.industry}</span>
                  )}
                  {p.competitive?.market_position && (
                    <span className="text-xs font-semibold px-3 py-1 rounded-full bg-fuchsia-100 text-fuchsia-700 border border-fuchsia-200 capitalize">{p.competitive.market_position}</span>
                  )}
                </div>
              </div>
              {scores && <Gauge value={scores.overall} label={t("r.overall")} accent={ACCENT.overall} size={GAUGE_MAIN} />}
            </div>
          </section>
        </Reveal>

        {/* Score band */}
        {scores && (
          <Reveal delay={60}>
            <Card>
              <div className="grid grid-cols-3 gap-4 place-items-center">
                <Gauge value={scores.overall} label={t("r.overall")} accent={ACCENT.overall} />
                <Gauge value={scores.seo} label="SEO" accent={ACCENT.seo} />
                <Gauge value={scores.geo} label="GEO" accent={ACCENT.geo} />
              </div>
            </Card>
          </Reveal>
        )}

        {/* Positioning */}
        {p.positioning && !p.positioning.error && (
          <Reveal>
            <Card title={t("sec.positioning")}>
              <div className="grid md:grid-cols-2 gap-8">
                <div>
                  <InfoRow label={t("pos.archetype")} value={p.positioning.archetype} />
                  <InfoRow label={t("pos.valueProp")} value={p.positioning.value_proposition} />
                  <InfoRow label={t("pos.audience")} value={p.positioning.target_audience} />
                  {p.positioning.brand_voice && (
                    <div className="py-3 border-b border-slate-200/70">
                      <span className="text-sm text-slate-500 block mb-2">{t("pos.voice")}</span>
                      <Chips items={p.positioning.brand_voice} accent="bg-indigo-50 text-indigo-700 border-indigo-200" />
                    </div>
                  )}
                  {p.positioning.differentiators && (
                    <div className="py-3">
                      <span className="text-sm text-slate-500 block mb-2">{t("pos.diff")}</span>
                      <Chips items={p.positioning.differentiators} accent="bg-emerald-50 text-emerald-700 border-emerald-200" />
                    </div>
                  )}
                </div>
                {(pos.price_axis || pos.appeal_axis) && (
                  <div>
                    <p className="text-sm font-semibold text-slate-500 mb-3 text-center">{t("pos.mapTitle")}</p>
                    <PositioningMap price={pos.price_axis} appeal={pos.appeal_axis} brand={brandTitle} t={t} />
                  </div>
                )}
              </div>
            </Card>
          </Reveal>
        )}

        {/* SWOT */}
        {p.swot && !p.swot.error && (
          <Reveal>
            <Card title={t("sec.swot")}>
              {p.swot.executive_summary && (
                <p className="text-sm text-slate-500 italic mb-5">{p.swot.executive_summary}</p>
              )}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {swotQuads.map((q) =>
                  q.items && q.items.length > 0 ? (
                    <div key={q.key} className={`rounded-2xl border bg-gradient-to-br ${q.box} p-4`}>
                      <div className="flex items-center gap-2 mb-3">
                        <span className={`h-2.5 w-2.5 rounded-full ${q.dot}`} />
                        <h3 className={`text-sm font-bold ${q.head}`}>{t(q.key)}</h3>
                      </div>
                      <ul className="space-y-1.5">
                        {q.items.map((it: string, i: number) => (
                          <li key={i} className="text-sm text-slate-700 leading-snug">{it}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null
                )}
              </div>
            </Card>
          </Reveal>
        )}

        {/* Competitive */}
        {p.competitive && !p.competitive.error && (
          <Reveal>
            <Card title={t("sec.competitive")}>
              <div className="grid sm:grid-cols-2 gap-3 mb-5">
                <div className="rounded-2xl bg-slate-50 border border-slate-200 p-4">
                  <span className="text-xs font-semibold text-slate-400">{t("comp.differentiator")}</span>
                  <p className="mt-1 text-sm text-slate-700">{p.competitive.brand_differentiator}</p>
                </div>
                <div className="rounded-2xl bg-slate-50 border border-slate-200 p-4">
                  <span className="text-xs font-semibold text-slate-400">{t("comp.advantage")}</span>
                  <p className="mt-1 text-sm text-slate-700">{p.competitive.competitive_advantage}</p>
                </div>
              </div>
              {p.competitive.direct_competitors && (
                <>
                  <p className="text-sm font-semibold text-slate-500 mb-2">{t("comp.directCompetitors")}</p>
                  <div className="space-y-2">
                    {p.competitive.direct_competitors.map((c: any, i: number) => (
                      <div key={i} className="flex items-center justify-between rounded-xl border border-slate-200 bg-white/70 p-3.5">
                        <div className="min-w-0">
                          <span className="font-semibold text-slate-800">{c.name}</span>
                          <p className="text-xs text-slate-500 truncate">{c.positioning}</p>
                        </div>
                        <span className={`shrink-0 text-xs font-semibold px-2.5 py-1 rounded-full border ${threatStyle[c.threat_level] || threatStyle.low}`}>
                          {t(`threat.${c.threat_level}`)}
                        </span>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </Card>
          </Reveal>
        )}

        {/* SEO + GEO */}
        <div className="grid md:grid-cols-2 gap-7">
          {p.seo && !p.seo.error && (
            <Reveal>
              <Card title={`${t("sec.seo")} — ${p.seo.label}`}>
                <div className="flex items-center gap-6">
                  <Gauge value={p.seo.score} label="SEO" accent={ACCENT.seo} />
                  <div className="flex-1 space-y-3">
                    {Object.entries(seoBreak).map(([k, v]) => (
                      <BarRow key={k} label={t(`bk.${k}`)} value={v} max={seoMax} accent={ACCENT.seo} />
                    ))}
                  </div>
                </div>
              </Card>
            </Reveal>
          )}
          {p.geo && !p.geo.error && (
            <Reveal delay={60}>
              <Card title={`${t("sec.geo")} — ${p.geo.label}`}>
                <div className="flex items-center gap-6">
                  <Gauge value={p.geo.score} label="GEO" accent={ACCENT.geo} />
                  <div className="flex-1 space-y-3">
                    {Object.entries(geoBreak).map(([k, v]) => (
                      <BarRow key={k} label={t(`bk.${k}`)} value={v} max={geoMax} accent={ACCENT.geo} />
                    ))}
                  </div>
                </div>
              </Card>
            </Reveal>
          )}
        </div>

        {/* Recommendations */}
        {p.recommendations && !p.recommendations.error && (
          <Reveal>
            <Card title={t("sec.reco")}>
              {p.recommendations.priority_focus && (
                <div className="rounded-2xl bg-gradient-to-r from-indigo-50 to-fuchsia-50 border border-indigo-100 p-4 mb-5">
                  <span className="text-xs font-bold text-indigo-500 uppercase tracking-wide">{t("reco.priority")}</span>
                  <p className="mt-1 text-sm text-slate-700">{p.recommendations.priority_focus}</p>
                </div>
              )}
              <div className="grid md:grid-cols-2 gap-6">
                {p.recommendations.quick_wins && (
                  <div>
                    <h3 className="text-sm font-bold text-slate-700 mb-3">{t("reco.quickWins")}</h3>
                    <div className="space-y-2">
                      {p.recommendations.quick_wins.map((w: any, i: number) => (
                        <div key={i} className="rounded-xl border border-slate-200 bg-white/70 p-3">
                          <p className="text-sm text-slate-700">{w.action}</p>
                          <div className="flex gap-1.5 mt-2">
                            <span className={`text-[11px] px-2 py-0.5 rounded-full border ${tagStyle[w.impact] || tagStyle.low}`}>{t("reco.impact")}: {w.impact}</span>
                            <span className={`text-[11px] px-2 py-0.5 rounded-full border ${tagStyle[w.effort] || tagStyle.low}`}>{t("reco.effort")}: {w.effort}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {p.recommendations.strategic_moves && (
                  <div>
                    <h3 className="text-sm font-bold text-slate-700 mb-3">{t("reco.strategic")}</h3>
                    <div className="space-y-2">
                      {p.recommendations.strategic_moves.map((m: any, i: number) => (
                        <div key={i} className="rounded-xl border border-slate-200 bg-white/70 p-3 flex items-start justify-between gap-3">
                          <p className="text-sm text-slate-700">{m.action}</p>
                          <span className="shrink-0 text-[11px] px-2 py-0.5 rounded-full border border-slate-200 bg-slate-50 text-slate-500">{m.timeframe}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </Card>
          </Reveal>
        )}

        {/* Meta Ads — gated */}
        <Reveal>
          <Card title={t("sec.metaads")}>
            {tier === "boussole" ? (
              <div className="relative overflow-hidden rounded-2xl">
                <div className="blur-sm pointer-events-none opacity-60 p-2">
                  <p className="text-slate-500">{t("meta.locked")}</p>
                  <p className="text-slate-400 text-sm mt-1">{t("meta.lockedSub")}</p>
                </div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center bg-white/90 backdrop-blur p-6 rounded-2xl border border-slate-200 shadow-lg">
                    <p className="text-lg font-bold text-slate-900 mb-1">{t("meta.upgradeTitle")}</p>
                    <p className="text-sm text-slate-500 mb-3">{t("meta.upgradePrice")}</p>
                    <Link href="/pricing" className="inline-block bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-4 py-2 rounded-lg text-sm transition">
                      {t("meta.upgradeNow")}
                    </Link>
                  </div>
                </div>
              </div>
            ) : metaAds?.meta_ads && typeof metaAds.meta_ads === "object" ? (
              <div className="space-y-3">
                <p className="text-sm text-slate-500">{t("meta.adsFound", { n: metaAds.meta_ads.total_ads_found, brand: metaAds.meta_ads.brand_name })}</p>
                {metaAds.meta_ads.ads?.map((ad: any, i: number) => (
                  <div key={i} className="rounded-xl border border-slate-200 bg-white/70 p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold text-sm text-slate-800">{ad.page_name || "—"}</span>
                      <span className="text-xs text-slate-400">{ad.media_type || "N/A"}</span>
                    </div>
                    <p className="text-sm text-slate-600 line-clamp-3">{ad.ad_text || ad.ad_creative_text || ad.body || "—"}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-400 text-sm">{t("meta.loading")}</p>
            )}
          </Card>
        </Reveal>

        {/* Footer */}
        <div className="pt-2 pb-6 flex items-center justify-between text-xs text-slate-400">
          <span>
            {report.generated_at ? `${t("r.generatedOn")} ${new Date(report.generated_at).toLocaleDateString()}` : ""}
          </span>
          <span className="font-medium">{t("r.poweredBy")}</span>
        </div>
      </main>
    </div>
  );
}

function PositioningMap({ price, appeal, brand, t }: { price?: string; appeal?: string; brand: string; t: (k: string) => string }) {
  const [ref, inView] = useInView<HTMLDivElement>(0.3);
  const x = appeal === "emotional" ? 27 : 73;
  const y = price === "premium" ? 27 : 73;
  return (
    <div ref={ref}>
      <div className="relative aspect-square w-full max-w-[18rem] mx-auto rounded-2xl border border-slate-200 bg-gradient-to-br from-slate-50 to-indigo-50/40">
        <div className="absolute left-1/2 top-0 bottom-0 w-px bg-slate-200" />
        <div className="absolute top-1/2 left-0 right-0 h-px bg-slate-200" />
        <span className="absolute top-2 left-1/2 -translate-x-1/2 text-[10px] font-semibold text-slate-400">{t("pos.premium")}</span>
        <span className="absolute bottom-2 left-1/2 -translate-x-1/2 text-[10px] font-semibold text-slate-400">{t("pos.value")}</span>
        <span className="absolute left-2 top-1/2 -translate-y-1/2 text-[10px] font-semibold text-slate-400">{t("pos.emotional")}</span>
        <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] font-semibold text-slate-400">{t("pos.rational")}</span>
        <div
          className="absolute"
          style={{ left: `${x}%`, top: `${y}%`, transform: "translate(-50%,-50%)", opacity: inView ? 1 : 0, transition: "opacity .6s ease .25s" }}
        >
          <span className="absolute inset-0 -m-1 rounded-full bg-indigo-400/40 animate-ping" />
          <span className="relative block h-4 w-4 rounded-full bg-gradient-to-br from-indigo-500 to-fuchsia-500 ring-4 ring-white shadow" />
          <span className="absolute left-1/2 -translate-x-1/2 top-full mt-1.5 whitespace-nowrap text-[11px] font-bold text-slate-700 capitalize">{brand}</span>
        </div>
      </div>
    </div>
  );
}
