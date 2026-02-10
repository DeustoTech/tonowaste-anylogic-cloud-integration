#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "ERROR: ${ENV_FILE} no existe. Crea .env desde .env.template."
  exit 1
fi

set -a
source "${ENV_FILE}"
set +a

required_vars=(
  IMAGE_NAME
  IMAGE_TAG
  REGISTRY_NS
  REGISTRY_USERNAME
  REGISTRY_PASSWORD
)

for var_name in "${required_vars[@]}"; do
  if [[ -z "${!var_name:-}" ]]; then
    echo "ERROR: La variable ${var_name} no está definida en .env"
    exit 1
  fi
done

LOCAL_IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"
REMOTE_IMAGE="${REGISTRY_NS}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "Building image ${LOCAL_IMAGE}..."
docker build --no-cache -t "${LOCAL_IMAGE}" "${ROOT_DIR}"

echo "Logging in to registry..."
printf '%s' "${REGISTRY_PASSWORD}" | docker login --username "${REGISTRY_USERNAME}" --password-stdin

echo "Tagging ${LOCAL_IMAGE} -> ${REMOTE_IMAGE}..."
docker tag "${LOCAL_IMAGE}" "${REMOTE_IMAGE}"

echo "Pushing ${REMOTE_IMAGE}..."
docker push "${REMOTE_IMAGE}"

echo "Done."
