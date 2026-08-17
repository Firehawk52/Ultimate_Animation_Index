#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
URL="http://localhost:${PORT:-8787}"
if ! command -v node >/dev/null 2>&1; then
  printf '\nUltimate Animation Index needs Node.js 20 or newer.\nInstall Node.js, then run this file again.\n\n' >&2
  printf 'Press Return to close...'
  read _ || true
  exit 1
fi
(
  i=0
  while [ "$i" -lt 80 ]; do
    if command -v curl >/dev/null 2>&1 && curl -fsS "$URL/api/health" >/dev/null 2>&1; then
      open "$URL" >/dev/null 2>&1 || true
      exit 0
    fi
    i=$((i+1))
    sleep 0.25
  done
) &
printf '\nUltimate Animation Index\nStarting the site and opening it in your default browser...\nKeep this window open while you use the site.\nPress Ctrl+C to stop the local server.\n\n'
exec npm start
