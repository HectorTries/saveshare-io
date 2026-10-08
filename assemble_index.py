#!/usr/bin/env python3
"""Assemble new index.html: head/nav/hero/controls + generated cards + footer.
Reads index.html (old) for tail sections, /tmp/cards.html, /tmp/feat.html, /tmp/rebuild_vars.txt."""
import re

old = open('index.html').read()
cards = open('/tmp/cards.html').read()
feat = open('/tmp/feat.html').read()
total_s, nfig = open('/tmp/rebuild_vars.txt').read().split()

GA = """<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-3T9QS61KD0"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-3T9QS61KD0');
</script>"""

CSS = """@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@700;800&display=swap');
:root{--teal:#0F766E;--teal-dark:#115E59;--teal-soft:#E0F2F1;--ink:#0F172A;--muted:#475569;--line:#E2E8F0;--bg:#F8FAFC}
*{box-sizing:border-box}
body{margin:0;font-family:'Inter',system-ui,sans-serif;background:var(--bg);color:var(--ink);line-height:1.6}
h1,h2{font-family:'Playfair Display',Georgia,serif;line-height:1.15;margin:0}
.wrap{max-width:1100px;margin:0 auto;padding:0 24px}
nav{background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:10}
nav .wrap{display:flex;align-items:center;justify-content:space-between;padding-top:14px;padding-bottom:14px}
.logo{font-weight:800;font-size:20px;color:var(--teal);text-decoration:none}
.logo span{color:var(--ink)}
.nav-links{display:flex;gap:24px;align-items:center}
.nav-links a{color:var(--muted);text-decoration:none;font-size:15px;font-weight:500}
.nav-links a:hover{color:var(--teal)}
.btn{display:inline-block;background:var(--teal);color:#fff;border:none;padding:12px 28px;font-size:15px;font-weight:600;border-radius:9999px;cursor:pointer;text-decoration:none;transition:all .2s ease;min-height:44px}
.btn:hover{background:var(--teal-dark);transform:translateY(-1px)}
.btn-outline{background:#fff;color:var(--teal);border:2px solid var(--teal)}
.btn-outline:hover{background:var(--teal-soft)}
@media(max-width:640px){.nav-links a:not(.btn){display:none}}
.hero{background:linear-gradient(135deg,#0F766E 0%,#134E4A 100%);color:#fff;padding:64px 0 72px;text-align:center}
.hero .badge{display:inline-block;background:rgba(255,255,255,.15);color:#fff;font-size:13px;font-weight:600;padding:6px 18px;border-radius:9999px;letter-spacing:.5px;margin-bottom:20px}
.hero h1{font-size:clamp(34px,5vw,56px);max-width:760px;margin:0 auto 18px}
.hero p{font-size:19px;opacity:.9;max-width:620px;margin:0 auto 28px}
.hero-ctas{display:flex;gap:14px;justify-content:center;flex-wrap:wrap}
.hero-ctas .btn-outline{border-color:#fff;color:#fff;background:transparent}
.hero-ctas .btn-outline:hover{background:rgba(255,255,255,.12)}
.hero .btn-light{background:#fff;color:var(--teal)}
.hero-stats{display:flex;gap:40px;justify-content:center;margin-top:36px;flex-wrap:wrap}
.hero-stats div{text-align:center}
.hero-stats strong{display:block;font-size:28px;font-weight:800}
.hero-stats span{font-size:14px;opacity:.8}
.feat-row{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-top:28px}
.feat-card{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.25);color:#fff;text-decoration:none;border-radius:12px;padding:10px 18px;text-align:left;min-height:44px}
.feat-card:hover{background:rgba(255,255,255,.2)}
.feat-card strong{display:block;font-size:15px}
.feat-card span{font-size:12px;opacity:.85}
section{padding:72px 0}
.section-head{text-align:center;max-width:640px;margin:0 auto 32px}
.section-head h2{font-size:32px;margin-bottom:12px}
.section-head p{color:var(--muted);font-size:17px}
.steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:24px}
.step{background:#fff;border:1px solid var(--line);border-radius:16px;padding:32px 28px;box-shadow:0 10px 15px -3px rgb(15 23 42/.05)}
.step .num{width:40px;height:40px;background:var(--teal-soft);color:var(--teal);border-radius:9999px;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:18px;margin-bottom:16px}
.step h3{margin:0 0 8px;font-size:18px}
.step p{margin:0;color:var(--muted);font-size:15px}
.controls{display:flex;gap:12px;flex-wrap:wrap;justify-content:center;margin-bottom:28px}
.controls input[type=search]{padding:12px 18px;font-size:15px;border:1px solid var(--line);border-radius:9999px;min-width:220px;min-height:44px;font-family:inherit}
.controls select{padding:12px 16px;font-size:15px;border:1px solid var(--line);border-radius:9999px;background:#fff;font-family:inherit;min-height:44px}
.controls label{display:flex;align-items:center;gap:8px;font-size:15px;color:var(--muted);min-height:44px}
.controls input[type=checkbox]{width:20px;height:20px;accent-color:var(--teal)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:20px}
.card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:24px;box-shadow:0 10px 15px -3px rgb(15 23 42/.05);transition:transform .2s ease,box-shadow .2s ease;display:flex;flex-direction:column;position:relative}
.card:hover{transform:translateY(-4px);box-shadow:0 20px 25px -5px rgb(15 23 42/.1)}
.card .avatar{width:56px;height:56px;border-radius:9999px;background:var(--teal);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:22px;margin-bottom:14px;object-fit:cover}
.card .fallback-avatar{width:56px;height:56px;border-radius:9999px;background:var(--teal);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:22px;margin-bottom:14px}
.tier{position:absolute;top:20px;right:20px;font-size:11px;font-weight:700;color:var(--teal-dark);background:var(--teal-soft);padding:3px 10px;border-radius:9999px}
.card h3{margin:0;font-size:19px;font-family:'Inter',sans-serif;font-weight:700}
.card h3 a{color:inherit;text-decoration:none;display:block;padding:6px 0}
.card .handle{margin:2px 0 12px}
.card .handle a{color:var(--teal);font-weight:600;font-size:15px;text-decoration:none;display:inline-block;padding:6px 0;min-height:44px}
.card .handle a:hover{text-decoration:underline}
.card .bio{font-size:14px;color:var(--muted);margin:0 0 14px;flex:1}
.card .figures{border-top:1px solid var(--line);padding-top:14px;display:flex;gap:20px}
.card .figures div strong{display:block;font-size:17px}
.card .figures div span{font-size:12px;color:var(--muted)}
.pending{color:var(--muted);font-weight:500;font-size:14px}
.sr-tag{display:inline-block;font-size:12px;color:var(--muted);margin-top:10px}
.tag{display:inline-block;background:var(--teal-soft);color:var(--teal-dark);font-size:12px;font-weight:600;padding:3px 12px;border-radius:9999px;margin:2px 6px 2px 0}
.pending-head{margin:40px 0 8px;font-size:22px;font-family:'Inter',sans-serif}
.pending-sub{color:var(--muted);margin:0 0 24px}
.networth-tag{display:inline-block;background:var(--teal-soft);color:var(--teal-dark);font-size:12px;font-weight:600;padding:3px 10px;border-radius:9999px;margin-top:8px}
.brands{background:var(--ink);color:#fff;text-align:center;border-radius:24px;padding:64px 32px;margin:0 24px;max-width:1052px}
.brands h2{font-size:30px;margin-bottom:12px}
.brands p{opacity:.85;max-width:560px;margin:0 auto 28px;font-size:17px}
.brands ul{list-style:none;padding:0;margin:0 auto 32px;display:flex;gap:24px;justify-content:center;flex-wrap:wrap;font-size:15px}
.brands li::before{content:"\\2713 ";color:#2DD4BF;font-weight:700}
footer{background:#fff;border-top:1px solid var(--line);padding:40px 0;font-size:14px;color:var(--muted)}
footer .wrap{display:flex;justify-content:space-between;gap:24px;flex-wrap:wrap}
.disclaimer{max-width:640px;font-size:13px;color:#4B5563;margin-top:16px;line-height:1.5}
#no-results{display:none;text-align:center;color:var(--muted);padding:32px}"""

