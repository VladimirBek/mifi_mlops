#!/usr/bin/env bash
set -e

IMAGE_NAME="credit-backend:latest"

docker build -t "${IMAGE_NAME}" .
docker run --rm -p 8000:8000 "${IMAGE_NAME}"
