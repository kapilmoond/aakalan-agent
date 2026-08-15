#!/usr/bin/env python3
"""Rebrand user-visible strings in the Python agent core (Hermes -> Aakalan Agent).

SAFE: line-based, only inside string literals, only standalone word "Hermes".
Skips: identifiers (HermesAgent, hermes_cli), env vars (HERMES_HOME),
lowercase commands/paths (hermes-agent, hermes.exe, `hermes chat`).
"""
import re, pathlib

ROOT = pathlib.Path(r"C:\Users\LAPTOP PC\Desktop\3_Apps_and_Development\aakalan agent")

SKIP_CONTEXT = re.compile(
    r"(HERMES_HOME|hermes_home|hermesAgent|hermesRoot|hermesDesktop|hermes-agent|hermes\.exe|"
    r"hermesRuntime|hermes:|/hermes|\\hermes|hermes_|@hermes|hermesAgentRoot|hermes\.py|"
    r"hermes gateway|hermes update|hermes doctor|hermes chat|hermes setup|hermes --|"
    r"hermes desktop|hermes config|install\.ps1|install\.sh|hermes_bootstrap|hermes-state|"
    r"hermes-gateway|hermes-cli|hermes-agent\.nousresearch|nousresearch\.com|github\.com/NousResearch|"
    r"hermes-bridge|hermes\.sh|hermes_agent|hermes_controller|hermes_gateway|hermes_runtime|"
    r"hermes\.js|hermes\.mjs|hermes\.cjs|hermes_proxy|hermes-server|hermes_service|"
    r"hermes-core|hermes-engine|hermes-runner|hermes-launcher|hermes-api|hermes-sdk|"
    r"HERMES_ROOT|HERMES_HOME_DIR|HermesAgent|HermesGateway|HermesSession|HermesMessage|"
    r"hermes\.toml|hermes\.yaml|hermes\.json|hermes_plugin|hermes_tool|hermes_command)"
)

WORD = re.compile(r"\bHermes\b")

# Python string literals: single, double, triple single/double.
STR_RE = re.compile(
    r'"""(?:[^"\\]|\\.)*?"""|'
    r"'''(?:[^'\\]|\\.)*?'''|"
    r'"(?:[^"\\\n]|\\.)*"|'
    r"'(?:[^'\\\n]|\\.)*'"
)

def rewrite(m):
    s = m.group(0)
    inner = s[3:-3] if s[:3] in ('"""', "'''") else s[1:-1]
    if SKIP_CONTEXT.search(inner):
        return s
    new_inner = WORD.sub("Aakalan Agent", inner)
    new_inner = new_inner.replace("X-Aakalan Agent-", "X-Aakalan-Agent-")
    if new_inner == inner:
        return s
    if s[:3] in ('"""', "'''"):
        return s[:3] + new_inner + s[-3:]
    return s[0] + new_inner + s[-1]

def process_file(path):
    try:
        txt = path.read_text(encoding="utf-8")
    except Exception:
        return 0
    new = STR_RE.sub(rewrite, txt)
    if new != txt:
        path.write_text(new, encoding="utf-8")
        return 1
    return 0

changed = 0
for sub in ("agent", "gateway", "hermes_cli", "hermes", "hermes_state*.py"):
    base = ROOT / sub
    if not base.exists():
        continue
    for p in base.rglob("*.py"):
        if "__pycache__" in str(p) or ".venv" in str(p):
            continue
        changed += process_file(p)

# also standalone hermes_state files at root
for p in ROOT.glob("hermes_state*.py"):
    changed += process_file(p)

print(f"changed={changed} python files")
