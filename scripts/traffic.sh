#!/usr/bin/env bash
# Génère un peu de trafic pour animer Grafana pendant la démo.
# Usage : ./scripts/traffic.sh [url] (Ctrl+C pour arrêter)
URL="${1:-http://localhost:8000}"
echo "Trafic vers $URL (Ctrl+C pour arrêter)"
while true; do
  curl -s -o /dev/null "$URL/"
  curl -s -o /dev/null "$URL/api/exposes"
  curl -s -o /dev/null "$URL/api/exposes/$((RANDOM % 10))"
  sleep 0.3
done
