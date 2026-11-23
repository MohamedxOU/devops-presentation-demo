#!/usr/bin/env bash
# Déploie une image sur un environnement : ./scripts/deploy.sh <staging|production> <image:tag>
set -euo pipefail

ENV_NAME="${1:?environnement attendu (staging ou production)}"
IMAGE="${2:?image attendue}"

case "$ENV_NAME" in
  production) PORT=8000 ;;
  staging)    PORT=8001 ;;
  *) echo "Environnement inconnu : $ENV_NAME" >&2; exit 1 ;;
esac

NAME="app-$ENV_NAME"
echo "Déploiement de $IMAGE sur $ENV_NAME (port $PORT)"

docker rm -f "$NAME" >/dev/null 2>&1 || true
docker run -d \
  --name "$NAME" \
  --network devops-demo \
  -p "$PORT:8000" \
  --restart unless-stopped \
  -e APP_ENV="$ENV_NAME" \
  --label "m354.env=$ENV_NAME" \
  "$IMAGE"
