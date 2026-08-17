#!/usr/bin/env sh
set -u
cd "$(dirname "$0")"
npm run update
status=$?
printf '\nPress Return to close...'
read _ || true
exit "$status"
