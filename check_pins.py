"""Guard: every pin-feed row must point at its own creator's avatar.

Usage: python3 check_pins.py <feed.json>
Feed rows need: slug, title, desc, avatar.
Fails nonzero with a clear message on the first violation class found.
"""
import json
import os
import sys

AVDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "avatars")


def check(feed_path):
    rows = json.load(open(feed_path))
    errors = []
    for i, r in enumerate(rows):
        slug = r.get("slug", "")
        title = r.get("title", "")
        desc = r.get("desc", "")
        avatar = r.get("avatar", "")
        where = f"row {i} slug={slug!r}"
        apath = os.path.join(AVDIR, avatar)
        if not os.path.isfile(apath):
            errors.append(f"{where}: avatar file missing: {avatar}")
            continue
        base = avatar[:-4] if avatar.endswith(".jpg") else avatar
        key = base.replace("_", "").lower()
        hay = [slug.replace("_", "").lower(), title.lower(), desc.lower()]
        if not any(key in h for h in hay):
            errors.append(
                f"{where}: avatar {avatar!r} (key {key!r}) matches neither "
                f"slug, title nor desc — wrong-creator image?"
            )
        if "@miarosemcgrath" in desc.lower() and slug != "miarosemcgrath":
            errors.append(
                f"{where}: desc mentions @miarosemcgrath but slug is not "
                f"miarosemcgrath — copy-paste desc?"
            )
    return errors


def main():
    if len(sys.argv) != 2:
        print("usage: check_pins.py <feed.json>", file=sys.stderr)
        return 2
    errors = check(sys.argv[1])
    for e in errors:
        print("PIN-GUARD VIOLATION:", e)
    if errors:
        print(f"check_pins: {len(errors)} violation(s) in {sys.argv[1]}")
        return 1
    print(f"check_pins: OK ({sys.argv[1]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
