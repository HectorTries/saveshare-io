#!/usr/bin/env python3
"""TokScript MCP client (stateless per-request), tolerant SSE parser."""
import json, sys, urllib.request, urllib.error
BASE = "https://api.tokscript.com/mcp"
KEY = "sk_b69e77d686313f2ea9dab69401ee8fcd817e480a7b9a292417e5294ce8ddaf12"

def raw_call(tool, args, timeout=300):
    d = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": tool, "arguments": args}}
    h = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json",
         "Accept": "application/json, text/event-stream"}
    r = urllib.request.Request(BASE, data=json.dumps(d).encode(), headers=h)
    try:
        return urllib.request.urlopen(r, timeout=timeout).read().decode()
    except urllib.error.HTTPError as e:
        return f"HTTPERROR {e.code}: {e.read().decode()[:1000]}"

def parse(text):
    """Extract inner result text from SSE envelope, tolerating literal newlines."""
    if text.startswith("HTTPERROR"):
        return {"http_error": text[:500]}
    i = text.find('"text":"')
    if i < 0:
        return {"envelope": text[:2000]}
    start = i + len('"text":"')
    endmark = '}]},"jsonrpc"'
    j = text.rfind(endmark)
    if j < 0:
        # single-line envelope fallback
        for line in text.splitlines():
            if line.startswith("data: "):
                try:
                    o = json.loads(line[6:])
                    t = o["result"]["content"][0]["text"]
                    try:
                        return json.loads(t)
                    except Exception:
                        return {"text": t}
                except Exception:
                    continue
        return {"parse_fail": text[:1000]}
    inner = text[start:j - 1]  # escaped JSON-string body of the text field
    inner = inner.replace("\r", "").replace("\n", "\\n").replace("\t", "\\t")
    try:
        # double-encoded: decode string layer, then parse object layer
        return json.loads(json.loads('"' + inner + '"'))
    except json.JSONDecodeError as e:
        return {"json_error": str(e), "snippet": inner[:400]}

def call(tool, args, timeout=300):
    return parse(raw_call(tool, args, timeout))

if __name__ == "__main__":
    tool = sys.argv[1]
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    out = call(tool, args)
    s = json.dumps(out, indent=1, ensure_ascii=False)
    if len(sys.argv) > 3:
        open(sys.argv[3], "w").write(s)
        key = "videos"
        n = len(out.get(key, [])) if isinstance(out, dict) else "?"
        print(f"wrote {sys.argv[3]} ({len(s)} bytes, videos={n})")
    else:
        print(s[:8000])
