#!/bin/sh
# validate-env.sh — Pre-flight check for required environment variables.
# Exits 0 if all variables are set and not placeholders, 1 otherwise.

ENV_FILE="/app/.env"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

errors=0

if [ ! -f "$ENV_FILE" ]; then
    echo "${RED}[env-validator] ERROR: .env file not found at $ENV_FILE${NC}"
    if [ -f "/app/.env.example" ]; then
        echo "${YELLOW}[env-validator] Copy .env.example to .env and fill in your values:${NC}"
        echo "  cp .env.example .env"
    fi
    exit 1
fi

check_var() {
    var_name="$1"
    placeholder="$2"
    value=$(grep -E "^${var_name}=" "$ENV_FILE" | cut -d'=' -f2-)

    if [ -z "$value" ]; then
        echo "${RED}  [FAIL] $var_name is missing or empty${NC}"
        errors=$((errors + 1))
    elif [ "$value" = "$placeholder" ]; then
        echo "${RED}  [FAIL] $var_name still has placeholder value: $value${NC}"
        errors=$((errors + 1))
    else
        echo "${GREEN}  [ OK ] $var_name is set${NC}"
    fi
}

echo "[env-validator] Checking .env ..."

check_var "POSTGRES_USER" ""
check_var "POSTGRES_PASSWORD" ""
check_var "POSTGRES_DB" ""
check_var "TELEGRAM_BOT_TOKEN" "your_token_here"
check_var "TELEGRAM_CHAT_ID" "your_chat_id_here"

echo ""

if [ $errors -gt 0 ]; then
    echo "${RED}[env-validator] $errors error(s) found. Fix the above issues and try again.${NC}"
    exit 1
fi

echo "${GREEN}[env-validator] All checks passed.${NC}"
exit 0
