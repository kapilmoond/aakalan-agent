#!/usr/bin/env python3
"""Replace the EXE asset on the v0.17.0 release (delete old, upload new)."""
import json, os, subprocess, sys, urllib.request, urllib.error

def get_token():
    cred = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True, env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    ).stdout
    for line in cred.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return None

token = get_token()
if not token:
    print("ERROR: no token"); sys.exit(1)
print("token acquired (not shown)")

HEADERS = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "aakalan-agent-setup",
}

def api(method, url, data=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            raw = r.read().decode() or "{}"
            return r.status, json.loads(raw)
    except urllib.error.HTTPError as e:
        raw = e.read().decode() or "{}"
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw[:200]}

exe = r"C:\Users\LAPTOP PC\Desktop\3_Apps_and_Development\aakalan agent\apps\desktop\release\AakalanAgent-0.17.0-win-x64.exe"

# Find release by tag
status, rel = api("GET", "https://api.github.com/repos/kapilmoond/aakalan-agent/releases/tags/v0.17.0")
print(f"[1] find release: HTTP {status} | id={rel.get('id')}")
if status != 200:
    sys.exit(1)

# Delete old asset (same name)
for asset in rel.get("assets", []):
    if asset["name"] == "AakalanAgent-0.17.0-win-x64.exe":
        st, _ = api("DELETE", f"https://api.github.com/repos/kapilmoond/aakalan-agent/releases/assets/{asset['id']}")
        print(f"[2] delete old asset {asset['id']}: HTTP {st}")

# Upload new EXE
upload_url = rel["upload_url"].replace("{?name,label}", "?name=AakalanAgent-0.17.0-win-x64.exe")
with open(exe, "rb") as f:
    data = f.read()
req = urllib.request.Request(upload_url, data=data, method="POST", headers={
    **HEADERS,
    "Content-Type": "application/octet-stream",
    "Content-Length": str(len(data)),
})
try:
    with urllib.request.urlopen(req, timeout=300) as r:
        asset = json.loads(r.read().decode())
    print(f"[3] upload: HTTP {r.status} | asset={asset.get('name')} | size={asset.get('size')}")
except urllib.error.HTTPError as e:
    print(f"[3] upload failed: HTTP {e.code}: {e.read().decode()[:300]}")
    sys.exit(1)

print("\nDONE — release updated")
