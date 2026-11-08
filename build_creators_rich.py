#!/usr/bin/env python3
"""Rich, data-driven SaveShare creator pages (2026-11-08).

Replaces the thin 5KB template pages with pages built from the transcript DB:
numbers table, real quotes with context, top videos table, topic mix, money
claims with sources, percentile comparison, posting rhythm, FAQ + JSON-LD,
related creators, and a Pinterest save action on every page.
"""
import os, re, json, sqlite3, html, statistics, urllib.parse
from datetime import datetime

REPO = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(REPO, "transcript_db.sqlite")
AVDIR = os.path.join(REPO, "avatars")
P = os.path.join(REPO, "p")
SITE = "https://saveshare.io"

def _load_map():
    """handle -> existing page filename (avatars strip dots, so filenames vary)."""
    import glob
    m = {}
    for f in glob.glob(os.path.join(P, "*.html")):
        try:
            h = open(f, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        for x in set(re.findall(r"tiktok\.com/@([A-Za-z0-9._]+)", h)):
            m.setdefault(x, os.path.basename(f)[:-5])
    return m

MAP = _load_map()

# ---- shared chrome from build_pages.py (template only) --------------------
_src = open(os.path.join(REPO, "build_pages.py")).read()
ns = {}
exec(compile(_src[: _src.index("CREATORS = [")], "tmpl", "exec"), ns)
page = ns["page"]
NAV_P = ns["NAV_P"]

EXTRA_CSS = """
<style>
.nums{width:100%;border-collapse:collapse;margin:18px 0;font-size:14px}
.nums th,.nums td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--line)}
.nums th{font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);font-weight:700}
.nums td b{font-variant-numeric:tabular-nums}
.vid{width:100%;border-collapse:collapse;margin:16px 0;font-size:13.5px}
.vid th,.vid td{text-align:left;padding:8px 8px;border-bottom:1px solid var(--line);vertical-align:top}
.vid th{font-size:11.5px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}
.vid td.n{font-variant-numeric:tabular-nums;white-space:nowrap}
.vid a{text-decoration:none}
.topics{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0}
.topic{background:#fff;border:1px solid var(--line);border-radius:12px;padding:10px 14px;font-size:13px}
.topic b{display:block;font-size:18px}
.pin-btn{display:inline-flex;align-items:center;gap:8px;background:#e60023;color:#fff;font-weight:700;
  font-size:14px;padding:10px 18px;border-radius:999px;text-decoration:none;margin:18px 0}
.pin-btn:hover{background:#ad081b;color:#fff}
.meta-line{font-size:12.5px;color:var(--muted);margin-top:6px}
</style>
"""


def fin(x, d=0.0):
    try:
        v = float(x)
        return v if v == v else d
    except Exception:
        return d


def fmt_int(n):
    return f"{int(round(n)):,}"


def fmt_money(n, cur="£"):
    n = fin(n)
    if n >= 1_000_000:
        return f"{cur}{n/1_000_000:.1f}M"
    if n >= 10_000:
        return f"{cur}{n/1000:.1f}K"
    return f"{cur}{n:,.0f}"


def initials(name):
    parts = re.sub(r"[^A-Za-z ]", " ", name).split()
    return "".join(p[0] for p in parts[:2]).upper() or "SS"


def clean_transcript(t):
    if not t:
        return ""
    t = re.sub(r"^WEBVTT.*?\n\n", "", t, flags=re.S)
    t = re.sub(r"\d{1,2}:\d{2}:\d{2}(?:\.\d+)?\s*-->\s*\d{1,2}:\d{2}:\d{2}(?:\.\d+)?", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def read_transcript(path):
    try:
        raw = open(path).read()
    except Exception:
        return "", ""
    cap = ""
    m = re.search(r"## Caption\s*\n+(.*?)\n+## Transcript", raw, re.S)
    if m:
        cap = re.sub(r"\s+", " ", m.group(1)).strip()
    i = raw.find("## Transcript")
    body = raw[i + len("## Transcript"):] if i >= 0 else ""
    return cap, clean_transcript(body)


MONEY = re.compile(r"£|\$|debt|save|saving|invest|salary|credit|pension|mortgage|interest|budget|income|pay", re.I)


def pick_quotes(rows, limit=6):
    """Sentences of 14-45 words that mention money, longest-video first."""
    seen, out = set(), []
    for r in rows:
        _, text = read_transcript(r["transcript_path"] or "")
        if not text:
            continue
        for s in re.split(r"(?<=[.!?])\s+", text):
            s = s.strip(" -")
            w = len(s.split())
            if not (14 <= w <= 45) or not MONEY.search(s):
                continue
            key = re.sub(r"[^a-z]", "", s.lower())[:60]
            if key in seen:
                continue
            seen.add(key)
            out.append((s, r))
            break
        if len(out) >= limit:
            break
    return out


def load():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    creators = {r["handle"]: dict(r) for r in c.execute("select * from creators")}
    rows = {}
    for r in c.execute("select * from transcripts order by views desc"):
        rows.setdefault(r["creator"], []).append(dict(r))
    figs = {}
    for r in c.execute("select * from figures order by amount desc"):
        figs.setdefault(r["creator"], []).append(dict(r))
    return creators, rows, figs


FIG_LABEL = {
    "net_worth": "Net worth", "income": "Income", "debt_paid": "Debt paid off",
    "invested": "Invested", "savings": "Savings", "portfolio": "Portfolio",
    "pension": "Pension", "debt_total": "Total debt", "savings_goal": "Savings goal",
    "property": "Property",
}


def existing_bits(handle):
    """Pull human-written copy + follower count from the current page."""
    path = os.path.join(P, MAP.get(handle, handle) + ".html")
    if not os.path.isfile(path):
        return {}
    h = open(path).read()
    out = {}
    m = re.search(r'<span class="stat"><strong>([^<]+)</strong><span>Followers</span>', h)
    if m:
        out["followers"] = m.group(1).strip()
    m = re.search(r'<p class="tag">([^<]+)</p>', h) or re.search(r'<span class="tag">([^<]+)</span>', h)
    if m:
        out["tagline"] = m.group(1).strip()
    m = re.search(r"<h2[^>]*>Who is [^<]*\?</h2>\s*<p>(.*?)</p>", h, re.S)
    if m:
        out["who"] = re.sub(r"\s+", " ", m.group(1)).strip()
    m = re.search(r"<h2[^>]*>How they got there</h2>\s*<p>(.*?)</p>", h, re.S)
    if m:
        out["journey"] = re.sub(r"\s+", " ", m.group(1)).strip()
    m = re.search(r"<!-- PinBridge: Pinterest pin ([0-9a-f-]{36}) -->", h)
    if m:
        out["pin"] = m.group(1)
    return out



def nw_series(fig_rows):
    """Self-reported net worth by year, last statement per year, min 3 points."""
    pts = {}
    for f in fig_rows:
        if (f.get("figure_type") or "") != "net_worth":
            continue
        amt = fin(f.get("amount"))
        year = f.get("as_of_year")
        if not year:
            d = (f.get("as_of_date") or "")[:4]
            year = int(d) if d.isdigit() else None
        if not year:
            continue
        pts[int(year)] = (amt, f.get("as_of_date") or "", f.get("currency") or "GBP")
    if len(pts) < 3:
        return []
    return [(y, pts[y][0], pts[y][1]) for y in sorted(pts)]


def compact_money(n, sign_ok=True):
    neg = n < 0
    a = abs(n)
    if a >= 1_000_000:
        s = f"{a/1_000_000:.1f}M"
    elif a >= 1000:
        s = f"{a/1000:.0f}K" if a % 1000 == 0 or a >= 10000 else f"{a/1000:.1f}K"
    else:
        s = f"{a:.0f}"
    return ("-" if neg else "") + "£" + s


def nw_chart(series, name):
    """Inline SVG line chart of self-reported net worth, no JS."""
    if len(series) < 3:
        return ""
    W, H = 720, 300
    L, R, T, B = 70, 20, 24, 40
    vals = [v for _, v, _ in series]
    lo, hi = min(min(vals), 0), max(max(vals), 0)
    if hi == lo:
        hi = lo + 1
    pad = (hi - lo) * 0.12
    lo2, hi2 = lo - (pad if lo < 0 else 0), hi + pad
    n = len(series)
    iw, ih = W - L - R, H - T - B

    def X(i):
        return L + (iw * i / (n - 1))

    def Y(v):
        return T + ih - (v - lo2) / (hi2 - lo2) * ih

    pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, (_, v, _) in enumerate(series))
    base = Y(max(0, lo2))
    area = f"{L:.1f},{base:.1f} " + pts + f" {X(n-1):.1f},{base:.1f}"

    grid = ""
    for k in range(4):
        v = lo2 + (hi2 - lo2) * k / 3
        y = Y(v)
        grid += (f'<line x1="{L}" y1="{y:.1f}" x2="{W-R}" y2="{y:.1f}" stroke="#E4E0D3" stroke-width="1"/>'
                 f'<text x="{L-10}" y="{y+4:.1f}" text-anchor="end" font-size="11" fill="#5A665E">{compact_money(v)}</text>')
    zero = ""
    if lo2 < 0 < hi2:
        zy = Y(0)
        zero = f'<line x1="{L}" y1="{zy:.1f}" x2="{W-R}" y2="{zy:.1f}" stroke="#B9B3A0" stroke-width="1.2" stroke-dasharray="4 4"/>'

    dots, labels = "", ""
    for i, (yr, v, _) in enumerate(series):
        x, y = X(i), Y(v)
        dots += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.2" fill="#C07A12" stroke="#fff" stroke-width="1.6"/>'
        step = 1 if n <= 8 else 2
        if i % step == 0 or i == n - 1:
            labels += f'<text x="{x:.1f}" y="{H-14}" text-anchor="middle" font-size="11" fill="#5A665E">{yr}</text>'
    first_i, last_i = 0, n - 1
    labels += (f'<text x="{X(first_i):.1f}" y="{Y(vals[first_i])-12:.1f}" text-anchor="middle" font-size="12" font-weight="700" fill="#17201B">{compact_money(vals[first_i])}</text>')
    labels += (f'<text x="{X(last_i):.1f}" y="{Y(vals[last_i])-12:.1f}" text-anchor="middle" font-size="12" font-weight="700" fill="#17201B">{compact_money(vals[last_i])}</text>')

    delta = vals[-1] - vals[0]
    trend = f"{compact_money(vals[0])} to {compact_money(vals[-1])} between {series[0][0]} and {series[-1][0]}"
    aria = f"{name} self-reported net worth over time: {trend}."
    return f"""<div class="nw-chart">
<svg viewBox="0 0 {W} {H}" role="img" aria-label="{html.escape(aria)}" preserveAspectRatio="xMidYMid meet">
{grid}{zero}
<polygon points="{area}" fill="#0B3D2E" opacity="0.08"/>
<polyline points="{pts}" fill="none" stroke="#0B3D2E" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round"/>
{dots}{labels}
</svg>
<p class="nw-note">Self-reported net worth by year, from the creator's own videos. {len(series)} yearly points. Change over the period: {"+" if delta >= 0 else ""}{compact_money(delta)}.</p>
</div>"""


def build(handle, creators, rows, figs, ctx):
    cr = creators[handle]
    tx = [r for r in rows.get(handle, []) if fin(r["views"]) > 0]
    tx.sort(key=lambda r: fin(r["views"]), reverse=True)
    bits = existing_bits(handle)
    name = (cr.get("nickname") or handle).split("|")[0].strip() or handle
    # Prefer the display name already published on the page (hand-curated).
    try:
        _h = open(os.path.join(P, MAP.get(handle, handle) + ".html")).read()
        _m = re.search(r"<h1>([^<]+?)\s*<span", _h)
        if _m:
            name = html.unescape(_m.group(1)).strip()
    except Exception:
        pass
    tagline = bits.get("tagline") or (cr.get("nickname") or "").replace(name, "").strip(" |") or "UK money creator"
    av = handle.replace(".", "") + ".jpg"
    if not os.path.isfile(os.path.join(AVDIR, av)):
        av = handle + ".jpg"
    has_av = os.path.isfile(os.path.join(AVDIR, av))

    views = [fin(r["views"]) for r in tx]
    likes = [fin(r["likes"]) for r in tx]
    engs = [fin(r["engagement_rate"]) for r in tx if fin(r["engagement_rate"]) > 0]
    total_views = sum(views)
    med_views = statistics.median(views) if views else 0
    avg_eng = (sum(engs) / len(engs) * 100) if engs else 0
    dates = sorted([r["published_at"] for r in tx if r.get("published_at")])
    span = ""
    if len(dates) >= 2:
        a = datetime.strptime(dates[0][:10], "%Y-%m-%d")
        b = datetime.strptime(dates[-1][:10], "%Y-%m-%d")
        days = max(1, (b - a).days)
        span = f"{a.strftime('%d %b %Y')} to {b.strftime('%d %b %Y')}"
        per_month = len(tx) * 30.44 / days
    else:
        per_month = 0

    # ---- stat row
    stats = []
    if bits.get("followers"):
        stats.append((bits["followers"], "Followers"))
    if tx:
        stats.append((fmt_int(total_views), "Views archived"))
        stats.append((fmt_int(med_views), "Median views"))
        stats.append((f"{avg_eng:.2f}%", "Avg engagement"))
    stats = stats[:4]

    # ---- numbers table
    num_rows = [
        ("Videos archived", f"{len(tx)}"),
        ("Total views on those videos", fmt_int(total_views)),
        ("Average views per video", fmt_int(total_views / len(tx)) if tx else "0"),
        ("Median views per video", fmt_int(med_views)),
        ("Average engagement rate", f"{avg_eng:.2f}%"),
        ("Best video", f"{fmt_int(views[0])} views" if views else "n/a"),
        ("Posting window tracked", span or "n/a"),
        ("Videos per month in window", f"{per_month:.1f}" if per_month else "n/a"),
    ]

    # ---- percentile comparison
    comp = ""
    if tx:
        rank = ctx["eng_rank"].get(handle)
        if rank:
            comp = (f"Her average engagement of {avg_eng:.2f}% is higher than "
                    f"{rank:.0f}% of the {ctx['n_creators']} creators tracked on SaveShare. ")
        vrank = ctx["view_rank"].get(handle)
        if vrank:
            comp += (f"Median views sit above {vrank:.0f}% of them.")

    # ---- money claims
    fig_html = ""
    for f in figs.get(handle, [])[:6]:
        label = FIG_LABEL.get(f.get("figure_type"), "Figure")
        cur = "$" if (f.get("currency") == "USD") else "£"
        amt = fmt_money(f.get("amount"), cur)
        q = html.escape(f.get("quote") or "")
        d = (f.get("as_of_date") or "")[:10]
        when = datetime.strptime(d, "%Y-%m-%d").strftime("%d %b %Y") if d else ""
        fig_html += (
            f"<tr><td><b>{label}</b></td><td class=\"n\">{amt}</td>"
            f"<td>{q}</td><td class=\"n\">{when}</td></tr>"
        )
    if fig_html:
        fig_html = ("<table class=\"nums\"><thead><tr><th>Claim</th><th>Figure</th>"
                    "<th>In their words</th><th>Date</th></tr></thead><tbody>"
                    + fig_html + "</tbody></table>")

    # ---- quotes
    qblocks = ""
    for q, r in pick_quotes(tx, 6):
        d = (r.get("published_at") or "")[:10]
        when = datetime.strptime(d, "%Y-%m-%d").strftime("%d %b %Y") if d else ""
        qblocks += (
            f"<blockquote>{html.escape(q)}<cite> {html.escape(name)} "
            f"(<a href=\"{r['url']}\" target=\"_blank\" rel=\"noopener\">watch on TikTok &#8599;</a>"
            f"{', ' + when if when else ''}, {fmt_int(fin(r['views']))} views)</cite></blockquote>\n"
        )
    if not qblocks:
        qblocks = "<p>No transcript quotes archived yet for this creator.</p>"

    # ---- top videos table
    vrows = ""
    for r in tx[:10]:
        title = (r.get("hook_first_line") or "").strip()
        if not title:
            cap, _ = read_transcript(r.get("transcript_path") or "")
            title = cap
        title = re.sub(r"\s+", " ", title)[:95]
        d = (r.get("published_at") or "")[:10]
        when = datetime.strptime(d, "%Y-%m-%d").strftime("%d %b %y") if d else ""
        vrows += (
            f"<tr><td><a href=\"{r['url']}\" target=\"_blank\" rel=\"noopener\">{html.escape(title)}</a></td>"
            f"<td class=\"n\">{when}</td><td class=\"n\">{fmt_int(fin(r['views']))}</td>"
            f"<td class=\"n\">{fmt_int(fin(r['likes']))}</td>"
            f"<td class=\"n\">{fin(r['engagement_rate'])*100:.1f}%</td></tr>"
        )
    vid_html = ""
    if vrows:
        vid_html = ("<table class=\"vid\"><thead><tr><th>Video</th><th>Date</th><th>Views</th>"
                    "<th>Likes</th><th>Eng.</th></tr></thead><tbody>" + vrows + "</tbody></table>")

    # ---- topic mix
    topics = {}
    for r in tx:
        for t in (r.get("theme_tags") or "").split(","):
            t = t.strip()
            if t:
                topics[t] = topics.get(t, 0) + 1
    topic_html = ""
    if topics:
        top = sorted(topics.items(), key=lambda kv: kv[1], reverse=True)[:6]
        topic_html = "<div class=\"topics\">" + "".join(
            f'<div class="topic"><b>{n}</b>{html.escape(t)} videos</div>' for t, n in top
        ) + "</div>"

    # ---- posting rhythm (last 12 months)
    months = {}
    for r in tx:
        d = (r.get("published_at") or "")[:7]
        if d:
            months[d] = months.get(d, 0) + 1
    rhythm = ""
    if months:
        last = sorted(months)[-12:]
        rhythm = ("<p class=\"meta-line\">Tracked activity: " + ", ".join(
            f"{datetime.strptime(m, '%Y-%m').strftime('%b %y')} ({months[m]})" for m in last) + "</p>")

    # ---- related creators
    rel = ctx["related"].get(handle, [])
    rel_html = ""
    if rel:
        rel_html = "<div class=\"topics\">" + "".join(
            f'<a class="topic" href="{MAP.get(h, h)}.html" style="text-decoration:none;color:var(--ink)">'
            f'<b>{html.escape(n)}</b>@{html.escape(h)}</a>' for h, n in rel
        ) + "</div>"

    # ---- FAQ + JSON-LD
    top_vid = tx[0] if tx else None
    faqs = [
        (f"Does {name} publish their net worth?",
         ("Yes. The figures they have stated in their own videos are listed above, each with the quote and date."
          if figs.get(handle) else
          f"No. {name} has not stated a net worth figure in the videos tracked here, so none is shown.")),
        (f"What does {name} post about?",
         (f"The archived videos cover {', '.join(t for t, _ in sorted(topics.items(), key=lambda kv: -kv[1])[:4])}."
          if topics else f"{name} posts personal finance content on TikTok.")),
        (f"How often does {name} post?",
         (f"About {per_month:.1f} videos a month across the tracked window ({span})." if per_month
          else "Posting frequency could not be calculated from the tracked videos.")),
        (f"What is {name}'s best performing video?",
         (f"{re.sub(r'\\s+', ' ', (top_vid.get('hook_first_line') or 'A video')[:80])} with {fmt_int(fin(top_vid['views']))} views."
          if top_vid else "Not available yet.")),
    ]
    faq_html = "".join(
        f'<div class="card"><h2 style="font-size:19px;margin-bottom:8px">{html.escape(q)}</h2>'
        f"<p>{html.escape(a)}</p></div>" for q, a in faqs
    )
    faq_ld = json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs],
    }, ensure_ascii=False)
    prof_ld = json.dumps({
        "@context": "https://schema.org", "@type": "ProfilePage",
        "mainEntity": {"@type": "Person", "name": name, "alternateName": "@" + handle,
                       "jobTitle": "Personal finance creator",
                       "description": tagline,
                       "url": f"{SITE}/p/{handle}.html",
                       "sameAs": [f"https://www.tiktok.com/@{handle}"]},
    }, ensure_ascii=False)
    ld = f'<script type="application/ld+json">{prof_ld}</script>\n<script type="application/ld+json">{faq_ld}</script>'

    # ---- pinterest
    pin_url = ("https://www.pinterest.com/pin/create/button/?url="
               + urllib.parse.quote(f"{SITE}/p/{handle}.html", safe="")
               + "&media=" + urllib.parse.quote(f"{SITE}/avatars/{av}", safe="")
               + "&description=" + urllib.parse.quote(f"{name}: money journey, numbers and quotes", safe=""))
    pin_block = (f'<a class="pin-btn" href="{pin_url}" target="_blank" rel="noopener">'
                 f'Save this profile to Pinterest</a>')
    if bits.get("pin"):
        pin_block += (f'\n<!-- PinBridge: Pinterest pin {bits["pin"]} -->\n'
                      f'<a href="https://www.pinterest.com/pin/{bits["pin"]}/" data-pinbridge="{bits["pin"]}" '
                      f'style="display:none" aria-hidden="true">Pin this page on Pinterest</a>')

    who = bits.get("who") or (
        f"{name} posts personal finance content on TikTok as @{handle}, "
        f"with {len(tx)} videos archived here and an average engagement rate of {avg_eng:.2f}%.")
    journey = bits.get("journey") or ""

    body = f"""
<div class="card">
<p><span class="tag">{html.escape(tagline)}</span> <span class="tag">Updated {datetime.now().strftime('%b %Y')}</span>
<span class="tag">{len(tx)} videos archived</span>
{f'<span class="tag">Avg engagement {avg_eng:.2f}%</span>' if tx else ''}</p>
<div class="stat-row">{"".join(f'<div class="stat"><strong>{v}</strong><span>{l}</span></div>' for v, l in stats)}</div>
<p class="src">Figures come from the creator's public TikTok videos. Engagement is (likes + comments + shares + bookmarks) divided by views, averaged across the archived videos. Not independently audited, not financial advice.</p>
{pin_block}
</div>

<h2 style="margin:32px 0 12px">The numbers</h2>
<table class="nums"><tbody>
{"".join(f'<tr><td>{l}</td><td class="n"><b>{v}</b></td></tr>' for l, v in num_rows)}
</tbody></table>
{f'<p>{comp}</p>' if comp else ''}
{nw_chart(nw_series(figs.get(handle, [])), name)}

<h2 style="margin:32px 0 12px">Who is {html.escape(name)}?</h2>
<p>{who}</p>
{f'<p>{journey}</p>' if journey else ''}

<h2 style="margin:32px 0 12px">Money claims, with sources</h2>
{fig_html or '<p>No self-stated figures have been archived for this creator yet.</p>'}

<h2 style="margin:32px 0 12px">What {html.escape(name)} actually says</h2>
{qblocks}

<h2 style="margin:32px 0 12px">Best performing videos</h2>
{vid_html or '<p>No video stats available.</p>'}

<h2 style="margin:32px 0 12px">What they post about</h2>
{topic_html or '<p>Topic tags are not available for this creator yet.</p>'}
{rhythm}

<h2 style="margin:32px 0 12px">Similar creators</h2>
{rel_html or '<p><a href="../index.html#creators">Browse all creators</a></p>'}

<h2 style="margin:32px 0 12px">Frequently asked</h2>
{faq_html}
{ld}
<p style="margin-top:32px"><a href="../index.html#creators">&larr; Back to all creators</a> &middot; <a href="../blog/index.html">Money advice hub &rarr;</a></p>
"""

    title = f"{name} (@{handle}): Numbers, Quotes and Money Journey | SaveShare.io"
    desc = (f"{name} (@{handle}) on TikTok: {len(tx)} videos archived, {fmt_int(total_views)} views, "
            f"{avg_eng:.2f}% average engagement, self-stated money figures with sources and quotes.")
    out = page(title, desc[:180], NAV_P, "UK MONEY CREATOR PROFILE" if cr.get("region") == "UK" else "US MONEY CREATOR PROFILE",
               f'{html.escape(name)} <span style="opacity:.8">(@{handle})</span>', tagline, body,
               avatar=av if has_av else None, slug=handle)
    out = re.sub(r"<style>.*?</style>\s*", "", out, flags=re.S)
    if 'href="../styles.css"' not in out:
        out = out.replace("</head>",
            '<link rel="stylesheet" href="../styles.css?v=20261108b">'
            '<link rel="preload" href="../fonts/manrope.woff2" as="font" type="font/woff2" crossorigin>\n</head>', 1)
    return out


