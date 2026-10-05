#!/usr/bin/env python3
"""TokScript MCP client (stateless per-request)."""
import json, sys, urllib.request, urllib.error
BASE = "https://api.tokscript.com/mcp"
KEY = "sk_b69e77d686313f2ea9dab69401ee8fcd817e480a7b9a292417e5294ce8ddaf12"

def call(tool, args):
    d = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": tool, "arguments": args}}
    h = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json",
         "Accept": "application/json, text/event-stream"}
    r = urllib.request.Request(BASE, data=json.dumps(d).encode(), headers=h)
    try:
        text = urllib.request.urlopen(r, timeout=300).read().decode()
    except urllib.error.HTTPError as e:
        return {"http_error": e.code, "body": e.read().decode()[:1000]}
    for line in text.splitlines():
        if line.startswith("data: "):
            try:
                j = json.loads(line[6:])
            except Exception:
                continue
            res = j.get("result", {})
            content = res.get("content", [])
            if content and isinstance(content, list) and "text" in (content[0] or {}):
                t = content[0]["text"]
                try:
                    return json.loads(t)
                except Exception:
                    return {"text": t[:6000]}
            return res
    return {"raw": text[:2000]}

if __name__ == "__main__":
    tool = sys.argv[1]
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    out = call(tool, args)
    s = json.dumps(out, indent=1)
    if len(sys.argv) > 3:
        open(sys.argv[3], "w").write(s)
        print(f"wrote {sys.argv[3]} ({len(s)} bytes)")
    else:
        print(s[:8000])
