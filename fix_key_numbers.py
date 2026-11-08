#!/usr/bin/env python3
"""Rebuild the 'Key numbers' aside on blog posts from whole sentences.

The old blocks were sliced +-120 characters around each figure, so every line
started and ended mid-word. This rebuilds them from the paragraph text: one
full sentence per figure, trimmed at a word boundary.
"""
import os, re, glob, html

REPO = os.path.dirname(os.path.abspath(__file__))
BLOG = os.path.join(REPO, "blog")

MONEY_RE = re.compile(
    r"(?:£|\$)\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:million|billion|k))?"
    r"|(?:\d[\d,]*(?:\.\d+)?)\s?(?:pounds|dollars|grand)\b",
    re.I,
)


def body_text(h):
    m = re.search(r"<main[^>]*>(.*?)</main>", h, re.S)
    t = m.group(1) if m else h
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<li[^>]*>", ". ", t)
    t = re.sub(r"</p>|</h[1-6]>|</li>", ". ", t, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    t = re.sub(r"\s+", " ", t)
    return t


def sentences(t):
    parts = re.split(r"(?<=[.!?])\s+", t)
    return [p.strip() for p in parts if len(p.split()) >= 6]


def amount_key(m):
    s = m.group(0).lower().replace(",", "")
    num = re.search(r"\d+(?:\.\d+)?", s)
    if not num:
        return s
    v = float(num.group(0))
    if s.rstrip().endswith(("k",)) or " k" in s:
        v *= 1000
    if "million" in s:
        v *= 1_000_000
    return round(v)


def trim(s, limit=190):
    if len(s) <= limit:
        return s
    cut = s[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(",;:") + "..."


def build_entries(text):
    """One entry per sentence: first figure in the sentence becomes the label."""
    out, used_desc, used_amounts = [], set(), set()
    for s in sentences(text):
        # strip creator-section headings that leak into the text
        s = re.sub(r"^[A-Z][\w'’.-]+(?:\s+[A-Z][\w'’.-]+){0,3}\s+@[\w.]+\s*", "", s).strip()
        wc = len(s.split())
        if wc < 7 or wc > 40:
            continue
        m = MONEY_RE.search(s)
        if not m or len(m.group(0)) < 4:
            continue
        ak = amount_key(m)
        if ak in used_amounts:
            continue
        key = re.sub(r"[^a-z0-9]", "", s.lower())[:80]
        if key in used_desc:
            continue
        used_desc.add(key)
        used_amounts.add(ak)
        s = re.sub(r"\.{2,}\s*$", ".", s)
        out.append((m.group(0).strip(), s))
        if len(out) >= 6:
            break
    return out


def render(entries):
    lis = "".join(
        f"<li><strong>{html.escape(lab)}</strong>: {html.escape(desc)}</li>" for lab, desc in entries
    )
    return f'<aside class="key-numbers" aria-label="Key numbers"><h2>Key numbers</h2><ul>{lis}</ul></aside>'


def main():
    files = sorted(f for f in glob.glob(os.path.join(BLOG, "*.html"))
                   if os.path.basename(f) != "index.html")
    fixed = added = 0
    for f in files:
        h = open(f, encoding="utf-8", errors="ignore").read()
        txt = body_text(h)
        entries = build_entries(txt)
        if not entries:
            continue
        block = render(entries)
        if '<aside class="key-numbers"' in h:
            h2 = re.sub(r'<aside class="key-numbers".*?</aside>', block, h, count=1, flags=re.S)
            if h2 != h:
                open(f, "w", encoding="utf-8").write(h2)
                fixed += 1
        else:
            # place after the byline, before the hero figure
            anchor = '<figure class="post-hero">'
            if anchor in h:
                h2 = h.replace(anchor, block + "\n" + anchor, 1)
            else:
                h2 = re.sub(r"(<p class=\"byline\".*?</p>)", r"\1" + block, h, count=1, flags=re.S)
            if h2 != h:
                open(f, "w", encoding="utf-8").write(h2)
                added += 1
    print(f"rebuilt {fixed}, added {added}")


if __name__ == "__main__":
    main()
