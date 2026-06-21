"use client";

import { useState } from "react";
import Link from "next/link";
import { SignInButton, SignUpButton, UserButton, useAuth } from "@/lib/clerk-shim";
import { LangToggle, useI18n } from "@/lib/i18n";

export default function Navbar() {
  const { isSignedIn } = useAuth();
  const { t } = useI18n();
  const [open, setOpen] = useState(false);

  const close = () => setOpen(false);

  return (
    <nav className="border-b border-white/60 bg-white/70 backdrop-blur-xl sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link href="/" className="text-lg font-bold tracking-tight text-slate-900" onClick={close}>
          Brand<span className="text-indigo-600">Compass</span>
        </Link>

        <div className="hidden md:flex items-center gap-3">
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

        <button
          type="button"
          aria-label="Toggle menu"
          aria-expanded={open}
          className="md:hidden inline-flex items-center justify-center w-10 h-10 rounded-md text-slate-700 hover:bg-slate-100 transition"
          onClick={() => setOpen((v) => !v)}
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            {open ? (
              <>
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </>
            ) : (
              <>
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </>
            )}
          </svg>
        </button>
      </div>

      {open && (
        <div className="md:hidden border-t border-white/60 bg-white/90 backdrop-blur-xl">
          <div className="max-w-6xl mx-auto px-4 py-3 flex flex-col gap-3">
            {isSignedIn ? (
              <>
                <Link
                  href="/dashboard"
                  className="text-sm text-slate-700 hover:text-indigo-600 transition"
                  onClick={close}
                >
                  {t("nav.dashboard")}
                </Link>
                <Link
                  href="/pricing"
                  className="text-sm text-slate-700 hover:text-indigo-600 transition"
                  onClick={close}
                >
                  {t("nav.pricing")}
                </Link>
                <div className="flex items-center gap-3 pt-2 border-t border-slate-200">
                  <LangToggle />
                  <UserButton />
                </div>
              </>
            ) : (
              <>
                <div className="flex items-center">
                  <LangToggle />
                </div>
                <SignInButton mode="modal">
                  <button
                    className="text-left text-sm text-slate-700 hover:text-indigo-600 transition"
                    onClick={close}
                  >
                    {t("nav.signin")}
                  </button>
                </SignInButton>
                <SignUpButton mode="modal">
                  <button
                    className="text-sm bg-gradient-to-r from-indigo-600 to-fuchsia-600 hover:from-indigo-500 hover:to-fuchsia-500 text-white font-medium px-3.5 py-2 rounded-lg transition"
                    onClick={close}
                  >
                    {t("nav.getstarted")}
                  </button>
                </SignUpButton>
              </>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