JS = """<script>
(function(){
var q=document.getElementById('q'),sort=document.getElementById('sort'),topic=document.getElementById('topic'),hasfig=document.getElementById('hasfig'),nores=document.getElementById('no-results');
function num(s){s=(s||'').trim();if(/M$/i.test(s))return parseFloat(s)*1e6;if(/K$/i.test(s))return parseFloat(s)*1e3;return parseFloat(s)||0;}
function apply(){
var query=(q.value||'').toLowerCase(),t=topic.value,hf=hasfig.checked;
var groups=[document.getElementById('fig-group'),document.getElementById('pend-group')];
var vis=0;
groups.forEach(function(g){
if(!g)return;
var list=Array.prototype.slice.call(g.querySelectorAll('.card'));
list.forEach(function(c){
var ok=c.getAttribute('data-name').indexOf(query)>-1;
if(t&&c.getAttribute('data-topics').indexOf(t)<0)ok=false;
if(hf&&c.getAttribute('data-nw')!=='1')ok=false;
c.style.display=ok?'':'none';
if(ok)vis++;
});
if(sort.value!=='default'){
list.sort(function(a,b){
var k=sort.value;
var av=k==='eng'?parseFloat(a.getAttribute('data-eng')):num(a.querySelector('.figures strong').textContent);
if(k==='nw')av=a.getAttribute('data-nw')==='1'?num(a.querySelectorAll('.figures strong')[1].textContent):-1;
var bv=k==='eng'?parseFloat(b.getAttribute('data-eng')):num(b.querySelector('.figures strong').textContent);
if(k==='nw')bv=b.getAttribute('data-nw')==='1'?num(b.querySelectorAll('.figures strong')[1].textContent):-1;
return bv-av;});
list.forEach(function(c){g.appendChild(c);});
}});
var searching=query!==''||t!==''||hf||sort.value!=='default';
document.querySelector('.pending-head').style.display=searching?'none':'';
document.querySelector('.pending-sub').style.display=searching?'none':'';
nores.style.display=vis===0?'block':'none';
}
[q,sort,topic,hasfig].forEach(function(el){el.addEventListener('input',apply);el.addEventListener('change',apply);});
})();
</script>"""

