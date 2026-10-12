#!/usr/bin/env python3
"""UK/US toggle + region flags + blog region tags. Idempotent-ish (check markers)."""
import re

# ---------- 1. index.html: toggle UI + region filter ----------
idx = open('index.html').read()

# 1a. tag all existing cards region=uk
idx = re.sub(r'<div class="card" data-name=', '<div class="card" data-region="uk" data-name=', idx)

# 1b. toggle buttons in controls
toggle_html = '''      <div class="region-toggle" role="group" aria-label="Region">
        <button type="button" id="reg-uk" class="reg-btn">🇬🇧 UK</button>
        <button type="button" id="reg-us" class="reg-btn">🇺🇸 US</button>
      </div>
'''
if 'region-toggle' not in idx:
    idx = idx.replace('    <div class="controls">\n', '    <div class="controls">\n' + toggle_html)

# 1c. toggle CSS
toggle_css = '.region-toggle{display:flex;gap:0;border:1px solid var(--line);border-radius:9999px;overflow:hidden}.reg-btn{border:none;background:#fff;color:var(--muted);font-weight:700;font-size:15px;padding:12px 22px;cursor:pointer;font-family:inherit;min-height:44px}.reg-btn.active{background:var(--teal);color:#fff}.region-flag{display:inline-block;font-size:12px;font-weight:700;margin-left:8px}'
if 'region-toggle' not in idx.split('<style>')[1].split('</style>')[0]:
    idx = idx.replace('#no-results{', toggle_css + '#no-results{', 1)

# 1d. JS: region state + filter
old_js = """function apply(){
var query=(q.value||'').toLowerCase(),t=topic.value,hf=hasfig.checked;"""
new_js = """var region=localStorage.getItem('ss-region')||'uk';
function setRegion(r){region=r;localStorage.setItem('ss-region',r);
document.getElementById('reg-uk').classList.toggle('active',r==='uk');
document.getElementById('reg-us').classList.toggle('active',r==='us');
apply();}
document.getElementById('reg-uk').addEventListener('click',function(){setRegion('uk');});
document.getElementById('reg-us').addEventListener('click',function(){setRegion('us');});
document.getElementById('reg-uk').classList.toggle('active',region==='uk');
document.getElementById('reg-us').classList.toggle('active',region==='us');
function apply(){
var query=(q.value||'').toLowerCase(),t=topic.value,hf=hasfig.checked;"""
assert old_js in idx
idx = idx.replace(old_js, new_js)

old_f = """var ok=c.getAttribute('data-name').indexOf(query)>-1;"""
new_f = """var ok=c.getAttribute('data-name').indexOf(query)>-1;
if((c.getAttribute('data-region')||'uk')!==region)ok=false;"""
assert old_f in idx
idx = idx.replace(old_f, new_f)
open('index.html', 'w').write(idx)
print('index.html: toggle + region filter done')

# ---------- 2. p/*.html: region flag on badge ----------
import glob
for f in glob.glob('p/*.html'):
    s = open(f).read()
    if 'UK MONEY CREATOR PROFILE' in s and 'region-flag' not in s:
        s = s.replace('UK MONEY CREATOR PROFILE',
            'UK MONEY CREATOR PROFILE <span class="region-flag">🇬🇧 UK</span>')
        # ensure flag css exists
        if '.region-flag' not in s:
            s = s.replace('.src{', '.region-flag{display:inline-block;background:rgba(255,255,255,.2);font-size:12px;font-weight:700;padding:2px 10px;border-radius:9999px;margin-left:8px}.src{', 1)
        open(f, 'w').write(s)
print('p/*.html: flags done')

# ---------- 3. blog/index.html: region tags on long-form guides + filter ----------
b = open('blog/index.html').read()
UK_GUIDES = ['isa-beginners-guide.html', 'pension-basics-uk.html',
             'lifetime-isa-first-home-bonus.html', 'women-money-uk.html',
             'money-moves-18-adamjay.html', '400k-net-worth-tatiana.html',
             'teacher-to-millionaire.html', 'five-monthly-habits-dahlia.html']
# tag guide cards: find <div class="card"><h2><a href="X"> and add data-region
def tagcard(m):
    href = m.group(1)
    r = 'uk' if href in UK_GUIDES else 'general'
    return f'<div class="card" data-region="{r}"><h2><a href="{href}">'
b2, n = re.subn(r'<div class="card"><h2><a href="([^"]+)">', tagcard, b)
print('blog guide cards tagged:', n)
open('blog/index.html', 'w').write(b2)
