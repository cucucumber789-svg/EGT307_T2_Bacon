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

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
NC = "\033[0m"


def load_env_file(path):
    """Parse a .env file and set variables in os.environ (no overwrites)."""
    if not os.path.isfile(path):
        return False
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # strip surrounding quotes
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            if key not in os.environ:
                os.environ[key] = value
    return True


def check_var(name, placeholder=""):
    value = os.environ.get(name, "")
    if not value:
        print(f"  {RED}[FAIL]{NC} {name} is missing or empty")
        return 1
    if placeholder and value == placeholder:
        print(f"  {RED}[FAIL]{NC} {name} still has placeholder value: {value}")
        return 1
    print(f"  {GREEN}[ OK ]{NC} {name} is set")
    return 0


def find_env_file():
    """Search for .env relative to this script's location (repo root)."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    return os.path.join(repo_root, ".env")


def main():
    env_path = find_env_file()

    if not os.path.isfile(env_path):
        print(f"{RED}[env-validator] ERROR: .env file not found at {env_path}{NC}")
        example = os.path.join(os.path.dirname(env_path), ".env.example")
        if os.path.isfile(example):
            print(f"{YELLOW}[env-validator] Copy .env.example to .env and fill in your values:{NC}")
            print("  cp .env.example .env")
        return 1

    load_env_file(env_path)
    print(f"[env-validator] Checking {env_path} ...")

    errors = 0
    errors += check_var("POSTGRES_USER")
    errors += check_var("POSTGRES_PASSWORD")
    errors += check_var("POSTGRES_DB")
    errors += check_var("TELEGRAM_BOT_TOKEN", "your_token_here")
    errors += check_var("TELEGRAM_CHAT_ID", "your_chat_id_here")

    print()
    if errors:
        print(f"{RED}[env-validator] {errors} error(s) found. Fix the above issues and try again.{NC}")
        return 1

    print(f"{GREEN}[env-validator] All checks passed.{NC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
