"""Offline Qwen3-TTS VoiceDesign worker; one explicitly requested job per process.

Uses the existing TTS environment without modifying it. Preparing this file does
not load a model. Integration was checked statically; inference is unverified.
"""
from __future__ import annotations

import argparse
import contextlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time
import traceback
import uuid


DEFAULT_ROOT = str(Path(__file__).resolve().parents[1])
MODEL_NAME = "Qwen3-TTS-12Hz-1.7B-VoiceDesign"
MODEL_REVISION = "5ecdb67327fd37bb2e042aab12ff7391903235d3"
LANGUAGES = ("Auto", "Chinese", "English", "Japanese", "Korean", "German",
             "French", "Russian", "Portuguese", "Spanish", "Italian")


def existing_helpers():
    # Explicit sibling loading also works with the caller's isolated (-I) Python.
    # tts_worker defines stdlib helpers at import time; its models load only in
    # synthesize(), which is never called by this adapter.
    path = Path(__file__).resolve().with_name("tts_worker.py")
    spec = importlib.util.spec_from_file_location("media_studio_tts_helpers", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot locate existing TTS helpers: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_request(request: dict, root: Path, helpers) -> dict:
    if not isinstance(request, dict):
        raise ValueError("Request must be a JSON object")
    if request.get("mode", "voice_design") != "voice_design":
        raise ValueError("This worker only supports voice_design")
    if any(request.get(key) for key in ("speaker", "reference_audio", "reference_text")):
        raise ValueError("VoiceDesign uses a description, without a speaker or reference recording")
    text, instruct = request.get("text", ""), request.get("instruct", "")
    if not isinstance(text, str) or not text.strip() or len(text) > 4000:
        raise ValueError("text must contain 1-4000 characters; split longer scripts")
    if not isinstance(instruct, str) or not instruct.strip() or len(instruct) > 2000:
        raise ValueError("instruct must describe the voice in 1-2000 characters")
    language = request.get("language", "Chinese")
    if language not in LANGUAGES:
        raise ValueError(f"Unsupported language: {language}")
    output_value = request.get("output", "")
    if not isinstance(output_value, str) or not output_value:
        raise ValueError("output must be an absolute WAV file path")
    output = Path(output_value)
    if not output.is_absolute() or output.suffix.lower() != ".wav":
        raise ValueError("output must be an absolute .wav file path")
    output = helpers.within(output, root / "output" / "speech")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite an existing output: {output}")
    job_id = request.get("job_id", uuid.uuid4().hex)
    if not isinstance(job_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", job_id):
        raise ValueError("job_id must contain 1-80 letters, digits, underscores or hyphens")
    model_dir = root / "models" / "tts" / MODEL_NAME
    required_files = ("config.json", "model.safetensors", "generation_config.json",
                      "preprocessor_config.json", "tokenizer_config.json", "vocab.json", "merges.txt",
                      "speech_tokenizer/config.json", "speech_tokenizer/model.safetensors",
                      "speech_tokenizer/preprocessor_config.json")
    missing = [name for name in required_files if not (model_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Local VoiceDesign model is incomplete: {', '.join(missing)}")
    config = json.loads((model_dir / "config.json").read_text(encoding="utf-8-sig"))
    if config.get("tts_model_type") != "voice_design" or config.get("tts_model_size") != "1b7":
        raise ValueError(f"Local model config is not the expected VoiceDesign 1.7B: {model_dir}")
    return dict(text=text.strip(), instruct=instruct.strip(), language=language,
                output=output, job_id=job_id, model_dir=model_dir,
                seed=helpers.integer(request.get("seed", 42), "seed", 0, 2**32 - 1),
                max_new_tokens=helpers.integer(request.get("max_new_tokens", 1024),
                                               "max_new_tokens", 64, 4096))


def synthesize(request: dict, root: Path, helpers) -> dict:
    options = validate_request(request, root, helpers)
    helpers.configure_environment(root, options["job_id"])
    os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
    import numpy as np
    import soundfile as sf
    import torch
    from qwen_tts import Qwen3TTSModel

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable in the dedicated TTS environment")
    torch.manual_seed(options["seed"])
    np.random.seed(options["seed"])
    torch.cuda.manual_seed_all(options["seed"])
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    started = time.monotonic()
    with helpers.windows_pread_loading():
        model = Qwen3TTSModel.from_pretrained(
            str(options["model_dir"]), device_map="cuda:0", dtype=dtype,
            attn_implementation="sdpa", local_files_only=True,
        )
    wavs, sample_rate = model.generate_voice_design(
        text=options["text"], language=options["language"], instruct=options["instruct"],
        max_new_tokens=options["max_new_tokens"],
    )
    if len(wavs) != 1:
        raise RuntimeError("Expected one generated waveform")
    waveform = np.asarray(wavs[0], dtype=np.float32)
    if waveform.ndim != 1 or waveform.size == 0 or not np.isfinite(waveform).all():
        raise RuntimeError("Generated waveform is empty, non-mono or non-finite")
    peak = float(np.max(np.abs(waveform)))
    rms = float(np.sqrt(np.mean(np.square(waveform, dtype=np.float64))))
    if peak < 1e-5 or rms < 1e-7:
        raise RuntimeError("Generated audio is silent")
    if not isinstance(sample_rate, (int, np.integer)) or not 8000 <= sample_rate <= 192000:
        raise RuntimeError(f"Invalid output sample rate: {sample_rate}")
    output = options["output"]
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        sf.write(stream, np.clip(waveform, -1.0, 1.0), int(sample_rate),
                 format="WAV", subtype="PCM_16")
    info = sf.info(str(output))
    if info.subtype != "PCM_16" or info.frames != waveform.size or info.channels != 1:
        raise RuntimeError("Saved WAV failed PCM16/frame/channel verification")
    return dict(ok=True, job_id=options["job_id"], output=str(output),
                sample_rate=int(sample_rate), channels=1, frames=int(info.frames),
                duration_seconds=info.frames / int(sample_rate), peak=peak, rms=rms,
                model=MODEL_NAME, model_revision=MODEL_REVISION, mode="voice_design",
                seed=options["seed"], elapsed_seconds=round(time.monotonic() - started, 3))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    root = Path(os.environ.get("MEDIA_STUDIO_ROOT", DEFAULT_ROOT)).resolve()
    helpers = existing_helpers()
    try:
        result_path = helpers.within(args.result, root / "temp" / "tts")
        request_path = helpers.within(args.request, root / "temp" / "tts")
        if result_path.exists():
            raise FileExistsError(f"Result file already exists: {result_path}")
        if request_path.parent != result_path.parent:
            raise ValueError("Request and result must belong to the same job directory")
        request = json.loads(request_path.read_text(encoding="utf-8-sig"))
        if not isinstance(request, dict) or request_path.parent.name != request.get("job_id"):
            raise ValueError("Request job_id does not match its directory")
        with contextlib.redirect_stdout(sys.stderr):
            result = synthesize(request, root, helpers)
    except Exception as exc:
        traceback.print_exc(file=sys.stderr)
        result = {"ok": False, "error": type(exc).__name__, "message": str(exc)}
    try:
        result_path = helpers.within(args.result, root / "temp" / "tts")
        result_path.parent.mkdir(parents=True, exist_ok=True)
        with result_path.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
    except Exception:
        traceback.print_exc(file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
