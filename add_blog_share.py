#!/usr/bin/env python3
"""Add a share bar (Facebook, X, WhatsApp, Pinterest, copy link) to blog posts."""
import os, re, glob, html, json

REPO = os.path.dirname(os.path.abspath(__file__))
BLOG = os.path.join(REPO, "blog")
SITE = "https://saveshare.io"


def share_bar(url, title):
    u = html.escape(url, quote=True)
    t = html.escape(title, quote=True)
    ue = html.escape(url.replace("&", "%26").replace(" ", "%20"), quote=True)
    te = html.escape(title.replace(" ", "%20"), quote=True)
    return f"""<div class="share-bar" data-share-url="{u}" data-share-title="{t}">
<span class="share-label">Share this</span>
<a class="share-btn fb" href="https://www.facebook.com/sharer/sharer.php?u={ue}" target="_blank" rel="noopener" aria-label="Share on Facebook"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M13.5 22v-8h2.7l.4-3.1h-3.1V8.9c0-.9.3-1.5 1.6-1.5h1.6V4.6c-.3 0-1.3-.1-2.4-.1-2.4 0-4 1.5-4 4.1v2.3H7.2V14h2.7v8h3.6z"/></svg>Facebook</a>
<a class="share-btn x" href="https://twitter.com/intent/tweet?url={ue}&text={te}" target="_blank" rel="noopener" aria-label="Share on X"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M17.5 3h3.2l-7 8 8.2 10h-6.4l-5-6.1L4.7 21H1.5l7.5-8.6L1.2 3h6.6l4.5 5.6L17.5 3zm-1.1 16h1.8L7.6 4.8H5.7L16.4 19z"/></svg>X</a>
<a class="share-btn wa" href="https://wa.me/?text={te}%20{ue}" target="_blank" rel="noopener" aria-label="Share on WhatsApp"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a9.9 9.9 0 0 0-8.5 15L2 22l5.2-1.4A9.9 9.9 0 1 0 12 2zm0 18a8 8 0 0 1-4.1-1.1l-.3-.2-3.1.8.8-3-.2-.3A8 8 0 1 1 12 20zm4.5-5.9c-.2-.1-1.4-.7-1.6-.8-.2-.1-.4-.1-.5.1l-.7.9c-.1.2-.3.2-.5.1a6.5 6.5 0 0 1-1.9-1.2 7.2 7.2 0 0 1-1.3-1.7c-.1-.2 0-.4.1-.5l.5-.6c.1-.2.1-.3 0-.5l-.7-1.7c-.2-.4-.4-.4-.5-.4h-.5c-.2 0-.5.1-.7.3-.2.3-.8.8-.8 1.9s.8 2.2.9 2.4a9 9 0 0 0 3.5 3.1c.5.2.9.4 1.2.5.5.2 1 .1 1.4.1.4-.1 1.3-.5 1.5-1.1.2-.5.2-1 .1-1.1z"/></svg>WhatsApp</a>
<a class="share-btn pin" href="https://www.pinterest.com/pin/create/button/?url={ue}&description={te}" target="_blank" rel="noopener" aria-label="Save on Pinterest"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a10 10 0 0 0-3.6 19.3c-.1-.7-.2-1.8 0-2.6l1.2-5s-.3-.6-.3-1.5c0-1.4.8-2.5 1.9-2.5.9 0 1.3.7 1.3 1.5 0 .9-.6 2.2-.9 3.4-.2 1 .5 1.9 1.5 1.9 1.8 0 3.2-1.9 3.2-4.6 0-2.4-1.7-4.1-4.2-4.1a4.4 4.4 0 0 0-4.6 4.4c0 .9.3 1.8.8 2.3l.1.4-.3 1.2c0 .2-.2.2-.4.1-1.3-.6-2-2.4-2-3.9 0-3.2 2.3-6.1 6.7-6.1 3.5 0 6.3 2.5 6.3 5.9 0 3.5-2.2 6.3-5.3 6.3-1 0-2-.5-2.3-1.2l-.6 2.4c-.2.9-.8 2-1.2 2.6A10 10 0 1 0 12 2z"/></svg>Pinterest</a>
<button class="share-btn copy" type="button" aria-label="Copy link"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 13a5 5 0 0 0 7.1 0l1.4-1.4a5 5 0 0 0-7.1-7.1L10 5.9"/><path d="M14 11a5 5 0 0 0-7.1 0L5.5 12.4a5 5 0 0 0 7.1 7.1L14 18.1"/></svg><span class="copy-text">Copy link</span></button>
</div>"""

