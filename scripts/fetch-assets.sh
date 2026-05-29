#!/usr/bin/env bash
# scripts/fetch-assets.sh — one-time download of bundled assets.
# Run from the repo root. Re-run to refresh.
set -euo pipefail

LUCIDE_VERSION="1.14.0"
JBM_VERSION="2.304"

STATIC_DIR="$(cd "$(dirname "$0")/.." && pwd)/src/localhost_pages/static"
LUCIDE_DIR="${STATIC_DIR}/lucide"
WORK="$(mktemp -d)"
trap "rm -rf $WORK" EXIT

echo "Fetching Lucide ${LUCIDE_VERSION}..."
curl -sL "https://github.com/lucide-icons/lucide/releases/download/${LUCIDE_VERSION}/lucide-icons-${LUCIDE_VERSION}.zip" -o "${WORK}/lucide.zip"
unzip -q "${WORK}/lucide.zip" -d "${WORK}/lucide"
rm -rf "${LUCIDE_DIR}"
mkdir -p "${LUCIDE_DIR}"
cp "${WORK}/lucide/icons/"*.svg "${LUCIDE_DIR}/"
echo "  -> $(ls -1 ${LUCIDE_DIR} | wc -l | xargs) icons"

echo "Fetching JetBrains Mono ${JBM_VERSION}..."
curl -sL "https://github.com/JetBrains/JetBrainsMono/releases/download/v${JBM_VERSION}/JetBrainsMono-${JBM_VERSION}.zip" -o "${WORK}/jbm.zip"
unzip -q "${WORK}/jbm.zip" -d "${WORK}/jbm"
cp "${WORK}/jbm/fonts/webfonts/JetBrainsMono-Regular.woff2" "${STATIC_DIR}/JetBrainsMono.woff2"
echo "  -> $(ls -lh ${STATIC_DIR}/JetBrainsMono.woff2 | awk '{print $5}')"

echo "Done."
