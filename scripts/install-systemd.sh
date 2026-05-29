#!/usr/bin/env bash
# Render scripts/localhost-pages.service.template for the current user and
# install it as a systemd --user unit. Idempotent: re-running re-renders.
set -euo pipefail

UNIT_NAME="${LOCALHOST_PAGES_UNIT:-localhost-pages.service}"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
UV_PATH="$(command -v uv || true)"

if [[ -z "$UV_PATH" ]]; then
    echo "error: 'uv' not found on PATH. Install uv first: https://docs.astral.sh/uv/" >&2
    exit 1
fi

PATH_ENV="$(dirname "$UV_PATH"):/usr/local/bin:/usr/bin:/bin"
DEST_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
DEST="${DEST_DIR}/${UNIT_NAME}"

mkdir -p "$DEST_DIR"

sed \
    -e "s|__UV_PATH__|${UV_PATH}|g" \
    -e "s|__PROJECT_DIR__|${PROJECT_DIR}|g" \
    -e "s|__PATH_ENV__|${PATH_ENV}|g" \
    "${PROJECT_DIR}/scripts/localhost-pages.service.template" > "$DEST"

systemctl --user daemon-reload
systemctl --user enable --now "$UNIT_NAME"

echo "Installed systemd user unit: $DEST"
echo "Status:  systemctl --user status $UNIT_NAME"
echo "Logs:    journalctl --user -u $UNIT_NAME -f"
echo "Stop:    systemctl --user stop $UNIT_NAME"
echo "Disable: systemctl --user disable --now $UNIT_NAME"
echo
echo "To keep the service running when you're not logged in:"
echo "  sudo loginctl enable-linger \"\$USER\""
