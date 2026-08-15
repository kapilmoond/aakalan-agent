import re, pathlib, glob

# GitHub Desktop stores its repo list in IndexedDB leveldb logs (binary).
# We only look for path-like strings mentioning aakalan/hermes/agent.
hits = set()
for f in glob.glob(r"C:\Users\LAPTOP PC\AppData\Roaming\GitHub Desktop\IndexedDB\file__0.indexeddb.leveldb\*.log"):
    try:
        data = open(f, "rb").read()
    except Exception:
        continue
    for m in re.finditer(rb"[A-Za-z]:[\\/][^\x00-\x1f\"']{3,120}", data):
        s = m.group(0).decode("utf-8", "ignore")
        if re.search(r"aakalan|hermes|agent", s, re.I):
            hits.add(s)
for h in sorted(hits):
    print(h)
print("---DONE---")
