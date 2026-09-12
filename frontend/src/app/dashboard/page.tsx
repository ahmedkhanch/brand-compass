"use client";

import { Suspense, useEffect, useState } from "react";
import { useAuth } from "@/lib/clerk-shim";
import { useI18n } from "@/lib/i18n";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import Navbar from "@/components/Navbar";
import StatusBadge from "@/components/StatusBadge";
import { listReports, getCredits, getSubscription } from "@/lib/api";

interface ReportItem {
  id: string;
  brand_name: string;
  status: string;
  scores: { seo: number; geo: number; overall: number } | null;
  created_at: string;
}

function DashboardInner() {
  const { getToken, isSignedIn } = useAuth();
  const { t } = useI18n();
  const searchParams = useSearchParams();
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [credits, setCredits] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [upgradeTier, setUpgradeTier] = useState<string | null>(null);

  // Confirm persisted rights after checkout; the redirect never grants access.
  useEffect(() => {
    const checkoutSuccess = searchParams.get("checkout");
    const tier = searchParams.get("tier");
    if (checkoutSuccess === "success" && tier && isSignedIn) {
      const confirmSubscription = async () => {
        const token = await getToken();
        const subscription = await getSubscription(token);
        if (subscription.data?.status === "active" && subscription.data.tier === tier) {
          setUpgradeTier(subscription.data.tier);
        }
        window.history.replaceState({}, "", "/dashboard");
      };
      confirmSubscription().catch(() => setUpgradeTier(null));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams, isSignedIn]);

  useEffect(() => {
    if (!isSignedIn) return;
    let cancelled = false;
    const load = async () => {
      try {
        const token = await getToken();
        const [reportsRes, creditsRes] = await Promise.all([
          listReports(1, 50, token),
          getCredits(token).catch(() => ({ data: { balance: "?" } })),
        ]);
        if (cancelled) return;
        setReports(reportsRes.data?.reports || []);
        setCredits(creditsRes.data?.balance ?? null);
        setError(null);
      } catch (e: any) {
        if (!cancelled) setError(e?.message || "Failed to load dashboard");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isSignedIn]);

  if (!isSignedIn) {
    return (
      <>
        <Navbar />
        <div className="max-w-lg mx-auto px-4 pt-24 text-center">
          <h1 className="text-2xl font-bold mb-4">{t("dash.signinTitle")}</h1>
          <p className="text-slate-600">{t("dash.signinSub")}</p>
        </div>
      </>
    );
  }

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="max-w-4xl mx-auto px-4 pt-24 flex items-center justify-center text-slate-500">
          <span className="h-5 w-5 mr-3 rounded-full border-2 border-slate-300 border-t-indigo-500 animate-spin" />
          {t("r.loading")}
        </div>
      </>
    );
  }

  if (error) {
    return (
      <>
        <Navbar />
        <div className="max-w-lg mx-auto px-4 pt-24 text-center">
          <p className="text-rose-500 font-semibold mb-2">{error}</p>
          <button onClick={() => { setError(null); setLoading(true); }} className="text-sm text-indigo-600 hover:underline">
            {t("r.retry") || "Retry"}
          </button>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <main className="max-w-4xl mx-auto px-4 pt-8 pb-16">
        {upgradeTier && (
          <div className="mb-6 p-4 border border-emerald-700 bg-emerald-950/30 rounded-lg text-emerald-300 text-sm">
            {t("dash.upgraded", { tier: upgradeTier })}
          </div>
        )}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold">{t("dash.title")}</h1>
            {credits !== null && (
              <p className="text-sm text-slate-500">{t("dash.credits", { n: credits })}</p>
            )}
          </div>
          <Link
            href="/analyze"
            className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-4 py-2 rounded-lg transition text-sm"
          >
            {t("dash.new")}
          </Link>
        </div>

        {loading ? (
          <p className="text-slate-500">{t("dash.loading")}</p>
        ) : reports.length === 0 ? (
          <div className="text-center py-16 border border-slate-200 rounded-xl">
            <p className="text-slate-600 mb-4">{t("dash.empty")}</p>
            <Link href="/analyze" className="text-emerald-600 hover:underline text-sm">
              {t("dash.emptyCta")}
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {reports.map((r) => (
              <Link
                key={r.id}
                href={`/reports/${r.id}`}
                className="block border border-slate-200 rounded-xl p-5 hover:border-slate-300 transition"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold">{r.brand_name || t("dash.untitled")}</h3>
                    <p className="text-xs text-slate-500">
                      {r.created_at ? new Date(r.created_at).toLocaleDateString() : ""}
                    </p>
                  </div>
                  <div className="flex items-center gap-4">
                    {r.scores && (
                      <div className="text-right">
                        <span className="text-lg font-bold">{r.scores.overall}</span>
                        <span className="text-slate-500 text-xs">/100</span>
                      </div>
                    )}
                    <StatusBadge status={r.status} />
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>
    </>
  );
}

export default function Dashboard() {
  return (
    <Suspense fallback={<div className="max-w-4xl mx-auto px-4 pt-24 text-slate-500">…</div>}>
      <DashboardInner />
    </Suspense>
  );
}
