"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import { getSubscription, getCredits, createPortal } from "@/lib/api";

export default function SettingsPage() {
  const { getToken, isSignedIn } = useAuth();
  const [sub, setSub] = useState<any>(null);
  const [credits, setCredits] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isSignedIn) return;
    const load = async () => {
      const token = await getToken();
      const [subRes, credRes] = await Promise.all([
        getSubscription(token),
        getCredits(token),
      ]);
      setSub(subRes.data);
      setCredits(credRes.data);
      setLoading(false);
    };
    load();
  }, [isSignedIn, getToken]);

  const handlePortal = async () => {
    const token = await getToken();
    const res = await createPortal(token);
    if (res.data?.portal_url) {
      window.location.href = res.data.portal_url;
    }
  };

  if (!isSignedIn) {
    return <><Navbar /><div className="max-w-lg mx-auto px-4 pt-24 text-center text-zinc-400">Sign in to view settings.</div></>;
  }

  return (
    <>
      <Navbar />
      <main className="max-w-lg mx-auto px-4 pt-12 pb-16">
        <h1 className="text-2xl font-bold mb-8">Settings</h1>

        {loading ? (
          <p className="text-zinc-500">Loading...</p>
        ) : (
          <div className="space-y-6">
            {/* Subscription */}
            <div className="border border-zinc-800 rounded-xl p-6">
              <h3 className="font-semibold mb-4">Subscription</h3>
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-lg font-bold capitalize">{sub?.tier || "boussole"}</p>
                  <p className="text-sm text-zinc-500">{sub?.tier_label || "Boussole"} Plan</p>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  sub?.status === "active" ? "bg-emerald-900/50 text-emerald-300" : "bg-red-900/50 text-red-300"
                }`}>
                  {sub?.status || "active"}
                </span>
              </div>
              <button
                onClick={handlePortal}
                className="mt-4 w-full border border-zinc-600 hover:border-zinc-400 text-zinc-200 py-2 rounded-lg text-sm transition"
              >
                Manage Billing
              </button>
            </div>

            {/* Credits */}
            <div className="border border-zinc-800 rounded-xl p-6">
              <h3 className="font-semibold mb-4">Credits</h3>
              <p className="text-3xl font-bold">{credits?.balance ?? "?"}</p>
              <p className="text-sm text-zinc-500">reports remaining this month</p>
            </div>

            <Link
              href="/pricing"
              className="block text-center border border-emerald-700 hover:border-emerald-500 text-emerald-400 py-3 rounded-lg text-sm transition"
            >
              Upgrade Plan →
            </Link>
          </div>
        )}
      </main>
    </>
  );
}
