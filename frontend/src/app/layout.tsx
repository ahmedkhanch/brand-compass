import type { Metadata } from "next";
import { AuthProvider } from "@/lib/clerk-shim";
import { I18nProvider } from "@/lib/i18n";
import "./globals.css";

export const metadata: Metadata = {
  title: "Brand Compass — AI Brand Intelligence",
  description: "Analyze any brand in 60 seconds. AI-powered positioning, SEO, GEO, and competitive intelligence.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthProvider>
      <html lang="fr">
        <body className="min-h-screen bg-transparent text-slate-900 antialiased">
          <div role="status" className="w-full bg-slate-100 text-slate-600 text-center text-xs py-2 px-4">
            Développement · <a href="/wip" className="underline">Suivi du projet RadarOS</a>
          </div>
          <I18nProvider>{children}</I18nProvider>
        </body>
      </html>
    </AuthProvider>
  );
}
