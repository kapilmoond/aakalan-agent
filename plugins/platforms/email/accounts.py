"""Multi-mailbox store for the Email messaging platform.

User-facing connection is one card per mailbox (Gmail, Google Workspace,
Outlook, or custom IMAP). The first mailbox stays mirrored onto the
legacy EMAIL_* env vars so older gateway paths keep working.
"""

from __future__ import annotations

import json
import re
import secrets
import stat
from pathlib import Path
from typing import Any

from hermes_constants import get_hermes_home

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

PROVIDERS: dict[str, dict[str, Any]] = {
    "gmail": {
        "label": "Gmail",
        "imap_host": "imap.gmail.com",
        "smtp_host": "smtp.gmail.com",
        "imap_port": 993,
        "smtp_port": 587,
    },
    "workspace": {
        "label": "Google Workspace",
        "imap_host": "imap.gmail.com",
        "smtp_host": "smtp.gmail.com",
        "imap_port": 993,
        "smtp_port": 587,
    },
    "outlook": {
        "label": "Outlook / Microsoft 365",
        "imap_host": "outlook.office365.com",
        "smtp_host": "smtp.office365.com",
        "imap_port": 993,
        "smtp_port": 587,
    },
    "other": {
        "label": "Other IMAP",
        "imap_host": "",
        "smtp_host": "",
        "imap_port": 993,
        "smtp_port": 587,
    },
}

_ACCOUNT_KEYS = (
    "id",
    "address",
    "provider",
    "imap_host",
    "smtp_host",
    "imap_port",
    "smtp_port",
    "password",
    "workspace_full",
    "enabled",
    "label",
)


def accounts_path(home: Path | None = None) -> Path:
    return (home or get_hermes_home()) / "email_accounts.json"


def infer_provider(address: str, imap_host: str = "") -> str:
    addr = (address or "").strip().lower()
    host = (imap_host or "").strip().lower()
    domain = addr.rsplit("@", 1)[-1] if "@" in addr else ""
    if host in {"imap.gmail.com", "smtp.gmail.com"} or domain == "gmail.com":
        return "gmail" if domain == "gmail.com" else "workspace"
    if host in {"outlook.office365.com", "smtp.office365.com", "imap-mail.outlook.com"}:
        return "outlook"
    if domain and domain not in {"gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com"}:
        if host in {"", "imap.gmail.com"}:
            return "workspace"
    return "other"


def apply_provider_defaults(account: dict[str, Any]) -> dict[str, Any]:
    provider = str(account.get("provider") or infer_provider(str(account.get("address") or ""), str(account.get("imap_host") or ""))).strip().lower()
    if provider not in PROVIDERS:
        provider = "other"
    preset = PROVIDERS[provider]
    out = dict(account)
    out["provider"] = provider
    out["label"] = out.get("label") or preset["label"]
    out["imap_host"] = str(out.get("imap_host") or preset["imap_host"] or "").strip()
    out["smtp_host"] = str(out.get("smtp_host") or preset["smtp_host"] or "").strip()
    try:
        out["imap_port"] = int(out.get("imap_port") or preset["imap_port"] or 993)
    except (TypeError, ValueError):
        out["imap_port"] = 993
    try:
        out["smtp_port"] = int(out.get("smtp_port") or preset["smtp_port"] or 587)
    except (TypeError, ValueError):
        out["smtp_port"] = 587
    return out


