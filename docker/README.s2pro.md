# FishAudio S2 Docker

This image is intended for serving FishAudio S2 TTS from this repository without
depending on the `sgl-omni` shell script being present in `PATH`.

## Build

Run from the repo root:

```bash
docker build -f docker/Dockerfile.s2pro -t sglang-omni-s2pro:local .
```

If the normal image build fails because `descript-audiotools` conflicts with
the base image's `protobuf/torch/sglang` stack, use the no-deps variant:

```bash
docker build -f docker/Dockerfile.s2pro-nodeps -t sglang-omni-s2pro:nodeps .
```

## Run

Mount your local model directory into `/models/s2-pro`:

```bash
docker run -d \
  --name s2pro-tts \
  --gpus all \
  --shm-size 32g \
  --ipc host \
  --network host \
  -v /path/to/s2-pro:/models/s2-pro:ro \
  sglang-omni-s2pro:local
```

For the no-deps image:

```bash
docker run -d \
  --name s2pro-tts \
  --gpus all \
  --shm-size 32g \
  --ipc host \
  --network host \
  -v /path/to/s2-pro:/models/s2-pro:ro \
  sglang-omni-s2pro:nodeps
```

The container starts:

```bash
python -m sglang_omni.cli.cli serve \
  --model-path /models/s2-pro \
  --config examples/configs/s2pro_tts.yaml \
  --host 0.0.0.0 \
  --port 8000 \
  --model-name s2-pro
```

## Override Defaults

You can override the default startup values via environment variables:

- `MODEL_PATH`
- `CONFIG_PATH`
- `HOST`
- `PORT`
- `MODEL_NAME`
- `LOG_LEVEL`

Example:

```bash
docker run -d \
  --name s2pro-tts \
  --gpus all \
  --shm-size 32g \
  --ipc host \
  --network host \
  -e PORT=9000 \
  -e MODEL_NAME=fish-speech-s2 \
  -v /path/to/s2-pro:/models/s2-pro:ro \
  sglang-omni-s2pro:local
```
