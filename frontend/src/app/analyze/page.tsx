"use client";

import { useState } from "react";
import { useAuth } from "@/lib/clerk-shim";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import StatusBadge from "@/components/StatusBadge";
import { analyzeBrand, streamReportProgress } from "@/lib/api";

export default function AnalyzePage() {
  const { getToken, isSignedIn } = useAuth();
  const router = useRouter();

  const [form, setForm] = useState({
    name: "",
    website_url: "",
    industry: "",
    competitor: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [reportId, setReportId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name) return;
    setSubmitting(true);
    setError(null);
    setStatus("queued");

    try {
      const token = await getToken();
      const res = await analyzeBrand(
        { name: form.name, website_url: form.website_url, industry: form.industry, competitor: form.competitor },
        token
      );
      const rid = res.data?.report_id;
      if (!rid) throw new Error("No report ID returned");
      setReportId(rid);

      // Start SSE stream
      streamReportProgress(
        rid,
        (s) => setStatus(s),
        () => {
          setSubmitting(false);
          router.push(`/reports/${rid}`);
        },
        (err) => {
          setError(err);
          setSubmitting(false);
        }
      );
    } catch (err: any) {
      setError(err.message);
      setSubmitting(false);
    }
  };

  return (
    <>
      <Navbar />
      <main className="max-w-lg mx-auto px-4 pt-12 pb-16">
        <h1 className="text-2xl font-bold mb-8">New Brand Analysis</h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-zinc-400 mb-1">Brand Name *</label>
            <input
              type="text"
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-emerald-500"
              placeholder="Nike"
            />
          </div>
          <div>
            <label className="block text-sm text-zinc-400 mb-1">Website URL</label>
            <input
              type="url"
              value={form.website_url}
              onChange={(e) => setForm({ ...form, website_url: e.target.value })}
              className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-emerald-500"
              placeholder="https://www.nike.com"
            />
          </div>
          <div>
            <label className="block text-sm text-zinc-400 mb-1">Industry</label>
            <input
              type="text"
              value={form.industry}
              onChange={(e) => setForm({ ...form, industry: e.target.value })}
              className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-emerald-500"
              placeholder="sportswear"
            />
          </div>
          <div>
            <label className="block text-sm text-zinc-400 mb-1">Competitor</label>
            <input
              type="text"
              value={form.competitor}
              onChange={(e) => setForm({ ...form, competitor: e.target.value })}
              className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-emerald-500"
              placeholder="adidas"
            />
          </div>

          <button
            type="submit"
            disabled={submitting || !form.name}
            className="w-full bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 disabled:cursor-not-allowed text-black font-semibold py-3 rounded-lg transition"
          >
            {submitting ? "Analyzing..." : "Start Analysis"}
          </button>
        </form>

        {status && (
          <div className="mt-8 p-5 border border-zinc-800 rounded-xl">
            <div className="flex items-center gap-3 mb-3">
              <StatusBadge status={status} />
              <span className="text-sm text-zinc-400">
                {status === "queued" && "Preparing analysis..."}
                {status === "running" && "Pipeline running — scraping, scoring, analyzing..."}
                {status === "complete" && "Report complete!"}
                {status === "failed" && "Analysis failed"}
              </span>
            </div>
            <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-1000 ${
                  status === "queued" ? "w-1/4 bg-zinc-500" :
                  status === "running" ? "w-3/4 bg-blue-500 animate-pulse" :
                  status === "complete" ? "w-full bg-emerald-500" :
                  "w-full bg-red-500"
                }`}
              />
            </div>
            {reportId && status === "complete" && (
              <p className="mt-3 text-sm text-emerald-400">
                Redirecting to report...
              </p>
            )}
          </div>
        )}

        {error && (
          <div className="mt-6 p-4 border border-red-800 bg-red-950/30 rounded-lg">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}
      </main>
    </>
  );
}
