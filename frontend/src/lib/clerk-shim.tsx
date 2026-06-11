"use client";
/**
 * Clerk shim — lets the app run with NO Clerk keys in demo mode.
 *
 * When NEXT_PUBLIC_DEMO_MODE === "1" every Clerk primitive is replaced by a stub:
 * useAuth() reports a signed-in demo user, the auth buttons render their children
 * (or a placeholder), and the provider is a pass-through. Otherwise the real Clerk
 * exports are used unchanged. The flag is a build-time constant, so the branch is
 * stable across renders (safe for the rules-of-hooks).
 */
import React from "react";
import * as Clerk from "@clerk/nextjs";

const DEMO = process.env.NEXT_PUBLIC_DEMO_MODE === "1";
// Matches the backend dev token branch in app/core/deps.py (token.startswith("dev-user-")).
const DEMO_TOKEN = "dev-user-demo";

function useDemoAuth() {
  return {
    isLoaded: true,
    isSignedIn: true,
    userId: DEMO_TOKEN,
    sessionId: DEMO_TOKEN,
    getToken: async () => DEMO_TOKEN,
    signOut: async () => {},
  };
}

type Kids = { children?: React.ReactNode };

export const useAuth: typeof Clerk.useAuth = (DEMO ? useDemoAuth : Clerk.useAuth) as typeof Clerk.useAuth;

export const SignInButton: React.FC<Kids & { mode?: string }> = DEMO
  ? ({ children }) => <>{children}</>
  : (Clerk.SignInButton as unknown as React.FC<Kids & { mode?: string }>);

export const SignUpButton: React.FC<Kids & { mode?: string }> = DEMO
  ? ({ children }) => <>{children}</>
  : (Clerk.SignUpButton as unknown as React.FC<Kids & { mode?: string }>);

export const UserButton: React.FC = DEMO
  ? () => (
      <div
        title="Demo user"
        className="h-7 w-7 rounded-full bg-emerald-500 text-black grid place-items-center text-xs font-bold select-none"
      >
        D
      </div>
    )
  : (Clerk.UserButton as unknown as React.FC);

export function AuthProvider({ children }: Kids) {
  if (DEMO) return <>{children}</>;
  return <Clerk.ClerkProvider>{children}</Clerk.ClerkProvider>;
}
