"""IndexTTS-2.5 Comfy bridge; all incompatible model imports stay in a worker."""
from __future__ import annotations

import gc
import json
import math
import os
from pathlib import Path
import uuid

import comfy.model_management as model_management

from .speech import DEFAULT_ROOT, _load_audio, _reference_path, _run_worker, _write_reference


LANGUAGES = ["Chinese", "English", "Japanese", "Spanish", "Arabic"]


def _index_python(root: Path) -> Path:
    """Executable path comes only from process/local configuration, never a graph."""
    value = os.environ.get("MEDIA_STUDIO_INDEX_TTS_PYTHON")
    if value is None:
        config = Path(os.environ.get("MEDIA_STUDIO_RUNTIME_CONFIG", str(root / "config/runtime-paths.json")))
        if config.is_file():
            settings = json.loads(config.read_text(encoding="utf-8-sig"))
            if not isinstance(settings, dict):
                raise ValueError("Runtime paths configuration must be an object")
            value = settings.get("index_tts_python")
    if value is None:
        value = str(root / ("runtime/index-tts-venv/Scripts/python.exe" if os.name == "nt"
                            else "runtime/index-tts-venv/bin/python"))
    if not isinstance(value, str) or not Path(value).is_absolute():
        raise ValueError("index_tts_python must be an absolute executable path")
    python = Path(value).resolve()
    if not python.is_file():
        raise FileNotFoundError(f"Separate IndexTTS environment is not installed: {python}")
    return python


class MediaStudioIndexTTS25:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "text": ("STRING", {"default": "请填写要合成的台词。", "multiline": True}),
            "language": (LANGUAGES, {"default": "Chinese"}),
            "reference_audio_path": ("STRING", {"default": ""}),
            "duration_factor": ("FLOAT", {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.05}),
            "seed": ("INT", {"default": 42, "min": 0, "max": 2**32 - 1}),
            "timeout_seconds": ("INT", {"default": 900, "min": 30, "max": 3600}),
        }, "optional": {"reference_audio": ("AUDIO",)}}

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio",)
    FUNCTION = "generate"
    CATEGORY = "Media Studio"
    DESCRIPTION = "IndexTTS-2.5 reference voice cloning; separate environment required. Prepared, not runtime validated."

    def generate(self, text, language, reference_audio_path, duration_factor, seed,
                 timeout_seconds, reference_audio=None):
        if not isinstance(text, str) or not text.strip() or len(text) > 4000:
            raise ValueError("IndexTTS text must contain 1-4000 characters")
        if language not in LANGUAGES:
            raise ValueError("Unsupported IndexTTS-2.5 language")
        if not isinstance(reference_audio_path, str):
            raise ValueError("reference_audio_path must be a string")
        if reference_audio is None and not reference_audio_path.strip():
            raise ValueError("IndexTTS requires reference AUDIO or reference_audio_path")
        if reference_audio is not None and reference_audio_path.strip():
            raise ValueError("Use one reference AUDIO or path")
        if (isinstance(duration_factor, bool) or not isinstance(duration_factor, (int, float))
                or not math.isfinite(duration_factor) or not 0.5 <= duration_factor <= 2.0):
            raise ValueError("duration_factor must be between 0.5 and 2.0")
        if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed <= 2**32 - 1:
            raise ValueError("seed is outside the supported integer range")
        if (isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, int)
                or not 30 <= timeout_seconds <= 3600):
            raise ValueError("timeout_seconds must be an integer between 30 and 3600")
        root = Path(os.environ.get("MEDIA_STUDIO_ROOT", DEFAULT_ROOT)).resolve()
        python = _index_python(root)
        worker = root / "scripts" / "index_tts_worker.py"
        if not worker.is_file():
            raise FileNotFoundError(f"IndexTTS worker is missing: {worker}")
        model_management.throw_exception_if_processing_interrupted()
        job_id = uuid.uuid4().hex
        work_dir = root / "temp" / "index-tts" / job_id
        output_dir, log_dir = root / "output" / "speech", root / "logs" / "index-tts"
        for directory in (work_dir, output_dir, log_dir):
            directory.mkdir(parents=True, exist_ok=True)
        reference = (_write_reference(reference_audio, work_dir / "reference.wav")
                     if reference_audio is not None else _reference_path(reference_audio_path, root))
        output = output_dir / f"index25_{job_id}.wav"
        request_path, result_path = work_dir / "request.json", work_dir / "result.json"
        log_path = log_dir / f"index25_{job_id}.log"
        request = dict(text=text, language=language, reference_audio=reference,
                       duration_factor=float(duration_factor), seed=seed,
                       output=str(output), job_id=job_id)
        with request_path.open("x", encoding="utf-8") as stream:
            json.dump(request, stream, ensure_ascii=False, indent=2)
        env = os.environ.copy()
        env.update(MEDIA_STUDIO_ROOT=str(root), PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
                   PYTHONDONTWRITEBYTECODE="1", TEMP=str(work_dir), TMP=str(work_dir),
                   TMPDIR=str(work_dir), HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                   HF_HUB_DISABLE_TELEMETRY="1", HF_HUB_DISABLE_IMPLICIT_TOKEN="1")
        model_management.unload_all_models()
        gc.collect()
        model_management.soft_empty_cache(force=True)
        command = [str(python), "-I", "-B", "-u", "-X", "utf8", str(worker),
                   "--request", str(request_path), "--result", str(result_path)]
        try:
            returncode = _run_worker(command, root, env, log_path, timeout_seconds)
            if not result_path.is_file():
                raise RuntimeError(f"IndexTTS worker returned no result (exit {returncode}); log: {log_path}")
            result = json.loads(result_path.read_text(encoding="utf-8"))
            if returncode != 0 or result.get("ok") is not True:
                raise RuntimeError(f"IndexTTS worker failed: {result.get('message', returncode)}; log: {log_path}")
            if result.get("job_id") != job_id or Path(result.get("output", "")).resolve() != output.resolve():
                raise RuntimeError(f"IndexTTS result identity/path mismatch; log: {log_path}")
            return (_load_audio(output, result),)
        except BaseException as exc:
            with log_path.open("a", encoding="utf-8") as stream:
                stream.write(f"\nNode stopped: {type(exc).__name__}: {exc}\n")
            raise


NODE_CLASS_MAPPINGS = {"MediaStudioIndexTTS25": MediaStudioIndexTTS25}
NODE_DISPLAY_NAME_MAPPINGS = {"MediaStudioIndexTTS25": "Media Studio IndexTTS 2.5"}
