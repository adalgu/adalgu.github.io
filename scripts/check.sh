#!/bin/sh
# One command: pull -> hugo build -> static server -> browser check -> stop.
#   make check            (or: npm run check)
#   NO_PULL=1 make check  skip git pull · SAMPLE=20 limit pages · PORT=4173
set -u
cd "$(dirname "$0")/.." || exit 1
PORT="${PORT:-4173}"
OUT="${OUT:-$(mktemp -d)/public}"
[ -z "${NO_PULL:-}" ] && { git pull --ff-only || exit 1; }
hugo --minify --baseURL "http://127.0.0.1:$PORT/" --destination "$OUT" || exit 1
python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$OUT" >/dev/null 2>&1 &
SERVER=$!
trap 'kill $SERVER 2>/dev/null' EXIT INT TERM
sleep 1
node scripts/site_check.mjs --base "http://127.0.0.1:$PORT" --sample "${SAMPLE:-0}" --recent 5
