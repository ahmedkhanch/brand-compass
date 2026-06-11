"use client";

import { Suspense, useEffect, useState } from "react";
import { useAuth } from "@/lib/clerk-shim";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import Navbar from "@/components/Navbar";
import StatusBadge from "@/components/StatusBadge";
import { listReports, getCredits, upgradeSubscription } from "@/lib/api";

interface ReportItem {
  id: string;
  brand_name: string;
  status: string;
  scores: { seo: number; geo: number; overall: number } | null;
  created_at: string;
}

function DashboardInner() {
  const { getToken, isSignedIn } = useAuth();
  const searchParams = useSearchParams();
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [credits, setCredits] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [upgradeMsg, setUpgradeMsg] = useState<string | null>(null);

  // Auto-upgrade on successful Stripe checkout redirect
  useEffect(() => {
    const checkoutSuccess = searchParams.get("checkout");
    const tier = searchParams.get("tier");
    if (checkoutSuccess === "success" && tier && isSignedIn) {
      const upgrade = async () => {
        const token = await getToken();
        await upgradeSubscription(tier, token);
        setUpgradeMsg(`Successfully upgraded to ${tier}!`);
        window.history.replaceState({}, "", "/dashboard");
      };
      upgrade();
    }
  }, [searchParams, isSignedIn, getToken]);

  useEffect(() => {
    if (!isSignedIn) return;
    const load = async () => {
      const token = await getToken();
      const [reportsRes, creditsRes] = await Promise.all([
        listReports(1, 50, token),
        getCredits(token).catch(() => ({ data: { balance: "?" } })),
      ]);
      setReports(reportsRes.data?.reports || []);
      setCredits(creditsRes.data?.balance ?? null);
      setLoading(false);
    };
    load();
  }, [isSignedIn, getToken]);

  if (!isSignedIn) {
    return (
      <>
        <Navbar />
        <div className="max-w-lg mx-auto px-4 pt-24 text-center">
          <h1 className="text-2xl font-bold mb-4">Sign in to view your dashboard</h1>
          <p className="text-zinc-400">Create an account to start analyzing brands.</p>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <main className="max-w-4xl mx-auto px-4 pt-8 pb-16">
        {upgradeMsg && (
          <div className="mb-6 p-4 border border-emerald-700 bg-emerald-950/30 rounded-lg text-emerald-300 text-sm">
            {upgradeMsg}
          </div>
        )}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold">Dashboard</h1>
            {credits !== null && (
              <p className="text-sm text-zinc-500">{credits} credits remaining</p>
            )}
          </div>
          <Link
            href="/analyze"
            className="bg-emerald-500 hover:bg-emerald-400 text-black font-semibold px-4 py-2 rounded-lg transition text-sm"
          >
            + New Analysis
          </Link>
        </div>

        {loading ? (
          <p className="text-zinc-500">Loading reports...</p>
        ) : reports.length === 0 ? (
          <div className="text-center py-16 border border-zinc-800 rounded-xl">
            <p className="text-zinc-400 mb-4">No reports yet</p>
            <Link href="/analyze" className="text-emerald-400 hover:underline text-sm">
              Run your first brand analysis →
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {reports.map((r) => (
              <Link
                key={r.id}
                href={`/reports/${r.id}`}
                className="block border border-zinc-800 rounded-xl p-5 hover:border-zinc-700 transition"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold">{r.brand_name || "Untitled"}</h3>
                    <p className="text-xs text-zinc-500">
                      {r.created_at ? new Date(r.created_at).toLocaleDateString() : ""}
                    </p>
                  </div>
                  <div className="flex items-center gap-4">
                    {r.scores && (
                      <div className="text-right">
                        <span className="text-lg font-bold">{r.scores.overall}</span>
                        <span className="text-zinc-500 text-xs">/100</span>
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
    <Suspense fallback={<div className="max-w-4xl mx-auto px-4 pt-24 text-zinc-500">Loading...</div>}>
      <DashboardInner />
    </Suspense>
  );
}
