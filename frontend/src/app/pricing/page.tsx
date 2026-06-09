"use client";

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import Navbar from "@/components/Navbar";
import { createCheckout } from "@/lib/api";

const TIERS = [
  {
    name: "Boussole",
    price: "$99",
    priceId: "boussole",
    reports: "25/month",
    features: ["Brand Positioning", "SWOT Analysis", "Competitive Landscape", "SEO Score", "GEO Score", "Recommendations"],
    highlighted: false,
  },
  {
    name: "Radar",
    price: "$199",
    priceId: "radar",
    reports: "100/month",
    features: ["Everything in Boussole", "Meta Ads Analysis", "Report History", "Export to PDF", "Priority Support"],
    highlighted: true,
  },
  {
    name: "Stratège",
    price: "$499",
    priceId: "stratege",
    reports: "500/month",
    features: ["Everything in Radar", "Competitive Alerts", "API Access", "White-Label Reports", "Dedicated Analyst"],
    highlighted: false,
  },
];

export default function PricingPage() {
  const { getToken, isSignedIn } = useAuth();
  const [loading, setLoading] = useState<string | null>(null);

  const handleUpgrade = async (tier: string) => {
    setLoading(tier);
    try {
      const token = await getToken();
      const res = await createCheckout(tier, token);
      if (res.data?.checkout_url) {
        window.location.href = res.data.checkout_url;
      }
    } catch (err: any) {
      alert("Checkout error: " + err.message);
    } finally {
      setLoading(null);
    }
  };

  return (
    <>
      <Navbar />
      <main className="max-w-5xl mx-auto px-4 pt-12 pb-16">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold mb-2">Simple Pricing</h1>
          <p className="text-zinc-400">Choose the plan that fits your brand intelligence needs</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {TIERS.map((tier) => (
            <div
              key={tier.name}
              className={`border rounded-xl p-6 flex flex-col ${
                tier.highlighted
                  ? "border-emerald-600 bg-emerald-950/20"
                  : "border-zinc-800"
              }`}
            >
              {tier.highlighted && (
                <div className="text-xs text-emerald-400 font-semibold mb-2">Most Popular</div>
              )}
              <h3 className="text-xl font-bold">{tier.name}</h3>
              <div className="mt-2 mb-4">
                <span className="text-3xl font-bold">{tier.price}</span>
                <span className="text-zinc-500">/month</span>
              </div>
              <p className="text-sm text-zinc-400 mb-4">{tier.reports}</p>
              <ul className="space-y-2 mb-6 flex-1">
                {tier.features.map((f) => (
                  <li key={f} className="text-sm flex items-center gap-2">
                    <span className="text-emerald-400">✓</span>
                    <span className="text-zinc-300">{f}</span>
                  </li>
                ))}
              </ul>
              <button
                onClick={() => handleUpgrade(tier.priceId)}
                disabled={loading === tier.priceId || !isSignedIn}
                className={`w-full py-2.5 rounded-lg font-semibold text-sm transition ${
                  tier.highlighted
                    ? "bg-emerald-500 hover:bg-emerald-400 text-black"
                    : "border border-zinc-600 hover:border-zinc-400 text-zinc-200"
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {loading === tier.priceId ? "Redirecting..." : isSignedIn ? "Upgrade" : "Sign In to Upgrade"}
              </button>
            </div>
          ))}
        </div>
      </main>
    </>
  );
}
