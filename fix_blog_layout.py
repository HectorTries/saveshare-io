#!/usr/bin/env python3
"""SaveShare blog layout fix: hero pull-quote, avatar quote units, merged Via blocks,
'All money advice' -> 'Blog', zero em/en dashes. Applies to all blog/*.html (not index)."""
import re, os, glob

BLOG = "/home/mint/.openclaw/workspace/saveshare-io/blog"
P = "/home/mint/.openclaw/workspace/saveshare-io/p"
AV = "/home/mint/.openclaw/workspace/saveshare-io/avatars"

# avatar file lookup
av_files = {f.lower(): f for f in os.listdir(AV)}
def avatar_for(handle):
    for cand in [handle, handle.replace("005", "_005"), handle.replace("talks", "talksu"),
                 handle + "2", handle.replace("insights", "")]:
        if (cand + ".jpg").lower() in av_files:
            return "../avatars/" + av_files[(cand + ".jpg").lower()]
    # fuzzy: any file starting with handle-ish
    for k, v in av_files.items():
        if k.startswith(handle[:6]):
            return "../avatars/" + v
    return None

# followers + display name from p/*.html
META = {}
for f in glob.glob(f"{P}/*.html"):
    h = os.path.basename(f).replace(".html", "")
    src = open(f).read()
    m = re.search(r'([\d.,]+[KM]?)</strong>\s*<span>Followers', src)
    t = re.search(r'<title>([^(@<]+)', src)
    META[h] = {"followers": m.group(1) if m else "?", "name": t.group(1).strip() if t else h}

CSS_ADD = """
.pullquote{font-family:'Playfair Display',Georgia,serif;font-size:clamp(22px,3vw,30px);line-height:1.35;border-left:5px solid var(--teal);background:#fff;border-radius:0 16px 16px 0;padding:24px 28px;margin:28px 0;font-style:italic}
.pullquote .pq-who{display:block;font-family:'Inter',system-ui,sans-serif;font-style:normal;font-size:14px;color:var(--muted);margin-top:12px}
.quote-unit{background:#fff;border:1px solid var(--line);border-radius:16px;padding:20px 22px;margin:20px 0}
.q-head{display:flex;align-items:center;gap:12px;margin-bottom:10px}
.q-head img{width:48px;height:48px;border-radius:50%;object-fit:cover;flex-shrink:0}
.q-avatar-fallback{width:48px;height:48px;border-radius:50%;background:var(--teal);color:#fff;font-weight:800;font-size:20px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.q-head strong a{color:var(--ink);text-decoration:none}
.q-head strong a:hover{color:var(--teal)}
.q-head .q-fol{display:block;font-size:12px;color:var(--muted);font-weight:400}
.quote-unit .q-text{font-family:'Playfair Display',Georgia,serif;font-size:19px;line-height:1.5;margin:6px 0 10px}
.quote-unit .q-src{font-size:13px;color:var(--muted)}
.quote-unit .q-src a{color:var(--teal)}"""

