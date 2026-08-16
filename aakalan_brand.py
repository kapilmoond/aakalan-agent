"""Aakalan product identity — single source of truth for client-facing names.

Internal Python packages may still be named hermes_* (upstream architecture).
Everything a client sees — command, folder, GitHub, company — is Aakalan.
"""

PRODUCT_NAME = "Aakalan Agent"
CLI_NAME = "aakalan"
COMPANY_NAME = "Aaklan Infra Consultancy"
WEBSITE = "https://aakalaninfra.com"
SUPPORT_EMAIL = "contact@aakalaninfra.com"

GITHUB_OWNER = "kapilmoond"
GITHUB_REPO = "aakalan-cli"
GITHUB_HTTPS = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}.git"
GITHUB_SSH = f"git@github.com:{GITHUB_OWNER}/{GITHUB_REPO}.git"
GITHUB_CANONICAL = f"github.com/{GITHUB_OWNER}/{GITHUB_REPO}".lower()
GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}"

# Windows: %LOCALAPPDATA%\aakalan   POSIX: ~/.aakalan
HOME_DIRNAME = "aakalan"
# Checkout folder inside home
INSTALL_DIRNAME = "aakalan-cli"
