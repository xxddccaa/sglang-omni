from __future__ import annotations

import os
from pathlib import Path

import yaml


def getenv(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value not in (None, "") else default


def build_profile() -> dict[str, str]:
    profile = getenv("S2PRO_DEVICE_PROFILE", "hybrid").lower()

    defaults = {
        "cpu": {
            "engine_device": "cpu",
            "stream_vocoder_device": "cpu",
            "vocoder_device": "cpu",
            "tts_relay_device": "cpu",
        },
        "hybrid": {
            "engine_device": "cuda:0",
            "stream_vocoder_device": "cpu",
            "vocoder_device": "cpu",
            "tts_relay_device": "cuda",
        },
        "gpu": {
            "engine_device": "cuda:0",
            "stream_vocoder_device": "cuda:0",
            "vocoder_device": "cuda:0",
            "tts_relay_device": "cuda",
        },
    }

    if profile not in defaults:
        raise SystemExit(
            f"Unsupported S2PRO_DEVICE_PROFILE={profile!r}. "
            "Use one of: cpu, hybrid, gpu."
        )

    selected = defaults[profile].copy()
    selected["engine_device"] = getenv(
        "S2PRO_ENGINE_DEVICE", selected["engine_device"]
    )
    selected["stream_vocoder_device"] = getenv(
        "S2PRO_STREAM_VOCODER_DEVICE", selected["stream_vocoder_device"]
    )
    selected["vocoder_device"] = getenv(
        "S2PRO_VOCODER_DEVICE", selected["vocoder_device"]
    )
    selected["tts_relay_device"] = getenv(
        "S2PRO_TTS_RELAY_DEVICE", selected["tts_relay_device"]
    )
    selected["profile"] = profile
    return selected


def build_config(profile: dict[str, str]) -> dict:
    model_path = getenv("MODEL_PATH", "/models/s2-pro")
    max_new_tokens = int(getenv("S2PRO_MAX_NEW_TOKENS", "2048"))
    relay_backend = getenv("S2PRO_RELAY_BACKEND", "shm")
    pipeline_name = getenv("S2PRO_PIPELINE_NAME", "s2pro-api")
    mem_fraction_static = float(getenv("S2PRO_MEM_FRACTION_STATIC", "0.85"))
    chunked_prefill_size = int(getenv("S2PRO_CHUNKED_PREFILL_SIZE", "8192"))
    max_running_requests = int(getenv("S2PRO_MAX_RUNNING_REQUESTS", "64"))
    disable_cuda_graph = getenv("S2PRO_DISABLE_CUDA_GRAPH", "false").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    return {
        "config_cls": "S2ProPipelineConfig",
        "model_path": model_path,
        "entry_stage": "preprocessing",
        "stages": [
            {
                "name": "preprocessing",
                "executor": {
                    "factory": "sglang_omni.models.fishaudio_s2_pro.pipeline.stages.create_preprocessing_executor",
                    "args": {},
                },
                "get_next": "sglang_omni.models.fishaudio_s2_pro.pipeline.next_stage.preprocessing_next",
                "input_handler": {"type": "direct"},
                "relay": {
                    "slot_size_mb": 512,
                    "credits": 2,
                    "device": "cpu",
                },
                "num_workers": 1,
                "stream_to": [],
            },
            {
                "name": "tts_engine",
                "executor": {
                    "factory": "sglang_omni.models.fishaudio_s2_pro.pipeline.stages.create_sglang_tts_engine_executor",
                    "args": {
                        "device": profile["engine_device"],
                        "max_new_tokens": max_new_tokens,
                        "stream_vocoder_device": profile["stream_vocoder_device"],
                        "mem_fraction_static": mem_fraction_static,
                        "chunked_prefill_size": chunked_prefill_size,
                        "max_running_requests": max_running_requests,
                        "disable_cuda_graph": disable_cuda_graph,
                    },
                },
                "get_next": "sglang_omni.models.fishaudio_s2_pro.pipeline.next_stage.tts_engine_next",
                "input_handler": {"type": "direct"},
                "relay": {
                    "slot_size_mb": 512,
                    "credits": 2,
                    "device": profile["tts_relay_device"],
                },
                "num_workers": 1,
                "stream_to": [],
            },
            {
                "name": "vocoder",
                "executor": {
                    "factory": "sglang_omni.models.fishaudio_s2_pro.pipeline.stages.create_vocoder_executor",
                    "args": {
                        "device": profile["vocoder_device"],
                    },
                },
                "get_next": "sglang_omni.models.fishaudio_s2_pro.pipeline.next_stage.vocoder_next",
                "input_handler": {"type": "direct"},
                "relay": {
                    "slot_size_mb": 512,
                    "credits": 2,
                    "device": "cpu",
                },
                "num_workers": 1,
                "stream_to": [],
            },
        ],
        "name": pipeline_name,
        "terminal_stages": [],
        "relay_backend": relay_backend,
        "fused_stages": [],
        "endpoints": {
            "scheme": "ipc",
            "base_path": "/tmp/sglang_omni",
            "base_port": 16000,
        },
        "gpu_placement": {},
        "completion_endpoint": None,
        "abort_endpoint": None,
    }


def main() -> None:
    profile = build_profile()
    config = build_config(profile)
    output_path = Path(getenv("S2PRO_CONFIG_PATH", "/tmp/s2pro-runtime.yaml"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, sort_keys=False)

    print(
        yaml.safe_dump(
            {
                "config_path": str(output_path),
                "profile": profile,
            },
            sort_keys=False,
        ).strip()
    )


if __name__ == "__main__":
    main()