CSS = """
/* Blog share bar */
.share-bar{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:0 0 26px;padding:14px 16px;background:#fff;border:1px solid var(--line);border-radius:14px}
.share-label{font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-right:4px}
.share-btn{display:inline-flex;align-items:center;gap:7px;font-size:13px;font-weight:600;padding:8px 14px;border-radius:999px;border:1px solid var(--line);background:#faf8f4;color:var(--ink);text-decoration:none;cursor:pointer;line-height:1}
.share-btn svg{width:15px;height:15px;fill:none;stroke:currentColor;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}
.share-btn.fb{background:#1877F2;border-color:#1877F2;color:#fff}
.share-btn.fb svg{fill:#fff;stroke:none}
.share-btn.x{background:#0f1419;border-color:#0f1419;color:#fff}
.share-btn.x svg{fill:#fff;stroke:none}
.share-btn.wa{background:#25D366;border-color:#25D366;color:#062b16}
.share-btn.wa svg{fill:#062b16;stroke:none}
.share-btn.pin{background:#e60023;border-color:#e60023;color:#fff}
.share-btn.pin svg{fill:#fff;stroke:none}
.share-btn:hover{opacity:.9}
.share-btn.copied{background:#22b07d;border-color:#22b07d;color:#fff}
@media(max-width:560px){.share-btn{font-size:12px;padding:7px 11px}.share-label{width:100%}}
"""

JS = """
<script>
(function(){
  document.querySelectorAll('.share-bar').forEach(function(bar){
    var btn=bar.querySelector('.copy');
    if(!btn) return;
    btn.addEventListener('click',function(){
      var url=bar.getAttribute('data-share-url')||location.href;
      var txt=btn.querySelector('.copy-text');
      function done(){ btn.classList.add('copied'); txt.textContent='Copied';
        setTimeout(function(){ btn.classList.remove('copied'); txt.textContent='Copy link'; },1800); }
      if(navigator.share && window.innerWidth<700){
        navigator.share({url:url,title:bar.getAttribute('data-share-title')||document.title})
          .catch(function(){ if(navigator.clipboard) navigator.clipboard.writeText(url).then(done); });
      } else if(navigator.clipboard){
        navigator.clipboard.writeText(url).then(done);
      } else {
        var t=document.createElement('textarea'); t.value=url; document.body.appendChild(t);
        t.select(); document.execCommand('copy'); t.remove(); done();
      }
    });
  });
})();
</script>
"""


def main():
    files = [f for f in sorted(glob.glob(os.path.join(BLOG, "*.html")))
             if os.path.basename(f) != "index.html"]
    added = 0
    for f in files:
        h = open(f, encoding="utf-8", errors="ignore").read()
        if "share-bar" in h:
            continue
        m = re.search(r'<link rel="canonical" href="([^"]+)"', h)
        url = m.group(1) if m else f"{SITE}/blog/{os.path.basename(f)}"
        m = re.search(r"<h1>(.*?)</h1>", h, re.S)
        title = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else "SaveShare.io"
        bar = share_bar(url, title)
        # place after the hero figure when present, else at the top of main
        if re.search(r'</figure>', h):
            h = re.sub(r'(</figure>)', r'\1\n' + bar, h, count=1)
        else:
            h = h.replace('<main data-blog-region', bar + '\n<main data-blog-region', 1)
        # styles + script once
        h = h.replace("</head>", f"<style>{CSS}</style>\n</head>", 1)
        h = h.replace("</body>", JS + "\n</body>", 1)
        open(f, "w", encoding="utf-8").write(h)
        added += 1
    print("share bar added to", added, "posts")


if __name__ == "__main__":
    main()
