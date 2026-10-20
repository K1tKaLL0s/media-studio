"""ACE-Step AUDIO node; all model dependencies remain in ace-venv.

Static integration only: model loading, GPU memory and generation are unverified.
"""
from __future__ import annotations

import gc
import json
import os
from pathlib import Path
import uuid
import wave

import torch
import comfy.model_management as model_management

from .speech import DEFAULT_ROOT, _run_worker


def _ace_python(root: Path) -> Path:
    value = os.environ.get("MEDIA_STUDIO_ACE_PYTHON")
    if not value:
        config = Path(os.environ.get("MEDIA_STUDIO_RUNTIME_CONFIG", str(root / "config/runtime-paths.json")))
        if config.is_file():
            data = json.loads(config.read_text(encoding="utf-8-sig"))
            if not isinstance(data, dict):
                raise ValueError("Runtime paths configuration must be an object")
            value = data.get("ace_python")
    if not value:
        value = str(root / ("runtime/ace-venv/Scripts/python.exe" if os.name == "nt" else "runtime/ace-venv/bin/python"))
    if not isinstance(value, str):
        raise ValueError("ace_python must be an absolute executable path")
    path = Path(value)
    if not path.is_absolute() or not path.is_file():
        raise FileNotFoundError(f"ACE-Step isolated runtime is not prepared: {path}")
    return path.resolve()


def _load_music(path: Path, result: dict) -> dict:
    with wave.open(str(path), "rb") as stream:
        channels, sample_rate, frames = stream.getnchannels(), stream.getframerate(), stream.getnframes()
        if channels not in (1, 2) or stream.getsampwidth() != 2 or stream.getcomptype() != "NONE":
            raise RuntimeError("Music worker output must be mono/stereo PCM16 WAV")
        if frames < 1 or result.get("frames") != frames or result.get("channels") != channels or result.get("sample_rate") != sample_rate:
            raise RuntimeError("Music worker WAV and result metadata disagree")
        raw = bytearray(stream.readframes(frames))
    if len(raw) != frames * channels * 2:
        raise RuntimeError("Music worker WAV is truncated")
    waveform = torch.frombuffer(raw, dtype=torch.int16).reshape(frames, channels).T.to(torch.float32) / 32768.0
    return {"waveform": waveform.unsqueeze(0), "sample_rate": sample_rate}


class MediaStudioMusic:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "caption": ("STRING", {"default": "A quiet acoustic piano instrumental, gentle and unhurried", "multiline": True}),
            "lyrics": ("STRING", {"default": "[Instrumental]", "multiline": True}),
            "instrumental": ("BOOLEAN", {"default": True}),
            "vocal_language": (["unknown", "zh", "en", "ja"], {"default": "unknown"}),
            "duration_seconds": ("INT", {"default": 30, "min": 10, "max": 120}),
            "bpm": ("INT", {"default": 0, "min": 0, "max": 300}),
            "keyscale": ("STRING", {"default": ""}),
            "timesignature": (["", "2", "3", "4", "6"], {"default": ""}),
            "thinking": ("BOOLEAN", {"default": True}),
            "seed": ("INT", {"default": 42, "min": 0, "max": 2**32 - 1}),
            "timeout_seconds": ("INT", {"default": 1800, "min": 60, "max": 7200}),
        }}

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio",)
    FUNCTION = "generate"
    CATEGORY = "Media Studio"
    DESCRIPTION = "ACE-Step 1.5 standard turbo + optional 0.6B LM, local text-to-music. Static integration; runtime unverified."

    def generate(self, caption, lyrics, instrumental, vocal_language, duration_seconds,
                 bpm, keyscale, timesignature, thinking, seed, timeout_seconds):
        if not isinstance(caption, str) or not caption.strip() or len(caption) > 512:
            raise ValueError("caption must contain 1-512 characters")
        if not isinstance(lyrics, str) or len(lyrics) > 4096:
            raise ValueError("lyrics must contain at most 4096 characters")
        if not isinstance(instrumental, bool) or not isinstance(thinking, bool):
            raise ValueError("instrumental and thinking must be booleans")
        if not 60 <= int(timeout_seconds) <= 7200:
            raise ValueError("timeout_seconds must be between 60 and 7200")
        root = Path(os.environ.get("MEDIA_STUDIO_ROOT", DEFAULT_ROOT)).resolve()
        python = _ace_python(root)
        worker = root / "scripts/ace_worker.py"
        if not worker.is_file():
            raise FileNotFoundError(f"ACE-Step worker is missing: {worker}")
        model_management.throw_exception_if_processing_interrupted()
        job_id = uuid.uuid4().hex
        work = root / "temp/music" / job_id
        output_dir, log_dir = root / "output/music", root / "logs/music"
        for directory in (work, output_dir, log_dir):
            directory.mkdir(parents=True, exist_ok=True)
        output = output_dir / f"music_{job_id}.wav"
        request_path, result_path, log_path = work / "request.json", work / "result.json", log_dir / f"music_{job_id}.log"
        request = dict(job_id=job_id, output=str(output), caption=caption, lyrics=lyrics,
                       instrumental=instrumental, vocal_language=vocal_language,
                       duration_seconds=duration_seconds, bpm=bpm, keyscale=keyscale,
                       timesignature=timesignature, thinking=thinking, seed=seed)
        with request_path.open("x", encoding="utf-8") as stream:
            json.dump(request, stream, ensure_ascii=False, indent=2)
        env = os.environ.copy()
        env.update(MEDIA_STUDIO_ROOT=str(root), PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
                   PYTHONDONTWRITEBYTECODE="1", TEMP=str(work), TMP=str(work), TMPDIR=str(work),
                   HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_IMPLICIT_TOKEN="1")
        model_management.unload_all_models()
        gc.collect()
        model_management.soft_empty_cache(force=True)
        command = [str(python), "-I", "-B", "-u", "-X", "utf8", str(worker),
                   "--request", str(request_path), "--result", str(result_path)]
        try:
            returncode = _run_worker(command, root, env, log_path, int(timeout_seconds))
            if not result_path.is_file():
                raise RuntimeError(f"ACE-Step worker returned no result (exit {returncode}); log: {log_path}")
            result = json.loads(result_path.read_text(encoding="utf-8"))
            if returncode != 0 or result.get("ok") is not True:
                raise RuntimeError(f"ACE-Step worker failed: {result.get('message', returncode)}; log: {log_path}")
            if result.get("job_id") != job_id or Path(result.get("output", "")).resolve() != output.resolve():
                raise RuntimeError(f"ACE-Step result identity/path mismatch; log: {log_path}")
            return (_load_music(output, result),)
        except BaseException as exc:
            if log_path.is_file():
                with log_path.open("a", encoding="utf-8") as stream:
                    stream.write(f"\nNode stopped: {type(exc).__name__}: {exc}\n")
            raise


NODE_CLASS_MAPPINGS = {"MediaStudioMusic": MediaStudioMusic}
NODE_DISPLAY_NAME_MAPPINGS = {"MediaStudioMusic": "ACE-Step 1.5 Music (unverified)"}
