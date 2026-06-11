import type { Metadata } from "next";
import { AuthProvider } from "@/lib/clerk-shim";
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
      <html lang="en">
        <body className="min-h-screen bg-zinc-950 text-zinc-100 antialiased">
          {children}
        </body>
      </html>
    </AuthProvider>
  );
}
