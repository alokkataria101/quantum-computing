#!/bin/sh
# docker-entrypoint.sh
#
# Resolves the secrets / API-keys file and exports its contents as environment
# variables before starting the application.
#
# Resolution order (first match wins):
#   1. $SECRETS_FILE          — explicit path passed at runtime
#   2. /app/secrets/.env.secrets  — default volume mount location
#   3. /run/secrets/.env.secrets  — Docker Swarm / Compose secrets standard
#   4. No file found           — start without AI (graceful fallback)

set -e

load_secrets() {
    local file="$1"
    if [ -f "$file" ]; then
        echo "[entrypoint] Loading secrets from $file"
        # Export each KEY=VALUE line; skip comments and blank lines
        while IFS= read -r line || [ -n "$line" ]; do
            # Strip inline comments and leading/trailing whitespace
            line=$(echo "$line" | sed 's/#.*//' | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
            [ -z "$line" ] && continue
            case "$line" in
                *=*) export "$line" ;;
            esac
        done < "$file"
        return 0
    fi
    return 1
}

SECRETS_LOADED=false

# 1. Explicit path
if [ -n "$SECRETS_FILE" ]; then
    if load_secrets "$SECRETS_FILE"; then
        SECRETS_LOADED=true
    else
        echo "[entrypoint] WARNING: SECRETS_FILE=$SECRETS_FILE not found."
    fi
fi

# 2. Default volume mount
if [ "$SECRETS_LOADED" = "false" ]; then
    if load_secrets "/app/secrets/.env.secrets"; then
        SECRETS_LOADED=true
    fi
fi

# 3. Docker Swarm / Compose secrets standard
if [ "$SECRETS_LOADED" = "false" ]; then
    if load_secrets "/run/secrets/.env.secrets"; then
        SECRETS_LOADED=true
    fi
fi

if [ "$SECRETS_LOADED" = "false" ]; then
    echo "[entrypoint] No secrets file found — starting without watsonx AI credentials."
    echo "[entrypoint] To enable AI: mount your .env.secrets to /app/secrets/.env.secrets"
fi

exec "$@"
