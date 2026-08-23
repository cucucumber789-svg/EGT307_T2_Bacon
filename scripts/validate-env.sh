#!/bin/sh
# =============================================================================
# validate-env.sh — Pre-flight check for required environment variables.
#
# Runs inside the env-validator Docker container. Reads /app/.env and checks
# that every required variable is set and not a placeholder. Exits 0 if all
# checks pass, 1 otherwise. Other services depend on this via a Docker
# healthcheck — they will not start until this passes.
#
# Usage (inside container):
#   /app/scripts/validate-env.sh
# =============================================================================

ENV_FILE="/app/.env"

# ---------------------------------------------------------------------------
# Terminal colours for readable output
# ---------------------------------------------------------------------------
RED='\033[0;31m'    # errors / failures
GREEN='\033[0;32m'  # success
YELLOW='\033[1;33m' # warnings / hints
NC='\033[0m'        # reset to default

errors=0

# ---------------------------------------------------------------------------
# check_var — validate a single variable from the .env file.
#
# Arguments:
#   $1  variable name  (e.g. TELEGRAM_BOT_TOKEN)
#   $2  placeholder    (value that means "not yet configured")
#   $3  hint           (setup instructions shown on failure)
# ---------------------------------------------------------------------------
check_var() {
    var_name="$1"
    placeholder="$2"
    hint="$3"
    # Extract value and strip inline comments (everything after the first #)
    value=$(grep -E "^${var_name}=" "$ENV_FILE" | cut -d'=' -f2- | sed 's/#.*//' | xargs)

    if [ -z "$value" ]; then
        echo "${RED}  [FAIL] $var_name is missing or empty${NC}"
        if [ -n "$hint" ]; then
            echo "         ${YELLOW}${hint}${NC}"
        fi
        errors=$((errors + 1))
    elif [ "$value" = "$placeholder" ]; then
        echo "${RED}  [FAIL] $var_name still has placeholder value: $value${NC}"
        if [ -n "$hint" ]; then
            echo "         ${YELLOW}${hint}${NC}"
        fi
        errors=$((errors + 1))
    else
        echo "${GREEN}  [ OK ] $var_name is set${NC}"
    fi
}

# ---------------------------------------------------------------------------
# 1. Check that .env exists — if not, tell the user how to create it
# ---------------------------------------------------------------------------
if [ ! -f "$ENV_FILE" ]; then
    echo "${RED}[env-validator] ERROR: .env file not found at $ENV_FILE${NC}"
    if [ -f "/app/.env.example" ]; then
        echo "${YELLOW}[env-validator] To get started:${NC}"
        echo "  1. Copy the example:  cp .env.example .env"
        echo "  2. Edit .env and fill in your values"
    fi
    exit 1
fi

# ---------------------------------------------------------------------------
# 2. Validate each required variable
#    Format: check_var NAME PLACEHOLDER "hint text"
#    Empty placeholder string means "any non-empty value is fine".
# ---------------------------------------------------------------------------
echo "[env-validator] Checking $ENV_FILE ..."

check_var "POSTGRES_USER" "" \
    "Local dev default -- only change if you customised the database service."

check_var "POSTGRES_PASSWORD" "" \
    "Local dev default -- only change if you customised the database service."

check_var "POSTGRES_DB" "" \
    "Local dev default -- only change if you customised the database service."

# ---------------------------------------------------------------------------
# 3. Summary
# ---------------------------------------------------------------------------
echo ""

if [ $errors -gt 0 ]; then
    echo "${RED}[env-validator] $errors error(s) found. Fix the above issues and try again.${NC}"
    exit 1
fi

echo "${GREEN}[env-validator] All checks passed.${NC}"
exit 0
