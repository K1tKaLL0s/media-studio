"""VoiceDesign node. Its Qwen dependency stays in the existing isolated TTS venv.

Static integration only: loading, generation, audio quality and 8GB fit unverified.
"""
from __future__ import annotations

import gc
import json
import os
from pathlib import Path
import uuid

import comfy.model_management as model_management

from .speech import (DEFAULT_ROOT, LANGUAGES, _load_audio, _run_worker,
                     _runtime_executable)


class MediaStudioVoiceDesign:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "text": ("STRING", {"default": "", "multiline": True}),
            "instruct": ("STRING", {"default": "A calm adult voice, clear articulation and a gentle pace.", "multiline": True}),
            "language": (LANGUAGES, {"default": "Chinese"}),
            "seed": ("INT", {"default": 42, "min": 0, "max": 2**32 - 1}),
            "max_new_tokens": ("INT", {"default": 1024, "min": 64, "max": 4096, "step": 64}),
            "timeout_seconds": ("INT", {"default": 900, "min": 30, "max": 3600}),
        }}

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio",)
    FUNCTION = "generate"
    CATEGORY = "Media Studio"
    DESCRIPTION = "Qwen3-TTS 1.7B VoiceDesign: describe a voice without choosing a preset. Static integration; not runtime validated."

    def generate(self, text, instruct, language, seed, max_new_tokens, timeout_seconds):
        if not isinstance(text, str) or not text.strip() or len(text) > 4000:
            raise ValueError("VoiceDesign text must contain 1-4000 characters")
        if not isinstance(instruct, str) or not instruct.strip() or len(instruct) > 2000:
            raise ValueError("VoiceDesign instruct must contain 1-2000 characters")
        if language not in LANGUAGES:
            raise ValueError("Unsupported language")
        if not 30 <= int(timeout_seconds) <= 3600:
            raise ValueError("timeout_seconds must be between 30 and 3600")
        root = Path(os.environ.get("MEDIA_STUDIO_ROOT", DEFAULT_ROOT)).resolve()
        python = _runtime_executable(root, "tts_python")
        worker = root / "scripts" / "voice_design_worker.py"
        for file in (worker, root / "scripts" / "tts_worker.py"):
            if not file.is_file():
                raise FileNotFoundError(f"VoiceDesign runtime is not prepared: {file}")
        model_management.throw_exception_if_processing_interrupted()
        job_id = uuid.uuid4().hex
        work_dir = root / "temp" / "tts" / job_id
        output_dir = root / "output" / "speech"
        log_dir = root / "logs" / "tts"
        for directory in (work_dir, output_dir, log_dir):
            directory.mkdir(parents=True, exist_ok=True)
        output = output_dir / f"voice_design_{job_id}.wav"
        request_path, result_path = work_dir / "request.json", work_dir / "result.json"
        log_path = log_dir / f"voice_design_{job_id}.log"
        request = dict(mode="voice_design", text=text, instruct=instruct, language=language,
                       seed=int(seed), max_new_tokens=int(max_new_tokens),
                       output=str(output), job_id=job_id)
        with request_path.open("x", encoding="utf-8") as stream:
            json.dump(request, stream, ensure_ascii=False, indent=2)
        env = os.environ.copy()
        env.update(MEDIA_STUDIO_ROOT=str(root), PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
                   PYTHONDONTWRITEBYTECODE="1", TEMP=str(work_dir), TMP=str(work_dir),
                   TMPDIR=str(work_dir), HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                   HF_HUB_DISABLE_IMPLICIT_TOKEN="1")
        model_management.unload_all_models()
        gc.collect()
        model_management.soft_empty_cache(force=True)
        command = [str(python), "-I", "-B", "-u", "-X", "utf8", str(worker),
                   "--request", str(request_path), "--result", str(result_path)]
        try:
            returncode = _run_worker(command, root, env, log_path, int(timeout_seconds))
            if not result_path.is_file():
                raise RuntimeError(f"VoiceDesign worker returned no result (exit {returncode}); log: {log_path}")
            result = json.loads(result_path.read_text(encoding="utf-8"))
            if returncode != 0 or result.get("ok") is not True:
                raise RuntimeError(f"VoiceDesign worker failed: {result.get('message', returncode)}; log: {log_path}")
            if result.get("job_id") != job_id or Path(result.get("output", "")).resolve() != output.resolve():
                raise RuntimeError(f"VoiceDesign result identity/path mismatch; log: {log_path}")
            return (_load_audio(output, result),)
        except BaseException as exc:
            with log_path.open("a", encoding="utf-8") as log:
                log.write(f"\nNode stopped: {type(exc).__name__}: {exc}\n")
            raise


NODE_CLASS_MAPPINGS = {"MediaStudioVoiceDesign": MediaStudioVoiceDesign}
NODE_DISPLAY_NAME_MAPPINGS = {"MediaStudioVoiceDesign": "Qwen VoiceDesign (unverified)"}
