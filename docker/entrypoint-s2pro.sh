#!/usr/bin/env bash
set -euo pipefail

export HOST="${HOST:-0.0.0.0}"
export PORT="${PORT:-18000}"
export MODEL_PATH="${MODEL_PATH:-/models/s2-pro}"
export S2PRO_CONFIG_PATH="${S2PRO_CONFIG_PATH:-/tmp/s2pro-runtime.yaml}"

python /app/scripts/render_s2pro_runtime_config.py

exec sgl-omni serve \
  --model-path "${MODEL_PATH}" \
  --config "${S2PRO_CONFIG_PATH}" \
  --host "${HOST}" \
  --port "${PORT}" \
  --log-level "${LOG_LEVEL:-info}"
