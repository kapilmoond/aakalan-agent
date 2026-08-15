#!/usr/bin/env python3
"""Make kapilmoond/aakalan-agent public + create Release v0.17.0 + upload EXE.
Uses the GitHub token from Windows Credential Manager (never prints it)."""
import json, os, pathlib, subprocess, sys, urllib.request, urllib.error

def get_token():
    # Ask git credential manager for the stored github.com token
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
    print("ERROR: no token")
    sys.exit(1)
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
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")

# 1. Make repo public
status, resp = api("PATCH", "https://api.github.com/repos/kapilmoond/aakalan-agent", {"private": False})
print(f"[1] set public: HTTP {status} | private={resp.get('private')} | html={resp.get('html_url')}")

# 2. Create release
status, rel = api("POST", "https://api.github.com/repos/kapilmoond/aakalan-agent/releases", {
    "tag_name": "v0.17.0",
    "name": "Aakalan Agent v0.17.0",
    "body": "Aakalan Agent — Windows desktop installer.\n\nWindows 10/11, 64-bit. Download AakalanAgent-0.17.0-win-x64.exe and run it.",
    "draft": False,
    "prerelease": False,
})
print(f"[2] create release: HTTP {status} | id={rel.get('id')} | tag={rel.get('tag_name')}")
if status not in (200, 201):
    print("   release response:", json.dumps(rel)[:300])
    sys.exit(1)

# 3. Upload EXE as release asset
exe = r"C:\Users\LAPTOP PC\Downloads\Consultancy_HEWP_Hisar_Rent_2026-06-13\website_draft\downloads\AakalanAgent-0.17.0-win-x64.exe"
upload_url = rel["upload_url"].replace("{?name,label}", f"?name={os.path.basename(exe)}")
size = os.path.getsize(exe)
with open(exe, "rb") as f:
    data = f.read()
req = urllib.request.Request(upload_url, data=data, method="POST", headers={
    **HEADERS,
    "Content-Type": "application/octet-stream",
    "Content-Length": str(size),
})
try:
    with urllib.request.urlopen(req, timeout=300) as r:
        asset = json.loads(r.read().decode())
    print(f"[3] upload EXE: HTTP {r.status} | asset={asset.get('name')} | size={asset.get('size')} | dl={asset.get('browser_download_url')}")
except urllib.error.HTTPError as e:
    print(f"[3] upload failed: HTTP {e.code}: {e.read().decode()[:300]}")
    sys.exit(1)

print("\nALL DONE — public release ready")
