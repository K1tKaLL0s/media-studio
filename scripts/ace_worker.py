"""ACE-Step 1.5 text-to-music worker; one future request per isolated process.

Prepared by static source inspection only. This file has not been run with models.
Model preparation is separate: this worker never downloads missing models.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
import time
import traceback


DEFAULT_ROOT = str(Path(__file__).resolve().parents[1])
MODEL = "acestep-v15-turbo"
LM = "acestep-5Hz-lm-0.6B"
REQUIRED = (
    "acestep-v15-turbo/config.json", "acestep-v15-turbo/model.safetensors",
    "acestep-v15-turbo/configuration_acestep_v15.py",
    "acestep-v15-turbo/modeling_acestep_v15_turbo.py",
    "acestep-v15-turbo/silence_latent.pt", "vae/config.json",
    "vae/diffusion_pytorch_model.safetensors", "Qwen3-Embedding-0.6B/config.json",
    "Qwen3-Embedding-0.6B/model.safetensors", "Qwen3-Embedding-0.6B/tokenizer.json",
    "Qwen3-Embedding-0.6B/tokenizer_config.json", "Qwen3-Embedding-0.6B/vocab.json",
    "Qwen3-Embedding-0.6B/merges.txt", "Qwen3-Embedding-0.6B/added_tokens.json",
    "Qwen3-Embedding-0.6B/special_tokens_map.json", "Qwen3-Embedding-0.6B/chat_template.jinja",
    "acestep-5Hz-lm-0.6B/config.json", "acestep-5Hz-lm-0.6B/model.safetensors",
    "acestep-5Hz-lm-0.6B/tokenizer.json", "acestep-5Hz-lm-0.6B/tokenizer_config.json",
    "acestep-5Hz-lm-0.6B/vocab.json", "acestep-5Hz-lm-0.6B/merges.txt",
    "acestep-5Hz-lm-0.6B/added_tokens.json", "acestep-5Hz-lm-0.6B/special_tokens_map.json",
    "acestep-5Hz-lm-0.6B/chat_template.jinja",
)


def within(value: Path, parent: Path) -> Path:
    value = value.resolve()
    if not value.is_relative_to(parent.resolve()):
        raise ValueError(f"Path must be inside {parent}: {value}")
    return value


def integer(value, name: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer between {minimum} and {maximum}")
    return value


def text(value, name: str, maximum: int, required: bool = False) -> str:
    if not isinstance(value, str) or len(value) > maximum or (required and not value.strip()):
        raise ValueError(f"{name} must be a {'nonempty ' if required else ''}string of at most {maximum} characters")
    return value.strip()


def validate_request(request: dict, root: Path) -> dict:
    if not isinstance(request, dict):
        raise ValueError("Request must be an object")
    job_id = request.get("job_id", "")
    if not isinstance(job_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", job_id):
        raise ValueError("Invalid job_id")
    caption = text(request.get("caption", ""), "caption", 512, required=True)
    lyrics = text(request.get("lyrics", ""), "lyrics", 4096)
    instrumental = request.get("instrumental", False)
    thinking = request.get("thinking", True)
    if not isinstance(instrumental, bool) or not isinstance(thinking, bool):
        raise ValueError("instrumental and thinking must be booleans")
    language = request.get("vocal_language", "unknown")
    if language not in ("unknown", "zh", "en", "ja"):
        raise ValueError("vocal_language must be unknown, zh, en or ja")
    duration = request.get("duration_seconds", 30)
    if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not math.isfinite(duration) or not 10 <= duration <= 120:
        raise ValueError("duration_seconds must be between 10 and 120 for this conservative 8GB profile")
    bpm = integer(request.get("bpm", 0), "bpm", 0, 300)
    if 0 < bpm < 30:
        raise ValueError("bpm must be 0 (auto) or 30-300")
    timesignature = request.get("timesignature", "")
    if timesignature not in ("", "2", "3", "4", "6"):
        raise ValueError("Unsupported timesignature")
    keyscale = text(request.get("keyscale", ""), "keyscale", 40)
    output_value = request.get("output", "")
    if not isinstance(output_value, str):
        raise ValueError("output must be an absolute WAV path")
    output = Path(output_value)
    if not output.is_absolute() or output.suffix.lower() != ".wav":
        raise ValueError("output must be an absolute WAV path")
    output = within(output, root / "output/music")
    if output.name != f"music_{job_id}.wav":
        raise ValueError("output filename must match the request job_id")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite output: {output}")
    checkpoints = root / "models/music/ACE-Step-1.5/checkpoints"
    missing = [name for name in REQUIRED if not (checkpoints / name).is_file()]
    if missing:
        raise FileNotFoundError(f"ACE-Step selected local files are incomplete: {missing}")
    source = root / "runtime/ACE-Step-1.5"
    if not (source / "acestep/inference.py").is_file():
        raise FileNotFoundError(f"Official ACE-Step source is missing: {source}")
    return dict(caption=caption, lyrics="[Instrumental]" if instrumental else lyrics,
                instrumental=instrumental, vocal_language=language, thinking=thinking,
                duration=float(duration), bpm=bpm or None, keyscale=keyscale,
                timesignature=timesignature, output=output, source=source,
                checkpoints=checkpoints, job_id=job_id,
                seed=integer(request.get("seed", 42), "seed", 0, 2**32 - 1))


def configure_environment(root: Path, job_id: str) -> Path:
    work = root / "temp/music" / job_id
    locations = {
        "HF_HOME": root / "cache/huggingface", "HF_HUB_CACHE": root / "cache/huggingface/hub",
        "HF_MODULES_CACHE": root / "cache/huggingface/modules", "TORCH_HOME": root / "cache/torch",
        "MODELSCOPE_CACHE": root / "cache/modelscope", "NUMBA_CACHE_DIR": root / "cache/numba",
        "MPLCONFIGDIR": root / "cache/matplotlib", "TORCHINDUCTOR_CACHE_DIR": root / "cache/torchinductor",
        "PYTHONPYCACHEPREFIX": root / "cache/pycache", "TEMP": work, "TMP": work, "TMPDIR": work,
    }
    for key, path in locations.items():
        path.mkdir(parents=True, exist_ok=True)
        os.environ[key] = str(path)
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1",
                      HF_HUB_DISABLE_IMPLICIT_TOKEN="1", TOKENIZERS_PARALLELISM="false",
                      PYTHONDONTWRITEBYTECODE="1", DO_NOT_TRACK="1")
    return work


def prepare_job_checkpoints(source: Path, work: Path) -> Path:
    """Preserve verified originals when upstream syncs local model Python files.

    Only large safetensors/PT weights are linked; all small files and Python
    source are copies. No package code is changed. N source and destination
    share a volume; fail on hard-link failure instead of silently copying GBs.
    """
    target = work / "checkpoints"
    target.mkdir(exist_ok=False)
    for component in (MODEL, "vae", "Qwen3-Embedding-0.6B", LM):
        for original in (source / component).rglob("*"):
            if original.is_symlink():
                raise ValueError(f"Symlink not allowed in prepared checkpoints: {original}")
            if not original.is_file():
                continue
            destination = target / original.relative_to(source)
            destination.parent.mkdir(parents=True, exist_ok=True)
            if original.suffix in (".safetensors", ".pt"):
                os.link(original, destination)
            else:
                shutil.copy2(original, destination)
    return target


def generate(request: dict, root: Path) -> dict:
    options = validate_request(request, root)
    work = configure_environment(root, options["job_id"])
    checkpoints = prepare_job_checkpoints(options["checkpoints"], work)
    os.environ["ACESTEP_CHECKPOINTS_DIR"] = str(checkpoints)
    # -I disables implicit source injection; add only this trusted fixed source.
    sys.path.insert(0, str(options["source"]))
    import numpy as np
    import soundfile as sf
    import torch
    from acestep.handler import AceStepHandler
    from acestep.llm_inference import LLMHandler
    from acestep.inference import GenerationParams, GenerationConfig, generate_music

    class LocalOnlyHandler(AceStepHandler):
        def _ensure_models_present(self, *, checkpoint_path, config_path, prefer_source, vae_variant=None):
            # Do not call upstream ensure_main_model: its default includes 1.7B
            # and may fall back to ModelScope independently of HF offline mode.
            if config_path != MODEL or vae_variant not in (None, "official"):
                return "Only the prepared standard turbo / official VAE profile is allowed", False
            absent = [name for name in REQUIRED if not (Path(checkpoint_path) / name).is_file()]
            if absent:
                return f"Selected local checkpoints are incomplete: {absent}", False
            return None

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required by this prepared 8GB profile")
    torch.manual_seed(options["seed"])
    np.random.seed(options["seed"])
    started = time.monotonic()
    dit = LocalOnlyHandler()
    status, ok = dit.initialize_service(
        project_root=str(options["source"]), config_path=MODEL, device="cuda",
        use_flash_attention=False, compile_model=False, offload_to_cpu=True,
        offload_dit_to_cpu=True, quantization=None, use_mlx_dit=False,
        vae_checkpoint="official",
    )
    if not ok:
        raise RuntimeError(f"ACE-Step initialization failed: {status}")
    lm = LLMHandler()
    if options["thinking"]:
        status, ok = lm.initialize(checkpoint_dir=str(checkpoints), lm_model_path=LM,
                                    backend="pt", device="cuda", offload_to_cpu=True)
        if not ok:
            raise RuntimeError(f"ACE-Step 0.6B LM initialization failed: {status}")
    params = GenerationParams(
        task_type="text2music", caption=options["caption"], lyrics=options["lyrics"],
        instrumental=options["instrumental"], vocal_language=options["vocal_language"],
        duration=options["duration"], bpm=options["bpm"], keyscale=options["keyscale"],
        timesignature=options["timesignature"], inference_steps=8, guidance_scale=1.0,
        shift=3.0, seed=options["seed"], thinking=options["thinking"],
        use_cot_metas=options["thinking"], use_cot_caption=False,
        use_cot_lyrics=False, use_cot_language=False,
    )
    config = GenerationConfig(batch_size=1, allow_lm_batch=False, use_random_seed=False,
                              seeds=[options["seed"]], lm_batch_chunk_size=1, audio_format="wav")
    result = generate_music(dit, lm, params, config, save_dir=str(work / "rendered"))
    if not result.success or len(result.audios) != 1:
        raise RuntimeError(f"ACE-Step generation failed: {result.error or result.status_message}")
    audio = result.audios[0]
    tensor = audio.get("tensor")
    if not isinstance(tensor, torch.Tensor):
        raise RuntimeError("ACE-Step result contains no AUDIO tensor")
    waveform = tensor.detach().to(device="cpu", dtype=torch.float32).numpy()
    if waveform.ndim != 2 or waveform.shape[0] not in (1, 2) or waveform.shape[1] < 1 or not np.isfinite(waveform).all():
        raise RuntimeError("ACE-Step result is empty or has unsupported channels/nonfinite values")
    peak = float(np.max(np.abs(waveform)))
    rms = float(np.sqrt(np.mean(np.square(waveform, dtype=np.float64))))
    if peak < 1e-5 or rms < 1e-7:
        raise RuntimeError("ACE-Step generated audio is silent")
    sample_rate = audio.get("sample_rate")
    if isinstance(sample_rate, bool) or not isinstance(sample_rate, int) or not 8000 <= sample_rate <= 192000:
        raise RuntimeError("Invalid ACE-Step output sample rate")
    output = options["output"]
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        sf.write(stream, np.clip(waveform.T, -1.0, 1.0), sample_rate, format="WAV", subtype="PCM_16")
    info = sf.info(str(output))
    if info.subtype != "PCM_16" or info.frames != waveform.shape[1] or info.channels != waveform.shape[0]:
        raise RuntimeError("Saved WAV does not match the generated tensor")
    return dict(ok=True, job_id=options["job_id"], output=str(output), sample_rate=sample_rate,
                channels=info.channels, frames=info.frames, duration_seconds=info.frames/sample_rate,
                peak=peak, rms=rms,
                model=MODEL, lm=LM if options["thinking"] else None, mode="text2music",
                seed=options["seed"], elapsed_seconds=round(time.monotonic()-started, 3))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    root = Path(os.environ.get("MEDIA_STUDIO_ROOT", DEFAULT_ROOT)).resolve()
    result_path = within(args.result, root / "temp/music")
    if result_path.exists():
        raise FileExistsError(f"Result already exists: {result_path}")
    try:
        request_path = within(args.request, root / "temp/music")
        request = json.loads(request_path.read_text(encoding="utf-8-sig"))
        if not isinstance(request, dict):
            raise ValueError("Request must be an object")
        if request_path.parent != result_path.parent or request_path.name != "request.json" or result_path.name != "result.json":
            raise ValueError("request.json and result.json must be in the same job directory")
        if request_path.parent.parent != (root / "temp/music").resolve() or request_path.parent.name != request.get("job_id"):
            raise ValueError("Request/result directory must match the request job_id")
        with contextlib.redirect_stdout(sys.stderr):
            result = generate(request, root)
    except Exception as exc:
        traceback.print_exc(file=sys.stderr)
        result = dict(ok=False, error=type(exc).__name__, message=str(exc))
    result_path.parent.mkdir(parents=True, exist_ok=True)
    with result_path.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
