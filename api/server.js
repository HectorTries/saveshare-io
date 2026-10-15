// SaveShare customer-test API — $0.05/call via @nanotab/merchant.
// Read-only SQLite lookups over transcript_db.sqlite (copied alongside).
const path = require('path');
const express = require('express');
const Database = require('better-sqlite3');
const { nanotabCharge } = require('@nanotab/merchant');

const MERCHANT_WALLET = '0xc47b6d6a4137373ab169aeeedb95971d4939ef0b';
const PRICE = 0.05;
const PORT = process.env.PORT || 4023;

const db = new Database(path.join(__dirname, 'transcript_db.sqlite'), { readonly: true });

const app = express();
app.disable('x-powered-by');

app.get('/health', (req, res) => res.json({ ok: true, service: 'saveshare-api' }));
app.get('/price', (req, res) =>
  res.json({ price: PRICE, asset: 'USDC', network: 'base', payTo: MERCHANT_WALLET })
);

const charge = nanotabCharge({ price: PRICE, wallet: MERCHANT_WALLET });

app.get('/creator/:handle', charge, (req, res) => {
  const handle = String(req.params.handle || '').replace(/^@/, '').toLowerCase();
  const row = db
    .prepare(
      `SELECT COUNT(*) AS video_count, ROUND(AVG(views),1) AS avg_views
       FROM transcripts WHERE LOWER(creator) = ?`
    )
    .get(handle);
  if (!row || !row.video_count) return res.status(404).json({ error: 'creator not found' });
  const top = db
    .prepare(
      `SELECT hook_first_line AS top_hook, views
       FROM transcripts WHERE LOWER(creator) = ? ORDER BY views DESC LIMIT 1`
    )
    .get(handle);
  res.json({
    handle,
    video_count: row.video_count,
    avg_views: row.avg_views,
    top_hook: top ? top.top_hook : null,
  });
});

app.listen(PORT, () => console.log(`[saveshare-api] :${PORT}`));
