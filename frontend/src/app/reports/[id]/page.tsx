"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/clerk-shim";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import StatusBadge from "@/components/StatusBadge";
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

export default function ReportPage() {
  const { id } = useParams<{ id: string }>();
  const { getToken, isSignedIn } = useAuth();
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

      // Load Meta Ads AFTER report renders — non-blocking
      if (subRes?.data?.tier !== "boussole") {
        getMetaAds(id, token)
          .then((mr) => setMetaAds(mr?.data || null))
          .catch(() => {});
      }
    };
    load();
  }, [id, isSignedIn, getToken]);

  if (loading) return <><Navbar /><div className="max-w-4xl mx-auto px-4 pt-12 text-zinc-500">Loading report...</div></>;
  if (!report) return <><Navbar /><div className="max-w-4xl mx-auto px-4 pt-12 text-red-400">Report not found</div></>;

  const p = report.payload || {};
  const scores = report.scores;

  return (
    <>
      <Navbar />
      <main className="max-w-4xl mx-auto px-4 pt-8 pb-16">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <button onClick={() => router.back()} className="text-sm text-zinc-500 hover:text-white mb-2">
              ← Back
            </button>
            <h1 className="text-2xl font-bold">
              {p.brand || "Brand"} Report
            </h1>
            <div className="flex items-center gap-3 mt-1">
              <StatusBadge status={report.status} />
              {scores && (
                <span className="text-lg font-bold">
                  Overall: {scores.overall}<span className="text-zinc-500 text-sm">/100</span>
                </span>
              )}
            </div>
          </div>
          {scores && (
            <div className="flex gap-6 text-center">
              <div>
                <div className="text-2xl font-bold text-emerald-400">{scores.seo}</div>
                <div className="text-xs text-zinc-500">SEO</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-blue-400">{scores.geo}</div>
                <div className="text-xs text-zinc-500">GEO</div>
              </div>
            </div>
          )}
        </div>

        {report.status === "running" && (
          <div className="mb-8 p-5 border border-blue-800 bg-blue-950/30 rounded-xl text-center">
            <div className="animate-pulse text-blue-300">Pipeline running... Refresh to check progress.</div>
          </div>
        )}

        {report.status === "failed" && (
          <div className="mb-8 p-5 border border-red-800 bg-red-950/30 rounded-xl">
            <p className="text-red-400">{report.error_message || "Analysis failed"}</p>
          </div>
        )}

        {/* Sections */}
        <div className="space-y-6">
          {/* Positioning */}
          {p.positioning && !p.positioning.error && (
            <Section title="Brand Positioning">
              <Row label="Archetype" value={p.positioning.archetype} />
              <Row label="Value Proposition" value={p.positioning.value_proposition} />
              <Row label="Target Audience" value={p.positioning.target_audience} />
              {p.positioning.brand_voice && (
                <Row label="Brand Voice" value={p.positioning.brand_voice.join(", ")} />
              )}
              {p.positioning.differentiators && (
                <Row label="Differentiators" value={p.positioning.differentiators.join(" • ")} />
              )}
            </Section>
          )}

          {/* SWOT */}
          {p.swot && !p.swot.error && (
            <Section title="SWOT Analysis">
              {p.swot.executive_summary && (
                <p className="text-sm text-zinc-400 mb-3 italic">{p.swot.executive_summary}</p>
              )}
              <TagList label="Strengths" items={p.swot.strengths} color="emerald" />
              <TagList label="Weaknesses" items={p.swot.weaknesses} color="red" />
              <TagList label="Opportunities" items={p.swot.opportunities} color="blue" />
              <TagList label="Threats" items={p.swot.threats} color="amber" />
            </Section>
          )}

          {/* Competitive */}
          {p.competitive && !p.competitive.error && (
            <Section title="Competitive Landscape">
              <Row label="Market Position" value={p.competitive.market_position} />
              <Row label="Differentiator" value={p.competitive.brand_differentiator} />
              <Row label="Advantage" value={p.competitive.competitive_advantage} />
              {p.competitive.direct_competitors && (
                <div className="mt-3 space-y-2">
                  {p.competitive.direct_competitors.map((c: any, i: number) => (
                    <div key={i} className="flex items-center justify-between border border-zinc-800 rounded-lg p-3">
                      <div>
                        <span className="font-medium">{c.name}</span>
                        <p className="text-xs text-zinc-500">{c.positioning}</p>
                      </div>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        c.threat_level === "high" ? "bg-red-900/50 text-red-300" :
                        c.threat_level === "medium" ? "bg-amber-900/50 text-amber-300" :
                        "bg-zinc-700 text-zinc-300"
                      }`}>{c.threat_level}</span>
                    </div>
                  ))}
                </div>
              )}
            </Section>
          )}

          {/* SEO */}
          {p.seo && !p.seo.error && (
            <Section title={`SEO Score: ${p.seo.score}/100 — ${p.seo.label}`}>
              <div className="grid grid-cols-4 gap-4 text-center">
                {p.seo.breakdown && Object.entries(p.seo.breakdown).map(([k, v]) => (
                  <div key={k} className="bg-zinc-900 rounded-lg p-3">
                    <div className="text-lg font-bold">{v as number}</div>
                    <div className="text-xs text-zinc-500 capitalize">{k.replace(/_/g, " ")}</div>
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* GEO */}
          {p.geo && !p.geo.error && (
            <Section title={`GEO Score: ${p.geo.score}/100 — ${p.geo.label}`}>
              <div className="grid grid-cols-3 gap-4 text-center">
                {p.geo.breakdown && Object.entries(p.geo.breakdown).map(([k, v]) => (
                  <div key={k} className="bg-zinc-900 rounded-lg p-3">
                    <div className="text-lg font-bold">{v as number}</div>
                    <div className="text-xs text-zinc-500 capitalize">{k}</div>
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* Recommendations */}
          {p.recommendations && !p.recommendations.error && (
            <Section title="Actionable Recommendations">
              {p.recommendations.priority_focus && (
                <p className="text-sm text-emerald-300 mb-3 font-medium">Priority: {p.recommendations.priority_focus}</p>
              )}
              {p.recommendations.quick_wins && (
                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-zinc-300 mb-2">Quick Wins</h4>
                  {p.recommendations.quick_wins.map((w: any, i: number) => (
                    <div key={i} className="flex justify-between border-b border-zinc-800 py-2 text-sm">
                      <span>{w.action}</span>
                      <span className="text-zinc-500">{w.impact} / {w.effort}</span>
                    </div>
                  ))}
                </div>
              )}
              {p.recommendations.strategic_moves && (
                <div>
                  <h4 className="text-sm font-semibold text-zinc-300 mb-2">Strategic Moves</h4>
                  {p.recommendations.strategic_moves.map((m: any, i: number) => (
                    <div key={i} className="flex justify-between border-b border-zinc-800 py-2 text-sm">
                      <span>{m.action}</span>
                      <span className="text-zinc-500">{m.timeframe}</span>
                    </div>
                  ))}
                </div>
              )}
            </Section>
          )}

          {/* Meta Ads — gated */}
          <Section title="Meta Ads Analysis">
            {tier === "boussole" ? (
              <div className="relative">
                <div className="blur-sm pointer-events-none opacity-50">
                  <p className="text-zinc-400">Meta Ads data is available on Radar tier and above.</p>
                  <p className="text-zinc-500 text-sm mt-1">Includes Facebook & Instagram ad library analysis.</p>
                </div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center bg-zinc-900/90 p-6 rounded-xl border border-zinc-700">
                    <p className="text-lg font-semibold mb-2">Upgrade to Radar</p>
                    <p className="text-sm text-zinc-400 mb-3">$199/mo — 100 reports, Meta Ads, history</p>
                    <Link
                      href="/pricing"
                      className="bg-emerald-500 hover:bg-emerald-400 text-black font-medium px-4 py-2 rounded-lg text-sm transition"
                    >
                      Upgrade Now
                    </Link>
                  </div>
                </div>
              </div>
            ) : metaAds?.meta_ads && typeof metaAds.meta_ads === "object" ? (
              <div className="space-y-3">
                <p className="text-sm text-zinc-400">
                  {metaAds.meta_ads.total_ads_found} active ads found for {metaAds.meta_ads.brand_name}
                </p>
                {metaAds.meta_ads.ads?.map((ad: any, i: number) => (
                  <div key={i} className="border border-zinc-800 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-sm">{ad.page_name || "Unknown"}</span>
                      <span className="text-xs text-zinc-500">{ad.media_type || "N/A"}</span>
                    </div>
                    <p className="text-sm text-zinc-400 line-clamp-3">
                      {ad.ad_text || ad.ad_creative_text || ad.body || "No ad copy available"}
                    </p>
                    {ad.detected_ctas && ad.detected_ctas.length > 0 && (
                      <div className="flex gap-1.5 mt-2">
                        {ad.detected_ctas.map((cta: string, j: number) => (
                          <span key={j} className="text-xs px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-400">
                            {cta}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : metaAds?.meta_ads ? (
              <p className="text-zinc-400">{String(metaAds.meta_ads)}</p>
            ) : (
              <p className="text-zinc-500">Loading Meta Ads data...</p>
            )}
          </Section>
        </div>
      </main>
    </>
  );
}

// ── Section sub-components ──
function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border border-zinc-800 rounded-xl p-6">
      <h3 className="font-semibold text-lg mb-4">{title}</h3>
      {children}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string | null | undefined }) {
  if (!value) return null;
  return (
    <div className="flex justify-between border-b border-zinc-800/50 py-2 text-sm">
      <span className="text-zinc-500">{label}</span>
      <span className="text-right max-w-xs">{value}</span>
    </div>
  );
}

function TagList({ label, items, color }: { label: string; items?: string[]; color: string }) {
  if (!items || items.length === 0) return null;
  const colorMap: Record<string, string> = {
    emerald: "bg-emerald-950/50 text-emerald-300 border-emerald-800",
    red: "bg-red-950/50 text-red-300 border-red-800",
    blue: "bg-blue-950/50 text-blue-300 border-blue-800",
    amber: "bg-amber-950/50 text-amber-300 border-amber-800",
  };
  return (
    <div className="mt-2">
      <span className="text-xs text-zinc-500">{label}</span>
      <div className="flex flex-wrap gap-1.5 mt-1">
        {items.map((item, i) => (
          <span key={i} className={`text-xs px-2 py-0.5 rounded-full border ${colorMap[color]}`}>
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}
