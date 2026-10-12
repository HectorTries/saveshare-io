#!/usr/bin/env python3
"""Validate a SaveShare blog post against BLOG_RECIPE.md hard rules.

Usage:
    python3 check_post.py blog/<file>.html

Checks:
    1. Body word count 1500-2000 (visible text inside <main>...</main>)
    2. Distinct q-mention creators >= 4
    3. No <ul> / <ol> lists
    4. No em dashes (U+2014) or en dashes (U+2013)

Prints PASS/FAIL per check. Exit 0 if all pass, 1 otherwise.
"""
import re
import sys

EM_DASH = "\u2014"
EN_DASH = "\u2013"


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 check_post.py blog/<file>.html")
        sys.exit(2)
    path = sys.argv[1]
    try:
        html = open(path, encoding="utf-8").read()
    except OSError as e:
        print(f"FAIL: cannot read {path}: {e}")
        sys.exit(1)

    ok = True

    # 1. Body word count inside <main>
    m = re.search(r"<main.*?>(.*?)</main>", html, re.S | re.I)
    if not m:
        print("FAIL: words: no <main> block found (need 1500-2000)")
        ok = False
        wc = 0
    else:
        text = re.sub(r"<[^>]+>", " ", m.group(1))
        text = re.sub(r"\s+", " ", text).strip()
        wc = len(text.split()) if text else 0
        if 1500 <= wc <= 2000:
            print(f"PASS: words: {wc} (need 1500-2000)")
        else:
            print(f"FAIL: words: {wc} (need 1500-2000)")
            ok = False

    # 2. Distinct q-mention creators
    handles = set(re.findall(r'q-mention.*?p/([^"/.]+)\.html', html))
    # fallback: any creator profile link counts only if q-mention present
    n = len(handles)
    if n >= 4:
        print(f"PASS: creators: {n} distinct q-mention ({sorted(handles)})")
    else:
        print(f"FAIL: creators: {n} distinct q-mention {sorted(handles)} (need >=4)")
        ok = False

    # 3. No lists
    has_ul = re.search(r"<ul[\s>]", html, re.I)
    has_ol = re.search(r"<ol[\s>]", html, re.I)
    if not has_ul and not has_ol:
        print("PASS: lists: no <ul>/<ol> found")
    else:
        found = []
        if has_ul:
            found.append("<ul>")
        if has_ol:
            found.append("<ol>")
        print(f"FAIL: lists: found {' '.join(found)} (need none)")
        ok = False

    # 4. No em/en dashes
    n_em = html.count(EM_DASH)
    n_en = html.count(EN_DASH)
    if n_em == 0 and n_en == 0:
        print("PASS: dashes: no em/en dashes found")
    else:
        print(f"FAIL: dashes: em={n_em} en={n_en} (need 0)")
        ok = False

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
