"""PinBridge blitz 2026-10-29: 100 scheduled pins (80 SaveShare + 20 Binx).
Regenerate: python3 - <<'PY' ... (see /tmp/saveshare_pins.json + /tmp/binx_pins.json build).
Schedule via MCP: /tmp/pbc.sh create_schedule '<json>' (one call per pin)."""
import json
pins = json.load(open('pinbridge-blitz-2026-10-29.json'))
print(f"{len(pins)} pins: {sum(1 for p in pins if '/p/' in p['link_url'])} saveshare, {sum(1 for p in pins if '/binx/' in p['image_url'])} binx")
print(pins[0]['run_at'], '->', pins[-1]['run_at'])
