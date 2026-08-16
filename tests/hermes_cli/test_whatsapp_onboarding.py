import asyncio
import time


class _FakeProc:
    def __init__(self, lines=None, returncode=0):
        self.stdout = iter(lines or [])
        self._returncode = returncode
        self.terminated = False
        self.killed = False
        self.pid = 12345

    def poll(self):
        return None if not self.terminated and not self.killed else self._returncode

    def wait(self, timeout=None):
        return self._returncode

    def terminate(self):
        self.terminated = True

    def kill(self):
        self.killed = True








def test_apply_whatsapp_onboarding_saves_pairing_policy(monkeypatch):
    from hermes_cli import web_server as ws

    saved = {}
    removed = []
    enabled = []

    monkeypatch.setattr(ws, "save_env_value", lambda key, value: saved.setdefault(key, value))
    monkeypatch.setattr(ws, "remove_env_value", lambda key: removed.append(key))
    monkeypatch.setattr(ws, "_write_platform_enabled", lambda platform, value: enabled.append((platform, value)))
    monkeypatch.setattr(
        ws,
        "_restart_gateway_after_whatsapp_onboarding",
        lambda profile=None, force_new=False: {"restart_started": True, "restart_pid": 12345},
    )

    record = ws._WhatsAppOnboardingSession(
        proc=None,
        mode="bot",
        allowed_users="",
        session_path="/tmp/session",
        expires_at="2099-01-01T00:00:00Z",
        expires_at_ts=time.time() + 600,
        status="connected",
    )
    ws._whatsapp_onboarding_sessions.clear()
    ws._whatsapp_onboarding_sessions["pairing"] = record

    result = asyncio.run(
        ws.apply_whatsapp_onboarding(
            "pairing",
            ws.WhatsAppOnboardingApply(mode="bot", allowed_users=""),
        )
    )

    assert result["ok"] is True
    assert saved["WHATSAPP_MODE"] == "bot"
    assert saved["WHATSAPP_DM_POLICY"] == "pairing"
    assert saved["WHATSAPP_ENABLED"] == "true"
    assert "WHATSAPP_ALLOWED_USERS" not in removed
    assert enabled == [("whatsapp", True)]
    assert "pairing" not in ws._whatsapp_onboarding_sessions


def test_start_whatsapp_onboarding_existing_creds_returns_linked_account(monkeypatch, tmp_path):
    from hermes_cli import web_server as ws

    session_dir = tmp_path / "session"
    session_dir.mkdir()
    (session_dir / "creds.json").write_text(
        '{"me":{"id":"15551234567:1@s.whatsapp.net","name":"Hermes Bot"}}',
        encoding="utf-8",
    )

    old_proc = _FakeProc(returncode=1)
    old_record = ws._WhatsAppOnboardingSession(
        proc=old_proc,
        mode="bot",
        allowed_users="",
        session_path=str(session_dir),
        expires_at="2099-01-01T00:00:00Z",
        expires_at_ts=time.time() + 600,
    )
    ws._whatsapp_onboarding_sessions.clear()
    ws._whatsapp_onboarding_sessions["old"] = old_record
    monkeypatch.setattr(ws, "_whatsapp_session_path", lambda: session_dir)
    monkeypatch.setattr(ws.secrets, "token_urlsafe", lambda size: "existing-creds")

    result = asyncio.run(
        ws.start_whatsapp_onboarding(
            ws.WhatsAppOnboardingStart(mode="self-chat", allowed_users="")
        )
    )

    assert result["pairing_id"] == "existing-creds"
    assert result["status"] == "connected"
    assert result["qr_payload"] is None
    assert result["account_id"] == "15551234567:1@s.whatsapp.net"
    assert result["account_name"] == "Hermes Bot"
    assert result["account_phone"] == "15551234567"
    assert old_record.status == "cancelled"
    assert old_proc.terminated is True
    assert ws._whatsapp_onboarding_sessions["existing-creds"].account_phone == "15551234567"
    ws._whatsapp_onboarding_sessions.clear()


def test_effective_messaging_state_not_connected_when_gateway_down():
    from hermes_cli.web_server import _effective_messaging_platform_state

    assert (
        _effective_messaging_platform_state(
            enabled=True,
            configured=True,
            gateway_running=False,
            runtime_state="connected",
            runtime_gateway_state="running",
        )
        == "gateway_stopped"
    )
    assert (
        _effective_messaging_platform_state(
            enabled=True,
            configured=True,
            gateway_running=True,
            runtime_state="connected",
            runtime_gateway_state="running",
        )
        == "connected"
    )


def test_apply_skips_restart_when_whatsapp_already_enabled(monkeypatch):
    from hermes_cli import web_server as ws

    saved = {}
    restarts = []
    monkeypatch.setattr(ws, "save_env_value", lambda key, value: saved.setdefault(key, value))
    monkeypatch.setattr(ws, "_write_platform_enabled", lambda platform, value: None)
    monkeypatch.setattr(ws, "get_env_value", lambda key: {
        "WHATSAPP_ENABLED": "true",
        "WHATSAPP_MODE": "self-chat",
        "WHATSAPP_ALLOWED_USERS": "917015854935",
    }.get(key))
    monkeypatch.setattr(
        ws,
        "_restart_gateway_after_whatsapp_onboarding",
        lambda profile=None, force_new=False: restarts.append((profile, force_new)) or {
            "restart_started": True,
            "restart_pid": 1,
        },
    )

    record = ws._WhatsAppOnboardingSession(
        proc=None,
        mode="self-chat",
        allowed_users="917015854935",
        session_path="/tmp/session",
        expires_at="2099-01-01T00:00:00Z",
        expires_at_ts=time.time() + 600,
        status="connected",
        account_phone="917015854935",
    )
    ws._whatsapp_onboarding_sessions.clear()
    ws._whatsapp_onboarding_sessions["pairing"] = record

    result = asyncio.run(
        ws.apply_whatsapp_onboarding(
            "pairing",
            ws.WhatsAppOnboardingApply(mode="self-chat", allowed_users="917015854935"),
        )
    )

    assert result["ok"] is True
    assert result.get("restart_skipped") is True
    assert restarts == []


def test_apply_forces_fresh_restart_when_enabling_whatsapp(monkeypatch):
    from hermes_cli import web_server as ws

    restarts = []
    monkeypatch.setattr(ws, "save_env_value", lambda key, value: None)
    monkeypatch.setattr(ws, "_write_platform_enabled", lambda platform, value: None)
    monkeypatch.setattr(ws, "get_env_value", lambda key: "")
    monkeypatch.setattr(
        ws,
        "_restart_gateway_after_whatsapp_onboarding",
        lambda profile=None, force_new=False: restarts.append((profile, force_new)) or {
            "restart_started": True,
            "restart_pid": 99,
        },
    )

    record = ws._WhatsAppOnboardingSession(
        proc=None,
        mode="self-chat",
        allowed_users="917015854935",
        session_path="/tmp/session",
        expires_at="2099-01-01T00:00:00Z",
        expires_at_ts=time.time() + 600,
        status="connected",
        account_phone="917015854935",
    )
    ws._whatsapp_onboarding_sessions.clear()
    ws._whatsapp_onboarding_sessions["pairing"] = record

    result = asyncio.run(
        ws.apply_whatsapp_onboarding(
            "pairing",
            ws.WhatsAppOnboardingApply(mode="self-chat", allowed_users="917015854935"),
        )
    )

    assert result["ok"] is True
    assert restarts == [(None, True)]




