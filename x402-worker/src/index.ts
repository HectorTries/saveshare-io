// SaveShare x402 paywall Worker (Coinbase x402 protocol, USDC on Base).
//
// Behaviour:
//  - HTML/browser traffic (Accept: text/html, no .json path) -> passthrough to origin untouched.
//  - JSON/API endpoints (/api/*, *.json, /llms.txt, /ai.txt) -> require x402 micropayment.
//    Without payment: HTTP 402 + PAYMENT-REQUIRED JSON (x402 spec).
//    With valid X-PAYMENT header: verify via facilitator, then serve origin content.

import { decode } from "x402/verify"; // version-agnostic helpers where available

interface Env {
  PAY_TO_ADDRESS: string;
  FACILITATOR_URL: string;
  NETWORK: string; // "base"
  ORIGIN_BASE?: string; // e.g. "https://hectortries.github.io/saveshare-io" or origin pages host
}

const USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA4b1e"; // native USDC on Base

// Price tiers in USD (atomic USDC = dollars * 1e6)
const PRICE_TABLE: { match: RegExp; priceUsd: number; resource: string }[] = [
  { match: /^\/api\/bulk(\/|$)/, priceUsd: 5.0, resource: "bulk dataset" },
  { match: /^\/api\/profiles(\/|$)/, priceUsd: 0.05, resource: "bulk profiles" },
  { match: /^\/api\//, priceUsd: 0.01, resource: "single api call" },
  { match: /\.json(\?|$)/, priceUsd: 0.01, resource: "profile json" },
  { match: /^\/(llms\.txt|ai\.txt)$/, priceUsd: 0.05, resource: "agent feed" },
];

function priceFor(path: string) {
  for (const t of PRICE_TABLE) if (t.match.test(path)) return t;
  return null;
}

function isPaywalled(req: Request, url: URL): boolean {
  const accept = req.headers.get("accept") || "";
  // Browsers navigating pages get HTML free.
  if (req.method === "GET" && accept.includes("text/html") && !url.pathname.endsWith(".json") && !url.pathname.startsWith("/api/")) {
    return false;
  }
  return priceFor(url.pathname) !== null;
}

function paymentRequired(env: Env, url: URL, tier: { priceUsd: number; resource: string }) {
  const amount = Math.round(tier.priceUsd * 1_000_000).toString(); // USDC 6dp
  const body = {
    x402Version: 1,
    accepts: [
      {
        scheme: "exact",
        network: env.NETWORK || "base",
        maxAmountRequired: amount,
        resource: `https://${url.host}${url.pathname}`,
        description: `SaveShare ${tier.resource} — $${tier.priceUsd.toFixed(2)} USDC (Base)`,
        mimeType: "application/json",
        payTo: env.PAY_TO_ADDRESS,
        maxTimeoutSeconds: 300,
        asset: USDC_BASE,
        extra: { name: "USDC", version: "2" },
      },
    ],
  };
  return new Response(JSON.stringify(body), {
    status: 402,
    headers: {
      "content-type": "application/json",
      "access-control-expose-headers": "X-PAYMENT-RESPONSE, PAYMENT-REQUIRED",
    },
  });
}

async function verifyPayment(env: Env, paymentHeader: string, url: URL, tier: { priceUsd: number; resource: string }): Promise<{ ok: boolean; settleResponse?: string; error?: string }> {
  try {
    const facilitator = (env.FACILITATOR_URL || "https://x402.org/facilitator").replace(/\/$/, "");
    const amount = Math.round(tier.priceUsd * 1_000_000).toString();
    const paymentRequirements = {
      scheme: "exact",
      network: env.NETWORK || "base",
      maxAmountRequired: amount,
      resource: `https://${url.host}${url.pathname}`,
      description: `SaveShare ${tier.resource}`,
      mimeType: "application/json",
      payTo: env.PAY_TO_ADDRESS,
      maxTimeoutSeconds: 300,
      asset: USDC_BASE,
      extra: { name: "USDC", version: "2" },
    };
    const decoded = paymentHeader.startsWith("{") ? JSON.parse(paymentHeader) : decode(paymentHeader);
    // 1. verify
    const v = await fetch(`${facilitator}/verify`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ x402Version: 1, paymentHeader: decoded, paymentRequirements }),
    });
    const vj = (await v.json()) as { isValid?: boolean; invalidReason?: string };
    if (!v.ok || !vj.isValid) return { ok: false, error: vj.invalidReason || `verify ${v.status}` };
    // 2. settle
    const s = await fetch(`${facilitator}/settle`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ x402Version: 1, paymentHeader: decoded, paymentRequirements }),
    });
    const sj = (await s.json()) as { success?: boolean; transaction?: string; errorReason?: string };
    if (!s.ok || !sj.success) return { ok: false, error: sj.errorReason || `settle ${s.status}` };
    return { ok: true, settleResponse: sj.transaction || "settled" };
  } catch (e) {
    return { ok: false, error: String(e) };
  }
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    if (!isPaywalled(req, url)) {
      return fetch(req); // HTML passthrough
    }
    const tier = priceFor(url.pathname)!;
    const payment = req.headers.get("X-PAYMENT");
    if (!payment) return paymentRequired(env, url, tier);
    const res = await verifyPayment(env, payment, url, tier);
    if (!res.ok) {
      const retry = paymentRequired(env, url, tier);
      const body = JSON.stringify({ ...(await retry.json()), error: res.error });
      return new Response(body, { status: 402, headers: { "content-type": "application/json" } });
    }
    // Payment verified — serve origin content, attach settlement receipt.
    const origin = env.ORIGIN_BASE ? new URL(url.pathname + url.search, env.ORIGIN_BASE) : req;
    const upstream = await fetch(origin as RequestInfo);
    const headers = new Headers(upstream.headers);
    headers.set("X-PAYMENT-RESPONSE", res.settleResponse || "ok");
    headers.set("Access-Control-Expose-Headers", "X-PAYMENT-RESPONSE");
    return new Response(upstream.body, { status: upstream.status, headers });
  },
};