files = sorted(glob.glob(f"{BLOG}/*.html"))
report = []
for fp in files:
    if os.path.basename(fp) == "index.html":
        continue
    src = open(fp).read()

    # 1. CSS additions (once)
    if ".pullquote" not in src:
        src = src.replace("ul.tick li::before{content:\"✓ \";color:#0F766E;font-weight:700}",
                          "ul.tick li::before{content:\"✓ \";color:#0F766E;font-weight:700}" + CSS_ADD)

    # 2. Back link
    src = src.replace("← All money advice", "← Blog")

    # 3. en/em dashes -> commas/colons (targeted, safe spots)
    src = src.replace(" – ", ", ").replace("–", "-").replace("—", ", ")

    # 4. Parse paragraphs
    paras = re.findall(r'<p(?: class="src")?>(.*?)</p>', src, re.S)
    # find back-link para index and disclaimer index
    out = []
    entries = []  # (handle, name, video_url, [quotes], narrative_html)
    pending_narr = None
    first_para = True
    for par in paras:
        m_via = re.match(r'\s*Via <a href="\.\./p/(\w+)\.html">([^<]+)</a> \(<a href="([^"]+)"[^>]*>TikTok source[^<]*</a>\)\s*$', par)
        if m_via:
            h, name, url = m_via.groups()
            _clean = re.sub(r'<[^>]+>', '', pending_narr or "")
            quotes = [q for q in re.findall(r'"([^"]{15,400})"', _clean) if '../p/' not in q and 'http' not in q and 'tiktok.com' not in q.lower()]
            entries.append({"h": h, "name": name, "url": url, "quotes": quotes, "narr": pending_narr or ""})
            pending_narr = None
        else:
            if pending_narr is not None:
                out.append(("narr", pending_narr))
            pending_narr = par
    if pending_narr is not None:
        out.append(("narr", pending_narr))
    # out has narrs in order; entries align: each entry's narr is the narr just before it.
    # Rebuild: walk original order. Simpler: rebuild body from scratch.
    # Reconstruct sequence: iterate paras again building ordered list
    seq = []
    pend = None
    for par in paras:
        m_via = re.match(r'\s*Via <a href="\.\./p/(\w+)\.html">([^<]+)</a> \(<a href="([^"]+)"[^>]*>TikTok source[^<]*</a>\)\s*$', par)
        if m_via:
            h, name, url = m_via.groups()
            _clean2 = re.sub(r'<[^>]+>', '', pend or "")
            quotes = [q for q in re.findall(r'"([^"]{15,400})"', _clean2) if '../p/' not in q and 'http' not in q and 'tiktok.com' not in q.lower()]
            seq.append({"type": "entry", "h": h, "name": name, "url": url, "quotes": quotes, "narr": pend or ""})
            pend = None
        else:
            if pend is not None:
                seq.append({"type": "narr", "html": pend})
            pend = par
    if pend is not None:
        seq.append({"type": "narr", "html": pend})

    # merge consecutive entries same handle+url
    merged = []
    for s in seq:
        if s["type"] == "entry" and merged and merged[-1]["type"] == "entry" \
           and merged[-1]["h"] == s["h"] and merged[-1]["url"] == s["url"]:
            merged[-1]["quotes"].extend(s["quotes"])
            # append narrative text too (strip to plain flow)
            merged[-1]["narr"] += " " + s["narr"]
        else:
            merged.append(dict(s))

    def unit(e):
        meta = META.get(e["h"], {"followers": "?", "name": e["name"]})
        av = avatar_for(e["h"])
        img = f'<img src="{av}" alt="{e["name"]}">' if av else \
              f'<div class="q-avatar-fallback">{e["name"][:1]}</div>'
        qs = "".join(f'<p class="q-text">"{q}"</p>' for q in e["quotes"]) or \
             f'<p class="q-text">{e["narr"][:200]}</p>'
        return (f'<div class="quote-unit"><div class="q-head"><a href="../p/{e["h"]}.html">{img}</a>'
                f'<div><strong><a href="../p/{e["h"]}.html">{e["name"]}</a></strong>'
                f'<span class="q-fol">{meta["followers"]} followers on TikTok</span></div></div>'
                f'{qs}<p class="q-src"><a href="{e["url"]}" target="_blank" rel="noopener">Watch on TikTok</a></p></div>')

    # hero pull-quote: first quote in post + its creator
    hero = ""
    hero_done = False
    for s in merged:
        if s["type"] == "entry" and s["quotes"]:
            hero = (f'<div class="pullquote">"{s["quotes"][0]}"'
                    f'<span class="pq-who">, <a href="../p/{s["h"]}.html">{s["name"]}</a></span></div>')
            break

    body_parts = []
    for i, s in enumerate(merged):
        if s["type"] == "narr":
            # back-link para: append hero after it
            if i == 0 and "← Blog" in s["html"]:
                body_parts.append(f'<p>{s["html"]}</p>')
                if hero:
                    body_parts.append(hero)
            else:
                body_parts.append(f'<p>{s["html"]}</p>')
        else:
            # narrative context (strip quoted strings now shown in unit? keep text, remove quote marks content dup)
            narr = s["narr"]
            if s["quotes"]:
                # remove the quoted strings from narrative to avoid duplication
                for q in s["quotes"]:
                    narr = narr.replace(f'"{q}"', "")
                narr = re.sub(r'\s{2,}', ' ', narr).strip()
            # drop narrative if it's now empty or just a creator-name stub
            if narr and len(re.sub(r'<[^>]+>', '', narr).strip()) > 40:
                body_parts.append(f'<p>{narr}</p>')
            body_parts.append(unit(s))

    new_body = "\n".join(body_parts)
    # replace old body: everything between <main><div class="wrap"> and </div></main>
    src = re.sub(r'(<main><div class="wrap">\n).*?(\n</div></main>)',
                 lambda m: m.group(1) + new_body + m.group(2), src, flags=re.S)

    open(fp, "w").write(src)
    n_units = sum(1 for s in merged if s["type"] == "entry")
    n_quotes = sum(len(s["quotes"]) for s in merged if s["type"] == "entry")
    report.append(f"{os.path.basename(fp)}: {n_units} units, {n_quotes} quotes, hero={'yes' if hero else 'NO QUOTE FOUND'}")

print("\n".join(report))
