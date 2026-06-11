"use client";

import { useState } from "react";
import { useAuth } from "@/lib/clerk-shim";
import { useI18n } from "@/lib/i18n";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import { analyzeBrand, getReport } from "@/lib/api";

// Scripted progress stages. The demo pipeline returns almost instantly, but a
// real brand analysis takes ~40–90s — so we narrate the actual pipeline steps
// over a believable duration instead of jumping straight to the report. Each
// stage mirrors a real section the backend produces (Firecrawl → positioning →
// SWOT → competitive → SEO → GEO → recommendations → assembly). Labels are i18n
// keys resolved through t().
const PIPELINE_STAGES: { key: string; ms: number }[] = [
  { key: "an.stage1", ms: 3200 },
  { key: "an.stage2", ms: 3600 },
  { key: "an.stage3", ms: 3000 },
  { key: "an.stage4", ms: 3400 },
  { key: "an.stage5", ms: 3800 },
  { key: "an.stage6", ms: 3200 },
  { key: "an.stage7", ms: 2800 },
  { key: "an.stage8", ms: 2000 },
];

// After the scripted stages finish, confirm the report row is actually COMPLETE
// before redirecting (it normally already is, since the mock pipeline is fast).
const POLL_INTERVAL_MS = 1500;
const MAX_POLLS = 20;
const FINAL_FILL_MS = 600;
const ERR_FAILED = "an.errFailed";

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export default function AnalyzePage() {
  const { getToken } = useAuth();
  const { t } = useI18n();
  const router = useRouter();

  const [form, setForm] = useState({
    name: "",
    website_url: "",
    industry: "",
    competitor: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [stageIndex, setStageIndex] = useState(0);
  const [errorKey, setErrorKey] = useState<string | null>(null);

  const stageCount = PIPELINE_STAGES.length;
  const done = stageIndex >= stageCount;
  const pct = done ? 100 : ((stageIndex + 1) / stageCount) * 100;
  const fillMs = done ? FINAL_FILL_MS : PIPELINE_STAGES[stageIndex].ms;
  const label = done ? t("an.ready") : t(PIPELINE_STAGES[stageIndex].key);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name) return;
    setSubmitting(true);
    setErrorKey(null);
    setStageIndex(0);

    try {
      const token = await getToken();
      const res = await analyzeBrand(
        {
          name: form.name,
          website_url: form.website_url,
          industry: form.industry,
          competitor: form.competitor,
        },
        token
      );
      const rid = res.data?.report_id;
      if (!rid) throw new Error("an.errNoId");

      // Narrate the pipeline stages over a realistic duration.
      for (let i = 0; i < stageCount; i++) {
        setStageIndex(i);
        await sleep(PIPELINE_STAGES[i].ms);
      }

      // Ensure the report is ready before navigating.
      let ready = false;
      for (let i = 0; i < MAX_POLLS; i++) {
        try {
          const r = await getReport(rid, token);
          const st = r.data?.status;
          if (st === "complete") {
            ready = true;
            break;
          }
          if (st === "failed") throw new Error(ERR_FAILED);
        } catch (pollErr) {
          if (pollErr instanceof Error && pollErr.message === ERR_FAILED) throw pollErr;
          // transient network error — keep polling
        }
        await sleep(POLL_INTERVAL_MS);
      }
      if (!ready) throw new Error("an.errTimeout");

      setStageIndex(stageCount);
      await sleep(FINAL_FILL_MS);
      router.push(`/reports/${rid}`);
    } catch (err) {
      setErrorKey(err instanceof Error ? err.message : "an.errUnknown");
      setSubmitting(false);
    }
  };

  return (
    <>
      <Navbar />
      <main className="max-w-lg mx-auto px-4 pt-12 pb-16">
        <h1 className="text-2xl font-bold mb-8">{t("an.title")}</h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-zinc-400 mb-1">{t("an.brand")}</label>
            <input
              type="text"
              required
              disabled={submitting}
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-emerald-500 disabled:opacity-50"
              placeholder="Nike"
            />
          </div>
          <div>
            <label className="block text-sm text-zinc-400 mb-1">{t("an.website")}</label>
            <input
              type="url"
              disabled={submitting}
              value={form.website_url}
              onChange={(e) => setForm({ ...form, website_url: e.target.value })}
              className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-emerald-500 disabled:opacity-50"
              placeholder="https://www.nike.com"
            />
          </div>
          <div>
            <label className="block text-sm text-zinc-400 mb-1">{t("an.industry")}</label>
            <input
              type="text"
              disabled={submitting}
              value={form.industry}
              onChange={(e) => setForm({ ...form, industry: e.target.value })}
              className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-emerald-500 disabled:opacity-50"
              placeholder="sportswear"
            />
          </div>
          <div>
            <label className="block text-sm text-zinc-400 mb-1">{t("an.competitor")}</label>
            <input
              type="text"
              disabled={submitting}
              value={form.competitor}
              onChange={(e) => setForm({ ...form, competitor: e.target.value })}
              className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-emerald-500 disabled:opacity-50"
              placeholder="adidas"
            />
          </div>

          <button
            type="submit"
            disabled={submitting || !form.name}
            className="w-full bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 disabled:cursor-not-allowed text-black font-semibold py-3 rounded-lg transition"
          >
            {submitting ? t("an.running") : t("an.start")}
          </button>
        </form>

        {submitting && (
          <div className="mt-8 p-5 border border-zinc-800 rounded-xl bg-zinc-950/40">
            <div className="flex items-center gap-3 mb-4">
              {!done ? (
                <span className="h-4 w-4 rounded-full border-2 border-zinc-600 border-t-emerald-500 animate-spin" />
              ) : (
                <span className="h-4 w-4 rounded-full bg-emerald-500" />
              )}
              <span className="text-sm text-zinc-200">{label}</span>
            </div>

            <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full bg-emerald-500"
                style={{ width: `${pct}%`, transition: `width ${fillMs}ms linear` }}
              />
            </div>

            <div className="mt-3 flex items-center justify-between text-xs text-zinc-500">
              <span>{done ? t("an.doneShort") : t("an.step", { i: stageIndex + 1, n: stageCount })}</span>
              <span>{Math.round(pct)}%</span>
            </div>
          </div>
        )}

        {errorKey && (
          <div className="mt-6 p-4 border border-red-800 bg-red-950/30 rounded-lg">
            <p className="text-sm text-red-400">{t(errorKey)}</p>
          </div>
        )}
      </main>
    </>
  );
}
