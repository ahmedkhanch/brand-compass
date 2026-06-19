"use client";

import Link from "next/link";
import { SignInButton, SignUpButton, UserButton, useAuth } from "@/lib/clerk-shim";
import { LangToggle, useI18n } from "@/lib/i18n";

export default function Navbar() {
  const { isSignedIn } = useAuth();
  const { t } = useI18n();

  return (
    <nav className="border-b border-white/60 bg-white/70 backdrop-blur-xl sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link href="/" className="text-lg font-bold tracking-tight text-slate-900">
          Brand<span className="text-indigo-600">Compass</span>
        </Link>

        <div className="flex items-center gap-3">
          {isSignedIn ? (
            <>
              <Link
                href="/dashboard"
                className="text-sm text-slate-600 hover:text-indigo-600 transition"
              >
                {t("nav.dashboard")}
              </Link>
              <Link
                href="/pricing"
                className="text-sm text-slate-600 hover:text-indigo-600 transition"
              >
                {t("nav.pricing")}
              </Link>
              <LangToggle />
              <UserButton />
            </>
          ) : (
            <>
              <LangToggle />
              <SignInButton mode="modal">
                <button className="text-sm text-slate-600 hover:text-indigo-600 transition">
                  {t("nav.signin")}
                </button>
              </SignInButton>
              <SignUpButton mode="modal">
                <button className="text-sm bg-gradient-to-r from-indigo-600 to-fuchsia-600 hover:from-indigo-500 hover:to-fuchsia-500 text-white font-medium px-3.5 py-1.5 rounded-lg transition">
                  {t("nav.getstarted")}
                </button>
              </SignUpButton>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
