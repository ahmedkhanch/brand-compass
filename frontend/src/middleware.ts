import { clerkMiddleware } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

// In demo mode there are no Clerk keys, so skip Clerk entirely and let every
// request through. NEXT_PUBLIC_DEMO_MODE is inlined at build time.
const DEMO = process.env.NEXT_PUBLIC_DEMO_MODE === "1";

export default DEMO ? () => NextResponse.next() : clerkMiddleware();

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)", "/", "/api/(.*)"],
};
