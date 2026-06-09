/**
 * API client — wraps all 11 Brand Compass backend endpoints.
 * Zero dependencies; uses native fetch. Works in browser and server.
 */

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const SSE = process.env.NEXT_PUBLIC_SSE_URL || "http://localhost:8000/sse";

async function fetchAPI(
  path: string,
  options: RequestInit = {},
  token?: string | null
) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error ${res.status}`);
  }
  return res.json();
}

// ── Auth ──
export async function getMe(token?: string | null) {
  return fetchAPI("/auth/me", {}, token);
}

// ── Brands ──
export async function analyzeBrand(
  data: {
    name: string;
    website_url?: string;
    industry?: string;
    competitor?: string;
    social_accounts?: Record<string, string>;
  },
  token?: string | null
) {
  return fetchAPI(
    "/brands/analyze",
    { method: "POST", body: JSON.stringify(data) },
    token
  );
}

// ── Reports ──
export async function listReports(
  page = 1,
  pageSize = 20,
  token?: string | null
) {
  return fetchAPI(`/reports?page=${page}&page_size=${pageSize}`, {}, token);
}

export async function getReport(id: string, token?: string | null) {
  return fetchAPI(`/reports/${id}`, {}, token);
}

export async function deleteReport(id: string, token?: string | null) {
  return fetchAPI(`/reports/${id}`, { method: "DELETE" }, token);
}

export async function getMetaAds(id: string, token?: string | null) {
  return fetchAPI(`/reports/${id}/meta-ads`, {}, token);
}

// ── Credits ──
export async function getCredits(token?: string | null) {
  return fetchAPI("/credits", {}, token);
}

// ── Subscription ──
export async function getSubscription(token?: string | null) {
  return fetchAPI("/subscription", {}, token);
}

export async function upgradeSubscription(tier: string, token?: string | null) {
  return fetchAPI(`/subscription/upgrade?tier=${tier}`, { method: "POST" }, token);
}

export async function createCheckout(
  tier: string,
  token?: string | null
) {
  return fetchAPI(
    `/checkout?tier=${tier}`,
    { method: "POST" },
    token
  );
}

export async function createPortal(token?: string | null) {
  return fetchAPI("/checkout/portal", { method: "POST" }, token);
}

// ── SSE (not JSON — returns EventSource) ──
export function streamReportProgress(
  reportId: string,
  onStatus: (status: string) => void,
  onComplete: () => void,
  onError: (err: string) => void
) {
  const url = `${SSE}/reports/${reportId}`;
  const source = new EventSource(url);

  source.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onStatus(data.status);
      if (data.status === "complete" || data.status === "failed") {
        source.close();
        onComplete();
      }
      if (data.status === "error" || data.status === "timeout") {
        source.close();
        onError(data.message || "Unknown error");
      }
    } catch {
      // ignore parse errors
    }
  };

  source.onerror = () => {
    source.close();
    onError("SSE connection lost");
  };

  return source;
}
