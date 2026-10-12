/* SaveShare.io light anti-scrape guard (static-safe, no backend).
   Detects rapid sequential page fetches (bot-like) and known headless/
   automation signals; shows a licensing notice. Humans are unaffected. */
(function(){
  try{
    var KEY='ss_nav_ts',WINDOW_MS=15000,THRESHOLD=12;
    var now=Date.now(),arr=[];
    try{arr=JSON.parse(sessionStorage.getItem(KEY)||'[]');}catch(e){arr=[];}
    arr=arr.filter(function(t){return now-t<WINDOW_MS;});
    arr.push(now);
    try{sessionStorage.setItem(KEY,JSON.stringify(arr));}catch(e){}
    var ua=navigator.userAgent||'';
    var auto=/HeadlessChrome|PhantomJS|Playwright|Selenium|Puppeteer|bot|crawl|spider/i.test(ua)&&!/Googlebot|Bingbot/i.test(ua);
    if(arr.length>THRESHOLD||auto||navigator.webdriver){
      var d=document.createElement('div');
      d.setAttribute('role','alert');
      d.style.cssText='position:fixed;left:0;right:0;bottom:0;z-index:9999;background:#0F172A;color:#fff;padding:14px 20px;font:14px/1.5 system-ui;text-align:center';
      d.innerHTML='Browsing fast like a bot? Bulk or automated access needs a licence — <a href="/licensing.html" style="color:#2DD4BF;font-weight:700">see plans from £29/mo</a> · <a href="mailto:licensing@saveshare.io" style="color:#fff">licensing@saveshare.io</a> <button id="ss-guard-x" style="margin-left:12px;background:none;border:1px solid #fff;color:#fff;border-radius:8px;padding:2px 10px;cursor:pointer">dismiss</button>';
      document.addEventListener('DOMContentLoaded',function(){document.body.appendChild(d);
        document.getElementById('ss-guard-x').onclick=function(){d.remove();};});
    }
    /* honeypot: invisible link no human clicks; bots that follow every href reveal themselves */
    var hp=document.createElement('a');
    hp.href='/licensing.html?hp=1';hp.rel='nofollow';hp.tabIndex=-1;hp.setAttribute('aria-hidden','true');
    hp.style.cssText='position:absolute!important;left:-9999px;width:1px;height:1px;overflow:hidden';
    hp.textContent='internal feed';
    hp.addEventListener('click',function(){try{localStorage.setItem('ss_hp','1');}catch(e){}});
    document.addEventListener('DOMContentLoaded',function(){document.body.appendChild(hp);});
  }catch(e){}
})();