def _normalize(account: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(account, dict):
        return None
    address = str(account.get("address") or "").strip().lower()
    if not address or not EMAIL_RE.match(address):
        return None
    password = str(account.get("password") or "")
    if not password.strip():
        return None
    out = apply_provider_defaults({
        "id": str(account.get("id") or secrets.token_urlsafe(8)),
        "address": address,
        "provider": account.get("provider"),
        "imap_host": account.get("imap_host"),
        "smtp_host": account.get("smtp_host"),
        "imap_port": account.get("imap_port"),
        "smtp_port": account.get("smtp_port"),
        "password": password,
        "workspace_full": bool(account.get("workspace_full")),
        "enabled": account.get("enabled", True) is not False,
        "label": account.get("label"),
    })
    if not out["imap_host"] or not out["smtp_host"]:
        return None
    return {key: out.get(key) for key in _ACCOUNT_KEYS}


def load_accounts(home: Path | None = None) -> list[dict[str, Any]]:
    path = accounts_path(home)
    raw_accounts: list[Any] = []
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        if isinstance(payload, list):
            raw_accounts = payload
        elif isinstance(payload, dict):
            raw_accounts = list(payload.get("accounts") or [])
    accounts: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in raw_accounts:
        normalized = _normalize(item) if isinstance(item, dict) else None
        if not normalized:
            continue
        if normalized["address"] in seen:
            continue
        seen.add(normalized["address"])
        accounts.append(normalized)
    return _merge_legacy_env(accounts)


def _legacy_from_env() -> dict[str, Any] | None:
    try:
        from hermes_cli.config import get_env_value
    except Exception:
        import os

        def get_env_value(name: str, default: str = "") -> str:  # type: ignore[misc]
            return os.getenv(name, default) or default

    address = str(get_env_value("EMAIL_ADDRESS") or "").strip()
    password = str(get_env_value("EMAIL_PASSWORD") or "")
    imap_host = str(get_env_value("EMAIL_IMAP_HOST") or "").strip()
    smtp_host = str(get_env_value("EMAIL_SMTP_HOST") or "").strip()
    if not (address and password and imap_host and smtp_host):
        return None
    return _normalize({
        "id": "legacy-env",
        "address": address,
        "password": password,
        "imap_host": imap_host,
        "smtp_host": smtp_host,
        "imap_port": get_env_value("EMAIL_IMAP_PORT") or 993,
        "smtp_port": get_env_value("EMAIL_SMTP_PORT") or 587,
        "provider": infer_provider(address, imap_host),
        "enabled": True,
    })


def _merge_legacy_env(accounts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    legacy = _legacy_from_env()
    if not legacy:
        return accounts
    for account in accounts:
        if account["address"] == legacy["address"]:
            if not account.get("password"):
                account["password"] = legacy["password"]
            return accounts
    return [legacy, *accounts]


def save_accounts(accounts: list[dict[str, Any]], home: Path | None = None) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in accounts:
        normalized = _normalize(item)
        if not normalized or normalized["address"] in seen:
            continue
        seen.add(normalized["address"])
        cleaned.append(normalized)

    path = accounts_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"accounts": cleaned}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    try:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except Exception:
        pass
    _sync_legacy_env(cleaned)
    return cleaned


def _sync_legacy_env(accounts: list[dict[str, Any]]) -> None:
    try:
        from hermes_cli.config import remove_env_value, save_env_value
    except Exception:
        return
    enabled = [item for item in accounts if item.get("enabled", True)]
    primary = enabled[0] if enabled else None
    if primary is None:
        for key in (
            "EMAIL_ADDRESS",
            "EMAIL_PASSWORD",
            "EMAIL_IMAP_HOST",
            "EMAIL_SMTP_HOST",
            "EMAIL_IMAP_PORT",
            "EMAIL_SMTP_PORT",
            "EMAIL_HOME_ADDRESS",
        ):
            try:
                remove_env_value(key)
            except Exception:
                pass
        return
    save_env_value("EMAIL_ADDRESS", primary["address"])
    save_env_value("EMAIL_PASSWORD", primary["password"])
    save_env_value("EMAIL_IMAP_HOST", primary["imap_host"])
    save_env_value("EMAIL_SMTP_HOST", primary["smtp_host"])
    save_env_value("EMAIL_IMAP_PORT", str(primary["imap_port"]))
    save_env_value("EMAIL_SMTP_PORT", str(primary["smtp_port"]))
    save_env_value("EMAIL_HOME_ADDRESS", primary["address"])
    allowed = ",".join(item["address"] for item in enabled)
    if allowed:
        save_env_value("EMAIL_ALLOWED_USERS", allowed)


def public_account(account: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": account.get("id"),
        "address": account.get("address"),
        "provider": account.get("provider"),
        "label": account.get("label") or PROVIDERS.get(str(account.get("provider") or ""), {}).get("label") or "Email",
        "imap_host": account.get("imap_host"),
        "smtp_host": account.get("smtp_host"),
        "imap_port": account.get("imap_port"),
        "smtp_port": account.get("smtp_port"),
        "workspace_full": bool(account.get("workspace_full")),
        "enabled": account.get("enabled", True) is not False,
        "has_password": bool(str(account.get("password") or "").strip()),
    }


def upsert_account(incoming: dict[str, Any], home: Path | None = None) -> dict[str, Any]:
    accounts = load_accounts(home)
    incoming_id = str(incoming.get("id") or "").strip()
    incoming_address = str(incoming.get("address") or "").strip().lower()
    existing = None
    for item in accounts:
        if incoming_id and item["id"] == incoming_id:
            existing = item
            break
        if incoming_address and item["address"] == incoming_address:
            existing = item
            break
    merged = dict(existing or {})
    merged.update({k: v for k, v in incoming.items() if v is not None})
    if existing and not str(incoming.get("password") or "").strip():
        merged["password"] = existing.get("password")
    normalized = _normalize(merged)
    if not normalized:
        raise ValueError("Need a valid email address, password or app password, and IMAP/SMTP hosts.")
    next_accounts = [item for item in accounts if item["id"] != normalized["id"] and item["address"] != normalized["address"]]
    next_accounts.append(normalized)
    # Keep first-added account first so primary / home address stays stable.
    if existing:
        ordered = []
        replaced = False
        for item in accounts:
            if item["id"] == existing["id"] or item["address"] == existing["address"]:
                if not replaced:
                    ordered.append(normalized)
                    replaced = True
                continue
            ordered.append(item)
        if not replaced:
            ordered.append(normalized)
        next_accounts = ordered
    save_accounts(next_accounts, home)
    return normalized


def delete_account(account_id: str, home: Path | None = None) -> bool:
    accounts = load_accounts(home)
    remaining = [item for item in accounts if item["id"] != account_id and item["address"] != account_id]
    if len(remaining) == len(accounts):
        return False
    save_accounts(remaining, home)
    return True


def has_any_account(home: Path | None = None) -> bool:
    return any(item.get("enabled", True) for item in load_accounts(home))
