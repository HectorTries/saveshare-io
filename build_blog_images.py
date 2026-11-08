#!/usr/bin/env python3
"""Generate 1200x630 social/OG cards for every SaveShare blog post.

Also injects og:image + twitter:image + a visible hero figure into each post,
so Facebook shares stop showing a blank card.
"""
import os, re, glob, html, textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter

REPO = os.path.dirname(os.path.abspath(__file__))
BLOG = os.path.join(REPO, "blog")
OUT = os.path.join(BLOG, "img")
SITE = "https://saveshare.io"
os.makedirs(OUT, exist_ok=True)

W, H = 1200, 630
TEAL, TEAL_DARK, INK = (15, 118, 110), (19, 78, 74), (250, 250, 248)
ACCENT = (232, 245, 233)

F_SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
F_SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
F_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def gradient():
    img = Image.new("RGB", (W, H), TEAL)
    top, bottom = TEAL, TEAL_DARK
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    # soft light blob top-right
    overlay = Image.new("RGB", (W, H), (0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.ellipse([W - 420, -260, W + 160, 320], fill=(255, 255, 255))
    overlay = overlay.filter(ImageFilter.GaussianBlur(120))
    img = Image.blend(img, overlay, 0.10)
    return img


def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def extract(path):
    h = open(path, encoding="utf-8", errors="ignore").read()
    title = re.search(r"<h1>(.*?)</h1>", h, re.S)
    title = html.unescape(re.sub(r"<[^>]+>", "", title.group(1))).strip() if title else ""
    if not title:
        t = re.search(r"<title>(.*?)</title>", h, re.S)
        title = html.unescape(t.group(1)).split("|")[0].strip() if t else "SaveShare.io"
    dek = re.search(r'<meta property="og:description" content="([^"]*)"', h)
    dek = html.unescape(dek.group(1)) if dek else ""
    cat = re.search(r'<div style="display:inline-block;background:rgba\(255,255,255,\.15\)[^>]*>([^<]+)</div>', h)
    cat = html.unescape(cat.group(1)).strip() if cat else "MONEY ADVICE"
    av = re.search(r'<img src="\.\./avatars/([^"]+)"', h)
    avatar = os.path.join(REPO, "avatars", av.group(1)) if av else None
    return title, dek, cat, avatar


def render(title, dek, cat, avatar_path, out_path):
    img = gradient()
    d = ImageDraw.Draw(img)

    # brand
    d.text((72, 54), "SaveShare", font=font(F_SANS_B, 30), fill=(255, 255, 255))
    x = 72 + d.textlength("SaveShare", font=font(F_SANS_B, 30))
    d.text((x, 54), ".io", font=font(F_SANS_B, 30), fill=(200, 230, 225))

    # category pill
    f_cat = font(F_SANS_B, 19)
    cw = d.textlength(cat.upper(), font=f_cat)
    d.rounded_rectangle([72, 112, 72 + cw + 34, 152], radius=20, fill=(255, 255, 255, 30) if False else (24, 96, 90))
    d.text((89, 121), cat.upper(), font=f_cat, fill=(224, 242, 241))

    # headline
    max_w = W - 144 - (220 if avatar_path else 0)
    f_h = font(F_SERIF, 62)
    lines = wrap(d, title, f_h, max_w)
    while len(lines) > 4 and f_h.size > 44:
        f_h = font(F_SERIF, f_h.size - 4)
        lines = wrap(d, title, f_h, max_w)
    y = 196
    for line in lines[:4]:
        d.text((72, y), line, font=f_h, fill=INK)
        y += int(f_h.size * 1.22)

    # dek
    if dek:
        f_d = font(F_SANS, 26)
        dlines = wrap(d, dek, f_d, max_w)
        y += 10
        for line in dlines[:2]:
            if y + 36 > H - 130:
                break
            d.text((72, y), line, font=f_d, fill=(214, 235, 231))
            y += 36

    # avatar
    if avatar_path and os.path.isfile(avatar_path):
        try:
            size = 168
            av = Image.open(avatar_path).convert("RGB")
            av = av.resize((size, size), Image.LANCZOS)
            mask = Image.new("L", (size, size), 0)
            ImageDraw.Draw(mask).ellipse([0, 0, size, size], fill=255)
            img.paste(av, (W - 72 - size, 150), mask)
            d.ellipse([W - 72 - size - 6, 144, W - 72 + 6, 150 + size + 6],
                      outline=(255, 255, 255), width=4)
        except Exception:
            pass

    # footer rule + url
    d.line([(72, H - 96), (W - 72, H - 96)], fill=(255, 255, 255), width=1)
    d.text((72, H - 76), "saveshare.io  ·  sourced UK and US money creators", font=font(F_SANS, 22), fill=(214, 235, 231))
    d.text((W - 72 - 220, H - 76), "Every figure linked", font=font(F_SANS_B, 22), fill=(255, 255, 255))

    img.save(out_path, "JPEG", quality=88, optimize=True, progressive=True)


def inject(path, img_rel, title):
    h = open(path, encoding="utf-8", errors="ignore").read()
    slug = os.path.basename(path)
    if "og:image" in h and "post-hero" in h:
        return False
    url = f"{SITE}/blog/{img_rel}"
    tags = (f'<meta property="og:image" content="{url}">\n'
            f'<meta property="og:image:width" content="1200">\n'
            f'<meta property="og:image:height" content="630">\n'
            f'<meta property="og:image:alt" content="{html.escape(title)[:150]}">\n'
            f'<meta name="twitter:image" content="{url}">\n')
    if 'property="og:image"' not in h:
        h = h.replace('<meta name="twitter:card" content="summary_large_image">',
                      tags + '<meta name="twitter:card" content="summary_large_image">', 1)
        if url not in h:  # no twitter card tag present
            h = h.replace("</head>", tags + "</head>", 1)
    # schema image
    if '"image"' not in h:
        h = re.sub(r'("@type": "Article",)', r'\1 "image": "' + url + '",', h, count=1)
    # visible hero
    if "post-hero" not in h:
        fig = (f'<figure class="post-hero"><img src="{img_rel}" alt="{html.escape(title)[:150]}" '
               f'width="1200" height="630" loading="eager"></figure>\n')
        h = h.replace('<main data-blog-region', fig + '<main data-blog-region', 1)
    open(path, "w", encoding="utf-8").write(h)
    return True


def main():
    files = sorted(glob.glob(os.path.join(BLOG, "*.html")))
    made = injected = 0
    for f in files:
        slug = os.path.basename(f)
        if slug == "index.html":
            continue
        title, dek, cat, avatar = extract(f)
        name = slug[:-5] + ".jpg"
        out = os.path.join(OUT, name)
        if not os.path.isfile(out):
            render(title, dek, cat, avatar, out)
            made += 1
        if inject(f, "img/" + name, title):
            injected += 1
    print(f"rendered {made} images, injected into {injected} posts")


if __name__ == "__main__":
    main()
