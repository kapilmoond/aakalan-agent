#!/usr/bin/env python3
"""Rebrand Hermes Desktop -> Aakalan Agent (SAFE version).

Rules:
- Process LINE BY LINE (never span lines -> no corrupted identifiers).
- Only rewrite standalone word "Hermes" INSIDE string literals (', ", `).
- Never touch code identifiers (HermesGateway, waitForHermesReady...),
  env names (HERMES_HOME), lowercase paths/commands (hermes-agent, hermes.exe,
  install.ps1, `hermes gateway setup`, hermes:...).
- Also rewrite JSX text nodes >Hermes< -> >Aakalan Agent<.
- Skip test/spec files.
"""
import re, pathlib

ROOT = pathlib.Path(r"C:\Users\LAPTOP PC\Desktop\3_Apps_and_Development\aakalan agent\apps\desktop")

# If a string contains any of these, it is an internal reference -> leave it.
SKIP_CONTEXT = re.compile(
    r"(HERMES_HOME|hermes_home|hermesAgent|hermesRoot|hermesDesktop|hermes-agent|hermes\.exe|"
    r"hermesRuntime|hermes:|/hermes|\\hermes|hermes_|@hermes|hermesAgentRoot|hermes\.py|"
    r"hermes gateway|hermes update|hermes doctor|hermes chat|hermes setup|hermes --|"
    r"hermes desktop|hermes config|install\.ps1|install\.sh|hermes_bootstrap|hermes-state|"
    r"hermes-gateway|hermes-cli|hermes-agent\.nousresearch|nousresearch\.com|github\.com/NousResearch|"
    r"hermes-bridge|hermes\.sh|hermes_agent|hermes_controller|hermes_gateway|hermes_runtime|"
    r"hermesDesktop|hermes\.js|hermes\.mjs|hermes\.cjs|hermes_proxy|hermes-server|hermes_service)"
)

WORD = re.compile(r"\bHermes\b")

def rewrite_string_literal(m):
    """m is a full string literal match (with quotes)."""
    s = m.group(0)
    quote = s[0]
    inner = s[1:-1]
    if SKIP_CONTEXT.search(inner):
        return s
    new_inner = WORD.sub("Aakalan Agent", inner)
    # HTTP header names cannot contain spaces. X-Hermes-Foo -> X-Aakalan Agent-Foo
    # would crash Node with ERR_INVALID_HTTP_TOKEN.
    new_inner = new_inner.replace("X-Aakalan Agent-", "X-Aakalan-Agent-")
    if new_inner != inner:
        return quote + new_inner + quote
    return s

# Matches one string literal: "..." or '...' or `...` (no line spans).
STR_RE = re.compile(
    r'"(?:[^"\\\n]|\\.)*"|\'(?:[^\'\\\n]|\\.)*\'|`(?:[^`\\\n]|\\.)*`'
)

# JSX text node: >Hermes< or > Hermes < (inside JSX element body)
JSX_RE = re.compile(r"(>)(\s*)\bHermes\b(\s*)(<)")

def process_text(text):
    # 1) string literals
    text = STR_RE.sub(rewrite_string_literal, text)
    # 2) JSX text nodes
    text = JSX_RE.sub(lambda m: m.group(1) + m.group(2) + "Aakalan Agent" + m.group(3) + m.group(4), text)
    return text

def process_file(path):
    try:
        txt = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  !! read fail {path}: {e}")
        return 0
    new = process_text(txt)
    if new != txt:
        path.write_text(new, encoding="utf-8")
        return 1
    return 0

changed = 0
skipped = 0
for sub in ("src", "electron"):
    base = ROOT / sub
    for p in base.rglob("*"):
        if p.suffix not in (".ts", ".tsx", ".js", ".mjs", ".jsx"):
            continue
        if ".test." in p.name or ".spec." in p.name:
            skipped += 1
            continue
        changed += process_file(p)

# index.html title
html = ROOT / "index.html"
if html.exists():
    t = html.read_text(encoding="utf-8")
    t2 = re.sub(r"<title>.*?</title>", "<title>Aakalan Agent</title>", t, count=1)
    if t2 != t:
        html.write_text(t2, encoding="utf-8")
        changed += 1

print(f"changed={changed} files, skipped {skipped} test files")
