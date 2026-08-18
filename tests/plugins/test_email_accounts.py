from plugins.platforms.email.accounts import (
    infer_provider,
    load_accounts,
    public_account,
    save_accounts,
    upsert_account,
)


def test_infer_provider_gmail_and_workspace():
    assert infer_provider("sdo@gmail.com") == "gmail"
    assert infer_provider("contact@aakalaninfra.com", "imap.gmail.com") == "workspace"


def test_save_and_reload_multiple_accounts(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    first = upsert_account(
        {
            "address": "sdonarwanacad@gmail.com",
            "password": "app-pass-1",
            "provider": "gmail",
        },
        home=tmp_path,
    )
    second = upsert_account(
        {
            "address": "contact@aakalaninfra.com",
            "password": "app-pass-2",
            "provider": "workspace",
            "workspace_full": True,
        },
        home=tmp_path,
    )
    loaded = load_accounts(home=tmp_path)
    assert [item["address"] for item in loaded] == [
        "sdonarwanacad@gmail.com",
        "contact@aakalaninfra.com",
    ]
    assert first["provider"] == "gmail"
    assert second["workspace_full"] is True
    public = public_account(loaded[1])
    assert public["has_password"] is True
    assert "password" not in public


def test_replace_same_address_keeps_one_row(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    upsert_account(
        {"address": "office@gmail.com", "password": "old", "provider": "gmail"},
        home=tmp_path,
    )
    upsert_account(
        {"address": "office@gmail.com", "password": "new", "provider": "gmail"},
        home=tmp_path,
    )
    loaded = load_accounts(home=tmp_path)
    assert len(loaded) == 1
    assert loaded[0]["password"] == "new"
    save_accounts(loaded, home=tmp_path)
    assert (tmp_path / "email_accounts.json").exists()
