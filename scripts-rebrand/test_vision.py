#!/usr/bin/env python3
"""Test meta-llama/llama-4-scout on OpenRouter with the same key."""
import base64, json, os, pathlib, urllib.request

# Read key from Hermes .env (same key the config uses)
env_path = pathlib.Path(os.path.expandvars(r"%LOCALAPPDATA%\hermes\.env"))
key = None
for line in env_path.read_text(encoding="utf-8").splitlines():
    if line.startswith("OPENROUTER_API_KEY="):
        key = line.split("=", 1)[1].strip()
        break
if not key:
    print("ERROR: OPENROUTER_API_KEY not found in .env")
    raise SystemExit(1)

image_path = r"C:\Users\LAPTOP PC\AppData\Roaming\Hermes\composer-images\composer_2026-08-15_12-23-14-888_e7ca8b.png"
b64 = base64.b64encode(pathlib.Path(image_path).read_bytes()).decode()

payload = {
    "model": "meta-llama/llama-4-scout",
    "max_tokens": 400,
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "This is a screenshot of a GitHub Desktop 'Failed to push' dialog. Transcribe the LAST 3 lines of the black terminal output exactly, especially anything after 'remote:' or 'fatal:'. Quote them word-for-word."},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
            ],
        }
    ],
}

req = urllib.request.Request(
    "https://openrouter.ai/api/v1/chat/completions",
    data=json.dumps(payload).encode(),
    headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://aakalaninfra.com",
        "X-Title": "Aakalan Agent vision test",
    },
)

try:
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode())
    content = data["choices"][0]["message"]["content"]
    print("=== MODEL OK ===")
    print("Model:", data.get("model"))
    print("=== ANSWER ===")
    print(content)
except urllib.error.HTTPError as e:
    print(f"HTTP ERROR {e.code}: {e.read().decode()[:500]}")
except Exception as e:
    print(f"ERROR: {e}")
