import type { NextConfig } from "next";

// Same-origin proxy: the browser calls /api/v1 and /sse on the page's own origin
// (so it works behind the Caddy reverse proxy with no CORS and no exposed backend
// port). Next forwards to the backend over the compose network. Override the
// target with BACKEND_ORIGIN at runtime.
const BACKEND_ORIGIN = process.env.BACKEND_ORIGIN || "http://backend:8000";

// Public domains (behind Cloudflare → Caddy) the dev server is reached through.
// Next 15.3+/16 blocks cross-origin loading of /_next dev resources (chunks, HMR)
// by default; without this the client bundle never loads through the public host,
// so the page renders but never hydrates and every button is dead.
const ALLOWED_DEV_ORIGINS = [
  "brandcompass-develop.oratelecom.net",
  "brandcompass-main.oratelecom.net",
];

const nextConfig: NextConfig = {
  allowedDevOrigins: ALLOWED_DEV_ORIGINS,
  async rewrites() {
    return [
      { source: "/api/v1/:path*", destination: `${BACKEND_ORIGIN}/api/v1/:path*` },
      { source: "/sse/:path*", destination: `${BACKEND_ORIGIN}/sse/:path*` },
    ];
  },
};

export default nextConfig;
