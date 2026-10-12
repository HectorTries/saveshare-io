# SaveShare x402 Paywall Worker

Micropayment gate in front of `saveshare.io` **data endpoints only**, using the [Coinbase x402 protocol](https://github.com/coinbase/x402). Humans browsing HTML are unaffected — only JSON/API hits get `402`.

## What it does

| Request | Behaviour |
|---|---|
| `GET /p/*.html`, `/blog/*` with `Accept: text/html` | Passthrough to origin, no charge |
| `GET /api/*`, `*.json`, `/llms.txt`, `/ai.txt` without payment | `402` + x402 `PAYMENT-REQUIRED` JSON (USDC on Base) |
| Same with valid `X-PAYMENT` header | Verify → settle via facilitator → serve origin + `X-PAYMENT-RESPONSE` receipt |

## Price tiers

| Tier | Match | Price |
|---|---|---|
| Single profile JSON | `*.json`, `/api/*` | **$0.01** USDC |
| Bulk profiles | `/api/profiles/*` | **$0.05** USDC |
| Agent feed | `/llms.txt`, `/ai.txt` | **$0.05** USDC |
| Bulk dataset | `/api/bulk/*` | **$5.00** USDC |

Edit `PRICE_TABLE` in `src/index.ts` to change tiers.

## Prerequisites

- Cloudflare account + domain `saveshare.io` on Cloudflare
- Wrangler: `npm i -g wrangler && wrangler login`
- A **Base chain USDC receiving wallet** (see below)
- (Optional) your own facilitator; default is the public `https://x402.org/facilitator`

## Wallet setup (receive USDC on Base)

1. Create a wallet that supports Base (Coinbase Wallet, MetaMask + Base network, etc.).
2. Copy your `0x...` address.
3. Fund nothing — receiving only. Optionally send $0.05 test USDC on Base to verify the address shows funds on [Basescan](https://basescan.org).
4. Set it as `PAY_TO_ADDRESS`:
   ```bash
   wrangler secret put PAY_TO_ADDRESS  # paste 0x... when prompted
   ```
   (Or set the var in `wrangler.toml` — secret preferred.)

## Deploy

```bash
cd x402-worker
npm install
npx tsc --noEmit            # typecheck
npm run deploy              # wrangler deploy
```

Then attach routes (dashboard: Workers → saveshare-x402-paywall → Triggers → Custom Domains/Routes, or `wrangler.toml` routes):

- `saveshare.io/api/*`
- `saveshare.io/p/*.json`
- `saveshare.io/blog/*.json`
- `saveshare.io/llms.txt`
- `saveshare.io/ai.txt`

Set `ORIGIN_BASE` var to the real content origin (e.g. your Pages/GitHub Pages host) so the Worker can fetch content after payment:
```bash
wrangler secret put ORIGIN_BASE  # e.g. https://hectortries.github.io/saveshare-io
```

## Testing

```bash
# 1. No payment -> expect 402 with payment requirements
curl -s -H "Accept: application/json" https://saveshare.io/p/admjay.html.json -o /dev/null -w "%{http_code}\n"
# 2. Pay with an x402 client (e.g. x402-fetch / Coinbase agent kit) passing X-PAYMENT, then data + X-PAYMENT-RESPONSE header
```

## Files

- `wrangler.toml` — Worker name, vars (`PAY_TO_ADDRESS`, `FACILITATOR_URL`, `NETWORK`), route notes
- `src/index.ts` — paywall logic: passthrough HTML, 402 JSON, verify+settle via facilitator
- `package.json` — deps (`x402`, `viem`), wrangler scripts
