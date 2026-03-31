#!/usr/bin/env bash
set -euo pipefail

cd /workspace/sglang-omni

MODEL_PATH="${MODEL_PATH:-/models/s2-pro}"
CONFIG_PATH="${CONFIG_PATH:-examples/configs/s2pro_tts.yaml}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
MODEL_NAME="${MODEL_NAME:-s2-pro}"
LOG_LEVEL="${LOG_LEVEL:-info}"

exec python -m sglang_omni.cli.cli serve \
  --model-path "${MODEL_PATH}" \
  --config "${CONFIG_PATH}" \
  --host "${HOST}" \
  --port "${PORT}" \
  --model-name "${MODEL_NAME}" \
  --log-level "${LOG_LEVEL}"
