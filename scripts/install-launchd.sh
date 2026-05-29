#!/usr/bin/env bash
# Render scripts/launchd.plist.template for the current user and install it
# as a launchd user agent. Idempotent: re-running re-renders and reloads.
set -euo pipefail

LABEL="${LOCALHOST_PAGES_LABEL:-localhost-pages}"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
UV_PATH="$(command -v uv || true)"

if [[ -z "$UV_PATH" ]]; then
    echo "error: 'uv' not found on PATH. Install uv first: https://docs.astral.sh/uv/" >&2
    exit 1
fi

LOG_PATH="$HOME/Library/Logs/${LABEL}.log"
BOOT_LOG_PATH="$HOME/Library/Logs/${LABEL}.boot.log"
PATH_ENV="$(dirname "$UV_PATH"):/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
DEST="$HOME/Library/LaunchAgents/${LABEL}.plist"

mkdir -p "$(dirname "$DEST")" "$(dirname "$LOG_PATH")"

sed \
    -e "s|__LABEL__|${LABEL}|g" \
    -e "s|__UV_PATH__|${UV_PATH}|g" \
    -e "s|__PROJECT_DIR__|${PROJECT_DIR}|g" \
    -e "s|__LOG_PATH__|${LOG_PATH}|g" \
    -e "s|__BOOT_LOG_PATH__|${BOOT_LOG_PATH}|g" \
    -e "s|__PATH_ENV__|${PATH_ENV}|g" \
    "${PROJECT_DIR}/scripts/launchd.plist.template" > "$DEST"

launchctl unload "$DEST" 2>/dev/null || true
launchctl load "$DEST"

echo "Installed launchd agent: $DEST"
echo "Logs: $LOG_PATH"
echo "Stop:    launchctl unload \"$DEST\""
echo "Restart: launchctl unload \"$DEST\" && launchctl load \"$DEST\""
