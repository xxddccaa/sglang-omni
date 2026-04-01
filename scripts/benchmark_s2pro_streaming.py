from __future__ import annotations

import argparse
import base64
import io
import json
import sys
import time
import wave
from pathlib import Path

import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark SGLang-Omni S2-Pro streaming TTS latency."
    )
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000/v1/audio/speech",
        help="Streaming TTS endpoint URL.",
    )
    parser.add_argument(
        "--text",
        default="你好，这是一段用于测试首包延迟的流式语音合成文本。",
        help="Input text to synthesize.",
    )
    parser.add_argument(
        "--ref-audio",
        default=None,
        help="Optional reference audio path for voice cloning.",
    )
    parser.add_argument(
        "--ref-text",
        default=None,
        help="Optional transcript for the reference audio.",
    )
    parser.add_argument(
        "--output",
        default="artifacts/s2pro_stream_output.wav",
        help="Path to save the reconstructed streamed wav.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=600.0,
        help="Request timeout in seconds.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional generation seed for reproducible sampling.",
    )
    return parser.parse_args()


def build_payload(args: argparse.Namespace) -> dict:
    payload: dict = {
        "input": args.text,
        "voice": "default",
        "response_format": "wav",
        "stream": True,
    }
    if args.ref_audio:
        reference: dict[str, str] = {"audio_path": args.ref_audio}
        if args.ref_text:
            reference["text"] = args.ref_text
        payload["references"] = [reference]
    if args.seed is not None:
        payload["seed"] = args.seed
    return payload


def save_wav_chunks(chunks: list[bytes], fmt: tuple[int, int, int], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    nchannels, sampwidth, framerate = fmt
    with wave.open(str(output_path), "wb") as wav_file:
        wav_file.setnchannels(nchannels)
        wav_file.setsampwidth(sampwidth)
        wav_file.setframerate(framerate)
        wav_file.writeframes(b"".join(chunks))


def main() -> int:
    args = parse_args()
    payload = build_payload(args)

    t0 = time.perf_counter()
    first_chunk_at: float | None = None
    fmt: tuple[int, int, int] | None = None
    audio_chunks: list[bytes] = []
    chunk_arrival_ms: list[float] = []
    chunk_count = 0
    final_usage: dict | None = None

    with requests.post(
        args.url,
        json=payload,
        stream=True,
        timeout=args.timeout,
    ) as response:
        response.raise_for_status()
        for raw_line in response.iter_lines(decode_unicode=True):
            if not raw_line or not raw_line.startswith("data: "):
                continue

            data = raw_line[len("data: ") :].strip()
            if data == "[DONE]":
                break

            event = json.loads(data)
            if event.get("audio") is None:
                final_usage = event.get("usage")
                continue

            audio_b64 = event["audio"]["data"]
            wav_bytes = base64.b64decode(audio_b64)
            if first_chunk_at is None:
                first_chunk_at = time.perf_counter()
            chunk_arrival_ms.append(round((time.perf_counter() - t0) * 1000, 2))

            with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
                current_fmt = (
                    wav_file.getnchannels(),
                    wav_file.getsampwidth(),
                    wav_file.getframerate(),
                )
                if fmt is None:
                    fmt = current_fmt
                elif fmt != current_fmt:
                    raise RuntimeError(
                        f"Inconsistent wav format across chunks: {fmt} vs {current_fmt}"
                    )
                audio_chunks.append(wav_file.readframes(wav_file.getnframes()))
            chunk_count += 1

    total_elapsed = time.perf_counter() - t0
    if first_chunk_at is None or fmt is None:
        print("No audio chunk received from streaming endpoint.", file=sys.stderr)
        return 1

    output_path = Path(args.output).resolve()
    save_wav_chunks(audio_chunks, fmt, output_path)

    first_chunk_latency_ms = (first_chunk_at - t0) * 1000
    print(json.dumps(
        {
            "url": args.url,
            "output_path": str(output_path),
            "first_chunk_latency_ms": round(first_chunk_latency_ms, 2),
            "total_elapsed_s": round(total_elapsed, 3),
            "chunk_count": chunk_count,
            "chunk_arrival_ms": chunk_arrival_ms,
            "usage": final_usage,
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
