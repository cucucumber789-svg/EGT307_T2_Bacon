"""
validate-env.py — Pre-flight check for required environment variables.

Works in standalone mode: loads .env if present, then validates all required
variables are set and not placeholder values. Exits 0 on success, 1 on failure.

Usage:
    python scripts/validate-env.py          # from repo root
    python ../../scripts/validate-env.py    # from a service folder
"""

import os
import sys

# ---------------------------------------------------------------------------
# Terminal colours for readable output
# ---------------------------------------------------------------------------
RED = "\033[0;31m"    # errors / failures
GREEN = "\033[0;32m"  # success
YELLOW = "\033[1;33m" # warnings / hints
NC = "\033[0m"        # reset to default

# ---------------------------------------------------------------------------
# Variable definitions — name, placeholder to flag, and setup hint.
# Add new variables here when the project requires more env vars.
# ---------------------------------------------------------------------------
REQUIRED_VARS = [
    (
        "POSTGRES_USER",
        "",
        "Local dev default — only change if you customised the database service.",
    ),
    (
        "POSTGRES_PASSWORD",
        "",
        "Local dev default — only change if you customised the database service.",
    ),
    (
        "POSTGRES_DB",
        "",
        "Local dev default — only change if you customised the database service.",
    ),
    (
        "TELEGRAM_BOT_TOKEN",
        "your_token_here",
        (
            "Obtained from @BotFather on Telegram:\n"
            "  1. Open Telegram and message @BotFather\n"
            "  2. Send /newbot and follow the prompts\n"
            "  3. Copy the token it gives you (format: 123456789:AA...)\n"
            "  Full guide: components/notification-service/README.md"
        ),
    ),
    (
        "TELEGRAM_CHAT_ID",
        "your_chat_id_here",
        (
            "The chat or group where alerts are sent:\n"
            "  1. Message your bot once (any text) so it can reach you\n"
            "  2. Run: curl \"https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates\"\n"
            '  3. Look for "chat":{"id": <number>} in the response\n'
            "  For groups the id is negative (e.g. -1001234567890)\n"
            "  Full guide: components/notification-service/README.md"
        ),
    ),
]


def load_env_file(path):
    """Parse a .env file and set variables in os.environ (no overwrites).

    Reads key=value pairs, ignoring comments (#) and blank lines.
    Existing environment variables are never overwritten so that
    shell-exported values take precedence over .env defaults.
    """
    if not os.path.isfile(path):
        return False
    with open(path) as f:
        for line in f:
            line = line.strip()
            # Skip blank lines and comments
            if not line or line.startswith("#"):
                continue
            # Skip lines without an equals sign (malformed)
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # Strip surrounding quotes if present
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            # Strip inline comments (everything after the first #)
            if "#" in value:
                value = value[:value.index("#")].strip()
            # Only set if not already in the environment
            if key not in os.environ:
                os.environ[key] = value
    return True


def check_var(name, placeholder="", hint=""):
    """Validate a single environment variable.

    Returns 0 if the variable is set and not a placeholder, 1 otherwise.
    When the check fails and a hint is provided, the hint is printed so
    the developer knows how to obtain the value.
    """
    value = os.environ.get(name, "")
    if not value:
        print(f"  {RED}[FAIL]{NC} {name} is missing or empty")
        if hint:
            print(f"         {YELLOW}{hint}{NC}")
        return 1
    if placeholder and value == placeholder:
        print(f"  {RED}[FAIL]{NC} {name} still has placeholder value: {value}")
        if hint:
            print(f"         {YELLOW}{hint}{NC}")
        return 1
    print(f"  {GREEN}[ OK ]{NC} {name} is set")
    return 0


def find_env_file():
    """Locate the .env file relative to this script's directory.

    Assumes the script lives in <repo-root>/scripts/, so the repo root
    is one directory up.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    return os.path.join(repo_root, ".env")


def main():
    env_path = find_env_file()

    # ------------------------------------------------------------------
    # 1. Check that .env exists — if not, tell the user how to create it
    # ------------------------------------------------------------------
    if not os.path.isfile(env_path):
        print(f"{RED}[env-validator] ERROR: .env file not found at {env_path}{NC}")
        example = os.path.join(os.path.dirname(env_path), ".env.example")
        if os.path.isfile(example):
            print(f"{YELLOW}[env-validator] To get started:{NC}")
            print("  1. Copy the example:  cp .env.example .env")
            print("  2. Edit .env and fill in your values")
        return 1

    # ------------------------------------------------------------------
    # 2. Load values from .env into os.environ (no overwrites)
    # ------------------------------------------------------------------
    load_env_file(env_path)
    print(f"[env-validator] Checking {env_path} ...")

    # ------------------------------------------------------------------
    # 3. Validate each required variable
    # ------------------------------------------------------------------
    errors = 0
    for var_name, placeholder, hint in REQUIRED_VARS:
        errors += check_var(var_name, placeholder, hint)

    # ------------------------------------------------------------------
    # 4. Summary
    # ------------------------------------------------------------------
    print()
    if errors:
        print(f"{RED}[env-validator] {errors} error(s) found. Fix the above issues and try again.{NC}")
        return 1

    print(f"{GREEN}[env-validator] All checks passed.{NC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
