import Navbar from "@/components/Navbar";
import Link from "next/link";

const FEATURES = [
  { title: "Brand Positioning", desc: "Archetype, value proposition, target audience, brand voice — extracted from your website by AI." },
  { title: "SEO & GEO Scoring", desc: "Google SERP ownership + AI engine visibility. Know where you stand in search and generative AI." },
  { title: "Competitive Landscape", desc: "Direct competitors mapped with threat levels. Know who's winning and why." },
  { title: "SWOT Analysis", desc: "Strengths, weaknesses, opportunities, threats — generated from real website content." },
  { title: "Actionable Recommendations", desc: "Quick wins and strategic moves prioritized by impact. Stop guessing." },
  { title: "Live Progress", desc: "Watch your report build step by step in real-time. No waiting in the dark." },
];

export default function Home() {
  return (
    <>
      <Navbar />
      <main>
        <section className="max-w-4xl mx-auto px-4 pt-24 pb-16 text-center">
          <h1 className="text-5xl font-bold tracking-tight mb-4">
            AI-Powered Brand Intelligence
          </h1>
          <p className="text-lg text-zinc-400 max-w-2xl mx-auto mb-8">
            Enter a brand name and website URL. Get a complete diagnostic report — positioning,
            SWOT, competitive analysis, SEO, GEO, and recommendations — in under 60 seconds.
          </p>
          <div className="flex gap-4 justify-center">
            <Link href="/dashboard" className="bg-emerald-500 hover:bg-emerald-400 text-black font-semibold px-6 py-3 rounded-lg transition">
              Get Started Free
            </Link>
            <Link href="/pricing" className="border border-zinc-700 hover:border-zinc-500 text-zinc-300 px-6 py-3 rounded-lg transition">
              View Pricing
            </Link>
          </div>
        </section>

        <section className="max-w-5xl mx-auto px-4 pb-24">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {FEATURES.map((f) => (
              <div key={f.title} className="border border-zinc-800 rounded-xl p-6 hover:border-zinc-700 transition">
                <h3 className="font-semibold mb-2">{f.title}</h3>
                <p className="text-sm text-zinc-400">{f.desc}</p>
              </div>
            ))}
          </div>
        </section>
      </main>
    </>
  );
}
