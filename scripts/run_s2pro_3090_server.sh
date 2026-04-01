#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-18000}"
MODEL_PATH="${MODEL_PATH:-/data/xiedong/fishaudio/s2-pro}"
CONFIG_PATH="${CONFIG_PATH:-$ROOT_DIR/examples/configs/s2pro_tts_3090.yaml}"

cd "$ROOT_DIR"
exec .venv/bin/sgl-omni serve \
  --model-path "$MODEL_PATH" \
  --config "$CONFIG_PATH" \
  --host "$HOST" \
  --port "$PORT" \
  --log-level info
