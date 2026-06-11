"use client";

import Link from "next/link";
import { SignInButton, SignUpButton, UserButton, useAuth } from "@/lib/clerk-shim";

export default function Navbar() {
  const { isSignedIn } = useAuth();

  return (
    <nav className="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link href="/" className="text-lg font-bold tracking-tight">
          Brand<span className="text-emerald-400">Compass</span>
        </Link>

        <div className="flex items-center gap-3">
          {isSignedIn ? (
            <>
              <Link
                href="/dashboard"
                className="text-sm text-zinc-400 hover:text-white transition"
              >
                Dashboard
              </Link>
              <Link
                href="/pricing"
                className="text-sm text-zinc-400 hover:text-white transition"
              >
                Pricing
              </Link>
              <UserButton />
            </>
          ) : (
            <>
              <SignInButton mode="modal">
                <button className="text-sm text-zinc-400 hover:text-white transition">
                  Sign In
                </button>
              </SignInButton>
              <SignUpButton mode="modal">
                <button className="text-sm bg-emerald-500 hover:bg-emerald-400 text-black font-medium px-3 py-1.5 rounded-lg transition">
                  Get Started
                </button>
              </SignUpButton>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
