# SaveShare customer-test API — $0.05/call (NanoTab paywall)

Live: `https://nanotab.dev/saveshare` (VPS 178.104.35.162, systemd `saveshare-api`, Caddy path route).

## Endpoints
- `GET /health` — free: `{ok:true, service:'saveshare-api'}`
- `GET /price` — free: `{price:0.05, asset:'USDC', network:'base', payTo:'0xc47b…'}`
- `GET /creator/:handle` — **402 paywalled, $0.05** → `{handle, video_count, avg_views, top_hook}`

## Paywall (@nanotab/merchant real middleware)
- No `X-Payment` header → `402` with x402 spec (`payTo`, `maxAmountRequired:"5"` cents).
- `X-Payment` = base64 JSON `{amount,to,asset,signature[,network,from]}` → structural verify → 200.
- Fee 0.5% logged server-side; on-chain settlement via gateway.
- `vendor/nanotab-merchant-0.1.0.tgz` = `npm pack` of `../../nanotab/packages/merchant` dist (real code, not a mock).

## Deploy
- VPS: `/opt/saveshare-api` (server.js, package.json, vendor/, transcript_db.sqlite), systemd unit `saveshare-api.service` (PORT=4023), Caddy `handle /saveshare/*` on nanotab.dev.
- Refresh DB copy: `scp transcript_db.sqlite root@178.104.35.162:/opt/saveshare-api/ && systemctl restart saveshare-api`.
- NOTE: `api/transcript_db.sqlite` is a local copy (git-ignored). Re-copy after DB updates.
