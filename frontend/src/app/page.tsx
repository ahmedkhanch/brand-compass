"use client";

import Navbar from "@/components/Navbar";
import Link from "next/link";
import { useI18n } from "@/lib/i18n";

// Feature → accent + icon path (same visual language as the report cards).
const FEATURES: { key: string; accent: string; ring: string; icon: string }[] = [
  { key: "feat.positioning", accent: "text-indigo-600", ring: "bg-indigo-50 ring-indigo-100", icon: "M12 3l2.5 5.5L20 9l-4 4 1 6-5-3-5 3 1-6-4-4 5.5-.5z" },
  { key: "feat.scoring", accent: "text-emerald-600", ring: "bg-emerald-50 ring-emerald-100", icon: "M3 17l6-6 4 4 8-8M21 7v6h-6" },
  { key: "feat.competitive", accent: "text-fuchsia-600", ring: "bg-fuchsia-50 ring-fuchsia-100", icon: "M16 8a4 4 0 10-8 0M3 20a6 6 0 0118 0M9 8a4 4 0 108 0" },
  { key: "feat.swot", accent: "text-sky-600", ring: "bg-sky-50 ring-sky-100", icon: "M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z" },
  { key: "feat.reco", accent: "text-amber-600", ring: "bg-amber-50 ring-amber-100", icon: "M9 18h6M10 21h4M12 3a6 6 0 00-4 10.5c.7.6 1 1.2 1 2h6c0-.8.3-1.4 1-2A6 6 0 0012 3z" },
  { key: "feat.progress", accent: "text-violet-600", ring: "bg-violet-50 ring-violet-100", icon: "M13 2L3 14h7l-1 8 10-12h-7l1-8z" },
];

function Backdrop() {
  return (
    <div aria-hidden className="fixed inset-0 -z-10 overflow-hidden bg-gradient-to-b from-white via-white to-indigo-50/40">
      <div className="absolute -top-28 -left-24"><div className="bc-float h-80 w-80 rounded-full bg-indigo-200/30 blur-3xl" /></div>
      <div className="absolute top-1/4 -right-28"><div className="bc-float-slow h-96 w-96 rounded-full bg-fuchsia-200/25 blur-3xl" /></div>
      <div className="absolute bottom-0 left-1/3"><div className="bc-float h-72 w-72 rounded-full bg-sky-200/25 blur-3xl" /></div>
    </div>
  );
}

export default function Home() {
  const { t } = useI18n();
  return (
    <div className="relative min-h-screen text-slate-800">
      <Backdrop />
      <Navbar />

      <main>
        {/* Hero */}
        <section className="max-w-4xl mx-auto px-4 pt-24 pb-20 text-center">
          <p className="bc-rise text-[11px] font-bold tracking-[0.22em] text-indigo-500 uppercase mb-4">
            Brand Compass
          </p>
          <h1
            className="bc-rise text-5xl sm:text-6xl font-extrabold tracking-tight bg-gradient-to-br from-slate-900 via-indigo-800 to-fuchsia-700 bg-clip-text text-transparent leading-[1.05]"
            style={{ animationDelay: "60ms" }}
          >
            {t("home.heroTitle")}
          </h1>
          <p className="bc-rise text-lg text-slate-600 max-w-2xl mx-auto mt-6" style={{ animationDelay: "140ms" }}>
            {t("home.heroSubtitle")}
          </p>
          <div className="bc-rise flex flex-col sm:flex-row gap-3 justify-center mt-9" style={{ animationDelay: "220ms" }}>
            <Link
              href="/dashboard"
              className="inline-flex items-center justify-center gap-2 bg-gradient-to-r from-indigo-600 to-fuchsia-600 hover:from-indigo-500 hover:to-fuchsia-500 text-white font-semibold px-7 py-3.5 rounded-xl shadow-lg shadow-indigo-500/25 transition-all hover:-translate-y-0.5"
            >
              {t("home.ctaStart")}
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" /></svg>
            </Link>
            <Link
              href="/pricing"
              className="inline-flex items-center justify-center bg-white/70 backdrop-blur border border-slate-200 hover:border-indigo-300 hover:bg-white text-slate-700 font-medium px-7 py-3.5 rounded-xl transition-all"
            >
              {t("home.ctaPricing")}
            </Link>
          </div>
        </section>

        {/* Features */}
        <section className="max-w-5xl mx-auto px-4 pb-28">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {FEATURES.map((f, i) => (
              <div
                key={f.key}
                className="bc-rise group rounded-3xl border border-white/70 bg-white/85 backdrop-blur-xl shadow-[0_14px_50px_-18px_rgba(30,41,59,0.25)] p-6 transition-all hover:-translate-y-1 hover:shadow-[0_22px_60px_-18px_rgba(79,70,229,0.35)]"
                style={{ animationDelay: `${300 + i * 70}ms` }}
              >
                <div className={`mb-4 h-11 w-11 rounded-2xl grid place-items-center ring-1 ${f.ring}`}>
                  <svg className={`w-5 h-5 ${f.accent}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d={f.icon} />
                  </svg>
                </div>
                <h3 className="font-bold text-slate-900 mb-1.5">{t(`${f.key}.t`)}</h3>
                <p className="text-sm text-slate-600 leading-relaxed">{t(`${f.key}.d`)}</p>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
