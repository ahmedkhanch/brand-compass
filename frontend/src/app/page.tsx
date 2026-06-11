"use client";

import Navbar from "@/components/Navbar";
import Link from "next/link";
import { useI18n } from "@/lib/i18n";

const FEATURE_KEYS = [
  "feat.positioning",
  "feat.scoring",
  "feat.competitive",
  "feat.swot",
  "feat.reco",
  "feat.progress",
];

export default function Home() {
  const { t } = useI18n();
  return (
    <>
      <Navbar />
      <main>
        <section className="max-w-4xl mx-auto px-4 pt-24 pb-16 text-center">
          <h1 className="text-5xl font-bold tracking-tight mb-4">{t("home.heroTitle")}</h1>
          <p className="text-lg text-zinc-400 max-w-2xl mx-auto mb-8">{t("home.heroSubtitle")}</p>
          <div className="flex gap-4 justify-center">
            <Link href="/dashboard" className="bg-emerald-500 hover:bg-emerald-400 text-black font-semibold px-6 py-3 rounded-lg transition">
              {t("home.ctaStart")}
            </Link>
            <Link href="/pricing" className="border border-zinc-700 hover:border-zinc-500 text-zinc-300 px-6 py-3 rounded-lg transition">
              {t("home.ctaPricing")}
            </Link>
          </div>
        </section>

        <section className="max-w-5xl mx-auto px-4 pb-24">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {FEATURE_KEYS.map((k) => (
              <div key={k} className="border border-zinc-800 rounded-xl p-6 hover:border-zinc-700 transition">
                <h3 className="font-semibold mb-2">{t(`${k}.t`)}</h3>
                <p className="text-sm text-zinc-400">{t(`${k}.d`)}</p>
              </div>
            ))}
          </div>
        </section>
      </main>
    </>
  );
}
