#!/usr/bin/env python3
"""US intake: profiles + top 20 videos + video-data jobs. Region=US.
Logs to us_intake_results.json. Run in background."""
import json, os, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ts import call

HANDLES = [
 ("blondebrokeandbougie","Becca Brenner"),
 ("humphreytalks","Humphrey Yang"),
 ("pricelessstay","Taylor Price"),
 ("grahamstephan","Graham Stephan"),
 ("andreijikh","Andrei Jikh"),
 ("personalfinanceclub","Jeremy Schneider"),
 ("moneywithkatie","Money with Katie"),
 ("erikakullberg","Erika Kullberg"),
 ("your.richbff","Vivian Tu"),
 ("herfirst100k","Tori Dunlap"),
 ("charliechang","Charlie Chang"),
 ("minoritymindset","Jaspreet Singh"),
 ("calltoleap","Steve Chen"),
 ("thebudgetnista","Tiffany Aliche"),
 ("thebudgetmom","Kumiko Love"),
 ("brokemillennial","Erin Lowry"),
 ("whiteboardfinance","Marko"),
 ("codie_sanchez","Codie Sanchez"),
 ("marktilbury","Mark Tilbury"),
 ("investdiva","Kiana Danial"),
 ("nicolelapin","Nicole Lapin"),
 ("itserinconfortini","Erin Confortini"),
 ("ecommjess","Jessica Spangler"),
 ("christine.elizabeth","Christine Elizabeth"),
 ("tradertoks","TraderToks"),
 ("sam_jarman","Sam Jarman"),
 ("rhercules_","Hercules"),
 ("themaestroreal","Danny"),
 ("klkbuilds","Keifer Kelson"),
 ("ribbs188","Robert Riordan"),
]

os.makedirs("ts_raw", exist_ok=True)
results = {}
for handle, name in HANDLES:
    r = {"name": name}
    try:
        u = call("get_tiktok_user", {"username": handle}, timeout=120)
        r["profile"] = {k: u.get(k) for k in ("nickname","followers","likes","videos","verified","bio") if isinstance(u, dict)}
        if not isinstance(u, dict) or u.get("http_error") or "envelope" in u:
            r["error"] = str(u)[:300]; results[handle] = r; continue
    except Exception as e:
        r["error"] = f"profile: {e}"; results[handle] = r; continue
    try:
        v = call("get_tiktok_user_videos", {"username": handle, "count": 20}, timeout=180)
        vids = v.get("videos", []) if isinstance(v, dict) else []
        r["videos_found"] = len(vids)
        with open(f"ts_raw/us_{handle}.json", "w") as f:
            json.dump(v, f, ensure_ascii=False)
        urls = []
        for x in vids:
            vid = x.get("id") or x.get("video_id")
            if vid: urls.append(f"https://www.tiktok.com/@{handle}/video/{vid}")
        r["urls"] = len(urls)
        tdir = f"transcripts/{handle}"
        os.makedirs(tdir, exist_ok=True)
        if urls:
            job = call("submit_transcript_job", {"urls": urls}, timeout=300)
            r["job"] = job.get("job_id") or job.get("jobId") or str(job)[:200]
        else:
            r["job"] = None
    except Exception as e:
        r["error"] = f"videos: {e}"
    results[handle] = results.get(handle, r)
    json.dump(results, open("us_intake_results.json", "w"), indent=1)
    print(f"{handle}: {json.dumps({k:v for k,v in r.items() if k!='profile'})[:200]}", flush=True)
    time.sleep(2)
print("INTAKE SUBMIT DONE")
