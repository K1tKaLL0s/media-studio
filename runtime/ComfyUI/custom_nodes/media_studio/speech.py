"""Media Studio audio node; Qwen dependencies stay in the separate TTS venv."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import gc
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import time
import uuid
import wave

import torch
import folder_paths
import comfy.model_management as model_management


DEFAULT_ROOT = str(Path(__file__).resolve().parents[4])
LANGUAGES = ["Auto", "Chinese", "English", "Japanese", "Korean", "German",
             "French", "Russian", "Portuguese", "Spanish", "Italian"]
SPEAKERS = ["Vivian", "Serena", "Uncle_Fu", "Dylan", "Eric", "Ryan", "Aiden",
            "Ono_Anna", "Sohee"]


def _runtime_option(root, key, default):
    """Read trusted process/local configuration; never workflow inputs."""
    names = {"tts_python": ("MEDIA_STUDIO_TTS_PYTHON",),
             "pv_python": ("MEDIA_STUDIO_PV_PYTHON", "PV_PYTHON"),
             "node": ("MEDIA_STUDIO_NODE", "NODE"),
             "ffmpeg": ("MEDIA_STUDIO_FFMPEG", "FFMPEG"),
             "ffprobe": ("MEDIA_STUDIO_FFPROBE", "FFPROBE"),
             "browser_channel": ("MEDIA_STUDIO_BROWSER_CHANNEL", "BROWSER_CHANNEL"),
             "browser_angle": ("MEDIA_STUDIO_BROWSER_ANGLE", "BROWSER_ANGLE")}
    for name in names[key]:
        if name in os.environ:
            return os.environ[name]
    config = Path(os.environ.get("MEDIA_STUDIO_RUNTIME_CONFIG", str(root / "config/runtime-paths.json")))
    if config.is_file():
        values = json.loads(config.read_text(encoding="utf-8-sig"))
        if not isinstance(values, dict):
            raise ValueError("Runtime paths configuration must be an object")
        if key in values:
            if not isinstance(values[key], str):
                raise ValueError(f"Runtime setting must be a string: {key}")
            return values[key]
    return str(default)


def _runtime_executable(root, key):
    windows = os.name == "nt"
    defaults = {
        "tts_python": root / ("runtime/tts-venv/Scripts/python.exe" if windows else "runtime/tts-venv/bin/python"),
        "pv_python": root / ("runtime/pv-venv/Scripts/python.exe" if windows else "runtime/pv-venv/bin/python"),
        "node": "node",
        "ffmpeg": root / "runtime/ffmpeg/bin/ffmpeg.exe" if windows else "ffmpeg",
        "ffprobe": root / "runtime/ffmpeg/bin/ffprobe.exe" if windows else "ffprobe",
    }
    default = defaults[key]
    if not windows and key in {"tts_python", "pv_python"} and not Path(default).is_file():
        default = "python3"
    value = _runtime_option(root, key, default)
    path = Path(value).expanduser()
    if not path.is_absolute():
        if path.name != value:
            raise ValueError(f"Runtime path must be absolute or a PATH command: {key}")
        found = shutil.which(value)
        if not found:
            raise FileNotFoundError(f"Runtime command is missing: {key}={value}")
        path = Path(found)
    if not path.is_file():
        raise FileNotFoundError(f"Runtime executable is missing: {key}={path}")
    return path.resolve()


class _WindowsJob:
    """A job owned by this request; closing it reaps only its assigned processes."""
    def __init__(self):
        class BasicLimits(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong),
                        ("PerJobUserTimeLimit", ctypes.c_longlong),
                        ("LimitFlags", wintypes.DWORD),
                        ("MinimumWorkingSetSize", ctypes.c_size_t),
                        ("MaximumWorkingSetSize", ctypes.c_size_t),
                        ("ActiveProcessLimit", wintypes.DWORD),
                        ("Affinity", ctypes.c_size_t),
                        ("PriorityClass", wintypes.DWORD),
                        ("SchedulingClass", wintypes.DWORD)]

        class IOCounters(ctypes.Structure):
            _fields_ = [(name, ctypes.c_ulonglong) for name in (
                "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

        class ExtendedLimits(ctypes.Structure):
            _fields_ = [("BasicLimitInformation", BasicLimits),
                        ("IoInfo", IOCounters),
                        ("ProcessMemoryLimit", ctypes.c_size_t),
                        ("JobMemoryLimit", ctypes.c_size_t),
                        ("PeakProcessMemoryUsed", ctypes.c_size_t),
                        ("PeakJobMemoryUsed", ctypes.c_size_t)]

        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        self.api.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        self.api.CreateJobObjectW.restype = wintypes.HANDLE
        self.api.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int,
                                                     ctypes.c_void_p, wintypes.DWORD]
        self.api.SetInformationJobObject.restype = wintypes.BOOL
        self.api.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        self.api.AssignProcessToJobObject.restype = wintypes.BOOL
        self.api.CloseHandle.argtypes = [wintypes.HANDLE]
        self.api.CloseHandle.restype = wintypes.BOOL
        self.handle = self.api.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = ExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = 0x2000  # KILL_ON_JOB_CLOSE
        if not self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            error = ctypes.get_last_error()
            self.close()
            raise ctypes.WinError(error)

    def assign(self, process):
        if not self.api.AssignProcessToJobObject(self.handle, wintypes.HANDLE(process._handle)):
            raise ctypes.WinError(ctypes.get_last_error())

    def close(self):
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle = None


def _run_worker(command: list[str], root: Path, env: dict, log_path: Path,
                timeout_seconds: int) -> int:
    process = None
    owned_job = _WindowsJob() if os.name == "nt" else None
    try:
        with log_path.open("xb") as log:
            process = subprocess.Popen(
                command, cwd=str(root), env=env, stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                start_new_session=os.name != "nt",
            )
            if owned_job is not None:
                try:
                    owned_job.assign(process)
                except BaseException:
                    process.kill()
                    process.wait(timeout=10)
                    raise
            deadline = time.monotonic() + timeout_seconds
            while process.poll() is None:
                model_management.throw_exception_if_processing_interrupted()
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"Speech worker exceeded {timeout_seconds}s; log: {log_path}")
                time.sleep(0.2)
            model_management.throw_exception_if_processing_interrupted()
            return process.returncode
    finally:
        # Executed for Comfy's BaseException cancellation as well as errors.
        if owned_job is not None:
            owned_job.close()
        elif process is not None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if process is not None and process.poll() is None:
            process.wait(timeout=10)


def _reference_path(value: str, root: Path) -> str:
    if not value.strip():
        return ""
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = Path(folder_paths.get_input_directory()) / candidate
    candidate = candidate.resolve()
    if not candidate.is_file():
        raise ValueError(f"Reference audio does not exist: {candidate}")
    if not any(candidate.is_relative_to((root / subdir).resolve())
               for subdir in ("input", "output")):
        raise ValueError("Reference audio must be inside the studio input or output directory")
    return str(candidate)


def _write_reference(audio: dict, path: Path) -> str:
    waveform = audio["waveform"].detach().to(device="cpu", dtype=torch.float32)
    if waveform.ndim != 3 or waveform.shape[0] != 1 or waveform.shape[1] not in (1, 2):
        raise ValueError("Reference AUDIO must have one batch and one or two channels")
    waveform = waveform[0].mean(dim=0)
    if waveform.numel() == 0 or not bool(torch.isfinite(waveform).all()):
        raise ValueError("Reference AUDIO is empty or contains non-finite samples")
    sample_rate = int(audio["sample_rate"])
    if not 8000 <= sample_rate <= 192000:
        raise ValueError("Invalid reference AUDIO sample rate")
    pcm = (waveform.clamp(-1.0, 1.0) * 32767).round().to(torch.int16).numpy().astype("<i2")
    with path.open("xb") as stream:
        with wave.open(stream, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(pcm.tobytes())
    return str(path)


def _load_audio(path: Path, result: dict) -> dict:
    with wave.open(str(path), "rb") as wav:
        if wav.getsampwidth() != 2 or wav.getnchannels() != 1 or wav.getcomptype() != "NONE":
            raise RuntimeError("Worker output must be uncompressed mono PCM16 WAV")
        frames, sample_rate = wav.getnframes(), wav.getframerate()
        if frames <= 0 or frames != result.get("frames") or sample_rate != result.get("sample_rate"):
            raise RuntimeError("Worker output does not match its JSON result")
        raw = bytearray(wav.readframes(frames))
    if len(raw) != frames * 2:
        raise RuntimeError("Worker output is truncated")
    waveform = torch.frombuffer(raw, dtype=torch.int16).to(torch.float32) / 32768.0
    if float(waveform.abs().max()) < 1e-5:
        raise RuntimeError("Worker output is silent")
    return {"waveform": waveform.reshape(1, 1, -1), "sample_rate": sample_rate}


class MediaStudioSpeech:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mode": (["preset", "clone"], {"default": "preset"}),
                "text": ("STRING", {"default": "你好，欢迎来到媒体创作工作台。", "multiline": True}),
                "language": (LANGUAGES, {"default": "Chinese"}),
                "speaker": (SPEAKERS, {"default": "Vivian"}),
                "instruct": ("STRING", {"default": "", "multiline": True}),
                "reference_audio_path": ("STRING", {"default": ""}),
                "reference_text": ("STRING", {"default": "", "multiline": True}),
                "seed": ("INT", {"default": 42, "min": 0, "max": 2**32 - 1}),
                "max_new_tokens": ("INT", {"default": 1024, "min": 64, "max": 4096, "step": 64}),
                "timeout_seconds": ("INT", {"default": 900, "min": 30, "max": 3600}),
            },
            "optional": {"reference_audio": ("AUDIO",)},
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio",)
    FUNCTION = "generate"
    CATEGORY = "Media Studio"
    DESCRIPTION = "Local Qwen speech: 1.7B CustomVoice presets/style, or 0.6B Base cloning."

    def generate(self, mode, text, language, speaker, instruct, reference_audio_path,
                 reference_text, seed, max_new_tokens, timeout_seconds, reference_audio=None):
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Speech text is empty")
        if mode not in ("preset", "clone"):
            raise ValueError("Speech mode must be preset or clone")
        if mode == "clone" and instruct.strip():
            raise ValueError("Clone mode does not support style instructions; leave instruct empty")
        if mode == "clone" and not reference_text.strip():
            raise ValueError("Clone mode requires the exact reference transcript")
        if mode == "clone" and reference_audio is None and not reference_audio_path.strip():
            raise ValueError("Clone mode requires reference AUDIO or reference_audio_path")
        if mode == "clone" and reference_audio is not None and reference_audio_path.strip():
            raise ValueError("Use either reference AUDIO or reference_audio_path, not both")
        if not 30 <= int(timeout_seconds) <= 3600:
            raise ValueError("timeout_seconds must be between 30 and 3600")
        root = Path(os.environ.get("MEDIA_STUDIO_ROOT", DEFAULT_ROOT)).resolve()
        python = _runtime_executable(root, "tts_python")
        worker = root / "scripts" / "tts_worker.py"
        for file in (python, worker):
            if not file.is_file():
                raise FileNotFoundError(f"Speech runtime is not prepared: {file}")
        model_management.throw_exception_if_processing_interrupted()
        job_id = uuid.uuid4().hex
        work_dir = root / "temp" / "tts" / job_id
        output_dir = root / "output" / "speech"
        log_dir = root / "logs" / "tts"
        for directory in (work_dir, output_dir, log_dir):
            directory.mkdir(parents=True, exist_ok=True)
        reference = ""
        if mode == "clone":
            reference = (_write_reference(reference_audio, work_dir / "reference.wav")
                         if reference_audio is not None else _reference_path(reference_audio_path, root))
        output = output_dir / f"speech_{job_id}.wav"
        request_path, result_path = work_dir / "request.json", work_dir / "result.json"
        log_path = log_dir / f"speech_{job_id}.log"
        request = dict(mode=mode, text=text, language=language, speaker=speaker,
                       instruct=instruct, reference_audio=reference, reference_text=reference_text,
                       seed=int(seed), max_new_tokens=int(max_new_tokens),
                       output=str(output), job_id=job_id)
        request_path.write_text(json.dumps(request, ensure_ascii=False, indent=2), encoding="utf-8")
        env = os.environ.copy()
        env.update(MEDIA_STUDIO_ROOT=str(root), PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
                   PYTHONDONTWRITEBYTECODE="1", TEMP=str(work_dir), TMP=str(work_dir),
                   TMPDIR=str(work_dir), HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
        model_management.unload_all_models()
        gc.collect()
        model_management.soft_empty_cache(force=True)
        command = [str(python), "-I", "-B", "-u", "-X", "utf8", str(worker),
                   "--request", str(request_path), "--result", str(result_path)]
        try:
            returncode = _run_worker(command, root, env, log_path, int(timeout_seconds))
            if not result_path.is_file():
                raise RuntimeError(f"Speech worker returned no result (exit {returncode}); log: {log_path}")
            result = json.loads(result_path.read_text(encoding="utf-8"))
            if returncode != 0 or result.get("ok") is not True:
                raise RuntimeError(f"Speech worker failed: {result.get('message', returncode)}; log: {log_path}")
            if result.get("job_id") != job_id or Path(result.get("output", "")).resolve() != output.resolve():
                raise RuntimeError(f"Speech result identity/path mismatch; log: {log_path}")
            return (_load_audio(output, result),)
        except BaseException as exc:
            with log_path.open("a", encoding="utf-8") as log:
                log.write(f"\nNode stopped: {type(exc).__name__}: {exc}\n")
            raise


NODE_CLASS_MAPPINGS = {"MediaStudioSpeech": MediaStudioSpeech}
NODE_DISPLAY_NAME_MAPPINGS = {"MediaStudioSpeech": "Media Studio Speech"}