# topic options from cards
topics = sorted(set(re.findall(r'data-topics="([^"]+)"', cards)))
allt = set()
for t in topics:
    allt.update(t.split(' '))
# better: collect from <span class="tag"> values
tags = sorted(set(re.findall(r'<span class="tag">([^<]+)</span>', cards)))
tagopts = '\n'.join('<option value="' + t.lower() + '">' + t + '</option>' for t in tags)

page = ("<!DOCTYPE html>\n<html lang=\"en-GB\">\n<head>\n<meta charset=\"UTF-8\">\n"
"<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n" + GA + "\n"
"<title>SaveShare.io \u2014 Sourced UK Money Creator Directory</title>\n"
"<meta name=\"description\" content=\"A sourced directory of UK personal finance creators. Self-reported figures, linked back to their TikTok.\">\n"
"<style>" + CSS + "</style>\n</head>\n<body>\n\n"
"<nav>\n  <div class=\"wrap\">\n"
"    <a class=\"logo\" href=\"#\">SaveShare<span>.io</span></a>\n"
"    <div class=\"nav-links\">\n"
"      <a href=\"#how\">How it works</a>\n"
"      <a href=\"#creators\">Directory</a>\n"
"      <a href=\"blog/index.html\">Money Advice</a>\n"
"      <a href=\"#brands\">For brands</a>\n"
"      <a href=\"#creators\" class=\"btn\">Browse directory</a>\n"
"    </div>\n  </div>\n</nav>\n\n"
"<header class=\"hero\">\n  <div class=\"wrap\">\n"
"    <div class=\"badge\">SOURCED UK CREATOR DIRECTORY</div>\n"
"    <h1>Discover UK money creators</h1>\n"
"    <p>Real people sharing real numbers. Every net-worth figure is self-reported in the creator's own TikTok content \u2014 linked back so you can check the source.</p>\n"
"    <div class=\"hero-ctas\">\n"
"      <a href=\"#creators\" class=\"btn btn-light\">Explore the directory</a>\n"
"      <a href=\"#brands\" class=\"btn btn-outline\">I\u2019m a brand</a>\n"
"    </div>\n"
"    <div class=\"hero-stats\">\n"
"      <div><strong>39</strong><span>Sourced creators</span></div>\n"
"      <div><strong>" + total_s + "</strong><span>Combined followers</span></div>\n"
"      <div><strong>" + nfig + "</strong><span>With sourced net worth</span></div>\n"
"    </div>\n"
"    <div class=\"feat-row\">\n" + feat + "\n    </div>\n"
"  </div>\n</header>\n\n"
"<section id=\"how\">\n  <div class=\"wrap\">\n"
"    <div class=\"section-head\">\n      <h2>How it works</h2>\n"
"      <p>Transparency by design \u2014 every figure traces back to the creator's own words.</p>\n"
"    </div>\n"
"    <div class=\"steps\">\n"
"      <div class=\"step\">\n        <div class=\"num\">1</div>\n"
"        <h3>Creators talk money</h3>\n"
"        <p>UK finance creators share their journeys, portfolios and net worth openly on TikTok.</p>\n"
"      </div>\n"
"      <div class=\"step\">\n        <div class=\"num\">2</div>\n"
"        <h3>We capture transcripts</h3>\n"
"        <p>We pull their video transcripts and extract the figures they share themselves.</p>\n"
"      </div>\n"
"      <div class=\"step\">\n        <div class=\"num\">3</div>\n"
"        <h3>You check the source</h3>\n"
"        <p>Every profile links straight back to the creator's TikTok \u2014 check the source yourself. See the FAQ for how figures work.</p>\n"
"      </div>\n    </div>\n  </div>\n</section>\n\n"
"<section id=\"creators\" style=\"background:#fff;border-top:1px solid var(--line);border-bottom:1px solid var(--line)\">\n"
"  <div class=\"wrap\">\n"
"    <div class=\"section-head\">\n"
"      <h2>Creator directory</h2>\n"
"      <p>UK personal finance creators sharing their money journeys openly. Figures last pulled 5 Oct 2026. Click any creator for their full profile, net-worth sources and key quotes \u2014 plus our <a href=\"blog/index.html\">money advice hub</a>.</p>\n"
"    </div>\n"
"    <div class=\"controls\">\n"
"      <input type=\"search\" id=\"q\" placeholder=\"Search creators\u2026\" aria-label=\"Search creators\">\n"
"      <select id=\"sort\" aria-label=\"Sort creators\">\n"
"        <option value=\"default\">Sort: featured</option>\n"
"        <option value=\"fol\">Sort: followers</option>\n"
"        <option value=\"nw\">Sort: net worth</option>\n"
"        <option value=\"eng\">Sort: engagement</option>\n"
"      </select>\n"
"      <select id=\"topic\" aria-label=\"Filter by topic\">\n"
"        <option value=\"\">All topics</option>\n" + tagopts + "\n      </select>\n"
"      <label><input type=\"checkbox\" id=\"hasfig\"> Has net-worth figure</label>\n"
"    </div>\n"
"    <div class=\"grid\">\n" + cards + "\n    </div>\n"
"    <div id=\"no-results\">No creators match your search. Try clearing a filter.</div>\n"
"    <p class=\"src\" style=\"margin-top:24px\">* Self-reported figure \u2014 stated by the creator in their own TikTok content, not independently verified. Source video (+ date) linked on each profile.</p>\n"
"  </div>\n</section>\n\n"
"<section id=\"brands\">\n  <div class=\"brands\">\n"
"    <h2>For brands</h2>\n"
"    <p>Connect with authentic UK finance creators whose audiences trust them with real money conversations.</p>\n"
"    <ul>\n"
"      <li>Sourced reach &amp; topics</li>\n"
"      <li>Direct creator access</li>\n"
"      <li>Transparent, sourced figures</li>\n"
"    </ul>\n"
"    <a href=\"mailto:hello@saveshare.io?subject=Brand%20partnership%20enquiry\" class=\"btn\">Partner with us</a>\n"
"  </div>\n</section>\n\n\n"
"<section id=\"faq\">\n"
"  <div class=\"wrap\" style=\"max-width:720px\">\n"
"    <div class=\"section-head\"><h2>FAQ</h2></div>\n"
"    <div style=\"display:grid;gap:20px\">\n"
"      <div><h3 style=\"margin:0 0 6px;font-size:17px\">Where do the net worth figures come from?</h3>\n"
"      <p style=\"margin:0;color:var(--muted)\">They're self-reported \u2014 stated by each creator in their own TikTok videos. We extract them from transcripts and link back to the source so you can check.</p></div>\n"
"      <div><h3 style=\"margin:0 0 6px;font-size:17px\">Are the figures verified?</h3>\n"
"      <p style=\"margin:0;color:var(--muted)\">No independent verification. Figures may be outdated or aspirational. Treat them as what the creator claims, not audited fact.</p></div>\n"
"      <div><h3 style=\"margin:0 0 6px;font-size:17px\">How often is data refreshed?</h3>\n"
"      <p style=\"margin:0;color:var(--muted)\">Stats and transcripts are re-polled every Monday. Last pull: 5 Oct 2026 (shown above the directory too).</p></div>\n"
"      <div><h3 style=\"margin:0 0 6px;font-size:17px\">Is this financial advice?</h3>\n"
"      <p style=\"margin:0;color:var(--muted)\">No. Nothing on this site constitutes financial advice. Do your own research.</p></div>\n"
"    </div>\n  </div>\n</section>\n\n"
"<footer>\n  <div class=\"wrap\">\n    <div>\n"
"      <a class=\"logo\" href=\"#\" style=\"font-size:18px\">SaveShare<span>.io</span></a>\n"
"      <p style=\"margin:8px 0 0\">Sourced creator directory for UK personal finance.</p>\n"
"    </div>\n"
"    <div style=\"font-size:14px\">\n"
"      <a href=\"#how\" style=\"color:var(--muted);text-decoration:none;margin-right:18px\">How it works</a>\n"
"      <a href=\"#creators\" style=\"color:var(--muted);text-decoration:none;margin-right:18px\">Directory</a>\n"
"      <a href=\"#brands\" style=\"color:var(--muted);text-decoration:none;margin-right:18px\">For brands</a>\n"
"      <a href=\"#faq\" style=\"color:var(--muted);text-decoration:none\">FAQ</a>\n"
"    </div>\n  </div>\n"
"  <div class=\"wrap\">\n"
"    <p class=\"disclaimer\">Disclaimer: Net worth figures shown are self-reported by each creator in their own TikTok content and have not been independently verified. They may be outdated. Nothing on this site constitutes financial advice. Figures are shown with attribution and a link back to the creator's original account so you can check the source yourself. Stats (followers, likes) last pulled 5 Oct 2026.</p>\n"
"    <p style=\"font-size:13px;color:#4B5563\">\u00a9 2026 SaveShare.io \u2014 All rights reserved.</p>\n"
"  </div>\n</footer>\n\n" + JS + "\n\n</body>\n</html>\n")

open('index.html', 'w').write(page)
print('index.html written:', len(page), 'bytes')