def main():
    creators, rows, figs = load()
    # comparison context across creators with >= 3 videos
    eng, med = {}, {}
    for h, rs in rows.items():
        v = [r for r in rs if fin(r["views"]) > 0]
        if len(v) < 3:
            continue
        e = [fin(r["engagement_rate"]) for r in v if fin(r["engagement_rate"]) > 0]
        if e:
            eng[h] = sum(e) / len(e)
        med[h] = statistics.median([fin(r["views"]) for r in v])

    def pct_rank(m, h):
        if h not in m or len(m) < 2:
            return None
        vals = sorted(m.values())
        below = sum(1 for x in vals if x < m[h])
        return below / (len(vals) - 1) * 100

    ctx = {"n_creators": len(eng), "eng_rank": {}, "view_rank": {}, "related": {}}
    for h in rows:
        r = pct_rank(eng, h)
        if r is not None:
            ctx["eng_rank"][h] = r
        r2 = pct_rank(med, h)
        if r2 is not None:
            ctx["view_rank"][h] = r2

    handles = [h for h in creators if len([r for r in rows.get(h, []) if fin(r["views"]) > 0]) >= 3]
    for h in handles:
        peers = []
        for o in handles:
            if o == h or eng.get(o) is None or eng.get(h) is None:
                continue
            peers.append((abs(eng[o] - eng[h]), o))
        peers.sort()
        ctx["related"][h] = [((o), (creators[o].get("nickname") or o).split("|")[0].strip())
                             for _, o in peers[:3]]

    import sys as _sys
    only = set(_sys.argv[1:]) if len(_sys.argv) > 1 else None
    if only:
        handles = [h for h in handles if h in only]
    wrote = 0
    for h in handles:
        html_out = build(h, creators, rows, figs, ctx)
        open(os.path.join(P, MAP.get(h, h) + ".html"), "w").write(html_out)
        wrote += 1
    print("wrote", wrote, "creator pages")


if __name__ == "__main__":
    main()
