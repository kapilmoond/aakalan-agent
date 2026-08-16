# Aakalan CLI

Local backend for **Aakalan Agent** by **Aaklan Infra Consultancy**.

This is the command-line engine that the Aakalan Agent desktop EXE installs on the client PC.

## What clients see

| Item | Value |
|---|---|
| Product | Aakalan Agent |
| Command | `aakalan` |
| Company | Aaklan Infra Consultancy |
| Home (Windows) | `%LOCALAPPDATA%\aakalan` |
| Checkout | `%LOCALAPPDATA%\aakalan\aakalan-cli` |
| GitHub | `https://github.com/kapilmoond/aakalan-cli` |

Clients should never see Hermes, Nous Research, or the upstream GitHub.

Internal Python packages may still use `hermes_*` names. That is engine plumbing, not the product name.

## Desktop first-run

The Windows EXE installs **locally only**. There is no cloud / remote choice during setup.

## Push this repo

Create an empty GitHub repository named `aakalan-cli` under `kapilmoond`, then:

```bat
cd "C:\Users\LAPTOP PC\Desktop\3_Apps_and_Development\aakalan-cli"
git remote add origin https://github.com/kapilmoond/aakalan-cli.git
git push -u origin main
```

After the first push, rebuild the desktop EXE so first-launch bootstrap can download `scripts/install.ps1` from this repo.
