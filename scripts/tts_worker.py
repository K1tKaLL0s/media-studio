"""One local Qwen3-TTS request per process; stdout contains one JSON result.

Run with the dedicated Python 3.12 environment, never ComfyUI's environment.
The caller supplies --request and --result JSON file paths. Model downloads are
disabled here; installation/model preparation is a separate, explicit action.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
from pathlib import Path
import re
import sys
import time
import traceback
import uuid


DEFAULT_ROOT = str(Path(__file__).resolve().parents[1])
MODELS = {
    "preset": ("Qwen3-TTS-12Hz-1.7B-CustomVoice", "custom_voice", "1b7"),
    "clone": ("Qwen3-TTS-12Hz-0.6B-Base", "base", "0b6"),
}
LANGUAGES = ("Auto", "Chinese", "English", "Japanese", "Korean", "German",
             "French", "Russian", "Portuguese", "Spanish", "Italian")
SPEAKERS = ("Vivian", "Serena", "Uncle_Fu", "Dylan", "Eric", "Ryan", "Aiden",
            "Ono_Anna", "Sohee")


def within(path: Path, parent: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(parent.resolve()):
        raise ValueError(f"Path must be inside {parent}: {resolved}")
    return resolved


def integer(value, name: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return value


def validate_request(request: dict, root: Path) -> dict:
    if not isinstance(request, dict):
        raise ValueError("Request must be a JSON object")
    mode = request.get("mode", "preset")
    if mode not in MODELS:
        raise ValueError("mode must be preset or clone")
    text = request.get("text", "")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty string")
    if len(text) > 4000:
        raise ValueError("text exceeds 4000 characters; split the script into shorter requests")
    language = request.get("language", "Auto")
    if language not in LANGUAGES:
        raise ValueError(f"Unsupported language: {language}")
    instruct = request.get("instruct", "")
    reference_text = request.get("reference_text", "")
    if not isinstance(instruct, str) or not isinstance(reference_text, str):
        raise ValueError("instruct and reference_text must be strings")
    if len(instruct) > 2000:
        raise ValueError("instruct exceeds 2000 characters")
    speaker = request.get("speaker", "Vivian")
    reference_audio = request.get("reference_audio", "")
    if not isinstance(reference_audio, str):
        raise ValueError("reference_audio must be a local file path")
    if mode == "preset":
        if speaker not in SPEAKERS:
            raise ValueError(f"Unsupported preset speaker: {speaker}")
    else:
        if instruct.strip():
            raise ValueError("clone uses the Base model, which does not support instruct")
        if not reference_audio or not reference_text.strip():
            raise ValueError("clone requires reference_audio and its exact reference_text")
        reference_path = Path(reference_audio)
        if not reference_path.is_absolute() or not reference_path.is_file():
            raise ValueError("reference_audio must be an existing absolute local file path")
        if not any(reference_path.resolve().is_relative_to((root / subdir).resolve())
                   for subdir in ("input", "output", "temp")):
            raise ValueError("reference_audio must be inside the studio input, output or temp directory")
        reference_audio = str(reference_path.resolve())
    output_value = request.get("output", "")
    if not isinstance(output_value, str) or not output_value:
        raise ValueError("output must be an absolute WAV file path")
    output = Path(output_value)
    if not output.is_absolute() or output.suffix.lower() != ".wav":
        raise ValueError("output must be an absolute .wav file path")
    output = within(output, root / "output" / "speech")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite an existing output: {output}")
    job_id = request.get("job_id", uuid.uuid4().hex)
    if not isinstance(job_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", job_id):
        raise ValueError("job_id must contain 1-80 letters, digits, underscores or hyphens")
    model_name, model_type, model_size = MODELS[mode]
    model_dir = root / "models" / "tts" / model_name
    required_files = ("config.json", "model.safetensors", "generation_config.json",
                      "preprocessor_config.json", "tokenizer_config.json", "vocab.json", "merges.txt",
                      "speech_tokenizer/config.json", "speech_tokenizer/model.safetensors",
                      "speech_tokenizer/preprocessor_config.json")
    missing = [name for name in required_files if not (model_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Local model is incomplete: {model_dir}; missing {', '.join(missing)}")
    config = json.loads((model_dir / "config.json").read_text(encoding="utf-8"))
    if config.get("tts_model_type") != model_type or config.get("tts_model_size") != model_size:
        raise ValueError(f"Local model config does not match mode={mode}: {model_dir}")
    return dict(mode=mode, text=text.strip(), language=language, speaker=speaker,
                instruct=instruct.strip(), reference_audio=reference_audio,
                reference_text=reference_text.strip(), output=output,
                seed=integer(request.get("seed", 0), "seed", 0, 2**32 - 1),
                max_new_tokens=integer(request.get("max_new_tokens", 1024), "max_new_tokens", 64, 4096),
                job_id=job_id, model_name=model_name, model_dir=model_dir)


def configure_environment(root: Path, job_id: str) -> None:
    locations = {
        "HF_HOME": root / "cache" / "huggingface",
        "HF_HUB_CACHE": root / "cache" / "huggingface" / "hub",
        "TORCH_HOME": root / "cache" / "torch",
        "NUMBA_CACHE_DIR": root / "cache" / "numba",
        "MPLCONFIGDIR": root / "cache" / "matplotlib",
        "PYTHONPYCACHEPREFIX": root / "cache" / "pycache",
        "TEMP": root / "temp" / "tts" / job_id,
        "TMP": root / "temp" / "tts" / job_id,
        "TMPDIR": root / "temp" / "tts" / job_id,
    }
    for name, path in locations.items():
        path.mkdir(parents=True, exist_ok=True)
        os.environ[name] = str(path)
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"


@contextlib.contextmanager
def windows_pread_loading():
    """Avoid persistent Windows COW commit while loading this worker's models.

    Transformers 4.57.3 already initializes on meta and streams tensors to the
    requested CUDA device. Safetensors 0.8's official pread backend avoids the
    persistent whole-file COW mapping. Its header reader still maps briefly,
    so skip the optional allocator preallocation until loading begins. Only
    in-process aliases are changed, and both are restored on every exit.
    """
    if os.name != "nt":
        yield
        return
    import transformers.modeling_utils as modeling_utils

    original_open = modeling_utils.safe_open
    original_warmup = modeling_utils.caching_allocator_warmup

    def pread_open(*args, **kwargs):
        kwargs["backend"] = "pread"
        return original_open(*args, **kwargs)

    modeling_utils.safe_open = pread_open
    modeling_utils.caching_allocator_warmup = lambda *args, **kwargs: None
    try:
        print("Windows model loading: official safetensors pread; allocator warmup skipped", flush=True)
        yield
    finally:
        modeling_utils.safe_open = original_open
        modeling_utils.caching_allocator_warmup = original_warmup


def synthesize(request: dict, root: Path) -> dict:
    options = validate_request(request, root)
    configure_environment(root, options["job_id"])
    # Imports happen only after preflight and local cache/temp routing.
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
    start = time.monotonic()
    with windows_pread_loading():
        model = Qwen3TTSModel.from_pretrained(
            str(options["model_dir"]), device_map="cuda:0", dtype=dtype,
            attn_implementation="sdpa", local_files_only=True,
        )
    common = dict(text=options["text"], language=options["language"],
                  max_new_tokens=options["max_new_tokens"])
    if options["mode"] == "preset":
        wavs, sample_rate = model.generate_custom_voice(
            **common, speaker=options["speaker"], instruct=options["instruct"],
        )
    else:
        reference, reference_rate = sf.read(options["reference_audio"], dtype="float32", always_2d=True)
        reference = reference.mean(axis=1)
        if reference.size == 0 or not np.isfinite(reference).all():
            raise ValueError("Reference audio is empty or contains non-finite samples")
        if float(np.max(np.abs(reference))) < 1e-5:
            raise ValueError("Reference audio is silent")
        wavs, sample_rate = model.generate_voice_clone(
            **common, ref_audio=(reference, reference_rate),
            ref_text=options["reference_text"], x_vector_only_mode=False,
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
    # Exclusive creation protects prior results even if a caller reuses a name.
    with output.open("xb") as stream:
        sf.write(stream, np.clip(waveform, -1.0, 1.0), int(sample_rate),
                 format="WAV", subtype="PCM_16")
    info = sf.info(str(output))
    if info.subtype != "PCM_16" or info.frames != waveform.size or info.channels != 1:
        raise RuntimeError("Saved WAV failed PCM16/frame/channel verification")
    return dict(ok=True, job_id=options["job_id"], output=str(output),
                sample_rate=int(sample_rate), channels=1, frames=int(info.frames),
                duration_seconds=info.frames / int(sample_rate), peak=peak, rms=rms,
                model=options["model_name"], mode=options["mode"], seed=options["seed"],
                elapsed_seconds=round(time.monotonic() - start, 3))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    root = Path(os.environ.get("MEDIA_STUDIO_ROOT", DEFAULT_ROOT)).resolve()
    result = None
    try:
        result_path = within(args.result, root / "temp" / "tts")
        if result_path.exists():
            raise FileExistsError(f"Result file already exists: {result_path}")
        request = json.loads(args.request.read_text(encoding="utf-8-sig"))
        with contextlib.redirect_stdout(sys.stderr):
            result = synthesize(request, root)
    except Exception as exc:
        traceback.print_exc(file=sys.stderr)
        result = {"ok": False, "error": type(exc).__name__, "message": str(exc)}
    # Failure to persist the protocol response is also a nonzero worker failure.
    try:
        result_path = within(args.result, root / "temp" / "tts")
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
