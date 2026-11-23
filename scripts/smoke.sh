#!/usr/bin/env bash
# Smoke test : ./scripts/smoke.sh <hôte> [version attendue]
# Vérifie que /health répond et, si demandé, que /version renvoie la bonne version.
set -euo pipefail

HOST="${1:?hôte attendu, ex. app-production}"
EXPECTED="${2:-}"
BASE="http://$HOST:8000"

for i in $(seq 1 30); do
  if curl -fsS "$BASE/health" >/dev/null 2>&1; then
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "ÉCHEC : $BASE/health ne répond pas" >&2
    exit 1
  fi
  sleep 1
done

VERSION_JSON="$(curl -fsS "$BASE/version")"
echo "Réponse /version : $VERSION_JSON"

if [ -n "$EXPECTED" ]; then
  ACTUAL="$(printf '%s' "$VERSION_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["version"])')"
  if [ "$ACTUAL" != "$EXPECTED" ]; then
    echo "ÉCHEC : version $ACTUAL en ligne, $EXPECTED attendue" >&2
    exit 1
  fi
fi

curl -fsS "$BASE/" | grep -q "Planning des exposés" || { echo "ÉCHEC : page d'accueil" >&2; exit 1; }
echo "Smoke test OK sur $HOST"
