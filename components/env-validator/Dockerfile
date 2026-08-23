# =============================================================================
# env-validator — Lightweight container that checks .env before services start.
#
# This container runs validate-env.sh as a Docker healthcheck. All other
# services in docker-compose.yml depend on it being healthy, so they will
# not start until the environment is validated.
#
# Build context is the repo root (not this folder) so it can access both
# .env and scripts/ via volume mounts.
#
# See: ARCHITECTURE.md — Configuration & Secrets
# =============================================================================

FROM alpine:latest

# bash is needed for the colour codes and shell features in the script
RUN apk add --no-cache bash

COPY scripts/validate-env.sh /app/scripts/validate-env.sh
RUN chmod +x /app/scripts/validate-env.sh

CMD ["tail", "-f", "/dev/null"]
