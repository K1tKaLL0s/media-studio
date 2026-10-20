"""One local IndexTTS-2.5 request per isolated Python 3.10/3.11 process.

Prepared by static source inspection only. Do not use the existing Qwen or
ComfyUI environment. All weights and auxiliary files must already exist locally;
this adapter does not call the upstream download helpers or start a service.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import shutil
import sys
import time
import traceback
import wave


DEFAULT_ROOT = str(Path(__file__).resolve().parents[1])
MODEL_NAME = "IndexTTS-2.5"
MODEL_REVISION = "c39ce5ba981572cb187443877ff559dfb246ce63"
SOURCE_REVISION = "d9e41aac89fd00b3d71497fddb287b7f24613712"
INFER_SHA256 = "b69330053ed603530458bb181029b3abb4c83dc57c811e70837c04141293b56a"
LANGUAGES = {"Chinese": "ZH", "English": "EN", "Japanese": "JA",
             "Spanish": "ES", "Arabic": "AR"}
REQUIRED_FILES = (
    "config.yaml", "gpt.pth", "codec.pth", "s2mel.pth", "feat1.pt", "feat2.pt",
    "wav2vec2bert_stats.pt", "multilingual_zh_ja_yue_char_del.tiktoken",
    "hf_cache/w2v-bert-2.0/config.json",
    "hf_cache/w2v-bert-2.0/preprocessor_config.json",
    "hf_cache/w2v-bert-2.0/model.safetensors",
    "hf_cache/campplus_cn_common.bin",
    "hf_cache/bigvgan/config.json", "hf_cache/bigvgan/bigvgan_generator.pt",
)
CONFIG_FILES = {"gpt_checkpoint": "gpt.pth", "w2v_stat": "wav2vec2bert_stats.pt",
                "s2mel_checkpoint": "s2mel.pth", "emo_matrix": "feat2.pt",
                "spk_matrix": "feat1.pt"}


def within(path: Path, parent: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(parent.resolve()):
        raise ValueError(f"Path must be inside {parent}: {resolved}")
    return resolved


def integer(value, name: str, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ValueError(f"{name} must be an integer between {low} and {high}")
    return value


def validate_request(request: dict, root: Path) -> dict:
    if not isinstance(request, dict):
        raise ValueError("Request must be a JSON object")
    text = request.get("text", "")
    if not isinstance(text, str) or not text.strip() or len(text) > 4000:
        raise ValueError("text must contain 1-4000 characters; split longer scripts")
    language = request.get("language", "Chinese")
    if language not in LANGUAGES:
        raise ValueError(f"Unsupported IndexTTS-2.5 language: {language}")
    duration_factor = request.get("duration_factor", 1.0)
    if (isinstance(duration_factor, bool) or not isinstance(duration_factor, (int, float))
            or not math.isfinite(duration_factor) or not 0.5 <= duration_factor <= 2.0):
        raise ValueError("duration_factor must be a finite number between 0.5 and 2.0")
    job_id = request.get("job_id", "")
    if not isinstance(job_id, str) or not re.fullmatch(r"[0-9a-f]{32}", job_id):
        raise ValueError("job_id must be a 32-character lowercase hexadecimal UUID")
    reference_value = request.get("reference_audio", "")
    if not isinstance(reference_value, str) or not reference_value:
        raise ValueError("IndexTTS voice cloning requires local reference_audio")
    reference = Path(reference_value)
    if not reference.is_absolute() or not reference.is_file():
        raise ValueError("reference_audio must be an existing absolute local file path")
    reference = reference.resolve()
    if not any(reference.is_relative_to((root / name).resolve())
               for name in ("input", "output", "temp")):
        raise ValueError("reference_audio must be in studio input, output or temp")
    output_value = request.get("output", "")
    if not isinstance(output_value, str) or not output_value:
        raise ValueError("output must be an absolute WAV path")
    output = Path(output_value)
    if not output.is_absolute() or output.suffix.lower() != ".wav":
        raise ValueError("output must be an absolute .wav path")
    output = within(output, root / "output" / "speech")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite: {output}")
    model_dir = root / "models" / "tts" / MODEL_NAME
    missing = [name for name in REQUIRED_FILES
               if not (model_dir / name).is_file() or (model_dir / name).stat().st_size == 0]
    if missing:
        raise FileNotFoundError("Local IndexTTS-2.5 files are incomplete: " + ", ".join(missing))
    source_dir = root / "runtime" / MODEL_NAME
    inference = source_dir / "indextts" / "infer_v2_5.py"
    if not inference.is_file() or not (source_dir / "pyproject.toml").is_file():
        raise FileNotFoundError(f"Pinned IndexTTS source is missing: {source_dir}")
    if hashlib.sha256(inference.read_bytes()).hexdigest() != INFER_SHA256:
        raise ValueError(f"IndexTTS inference source differs from pinned commit {SOURCE_REVISION}")
    return dict(text=text.strip(), language=language, lang=LANGUAGES[language],
                reference_audio=str(reference), output=output, job_id=job_id,
                duration_factor=float(duration_factor), model_dir=model_dir,
                source_dir=source_dir,
                seed=integer(request.get("seed", 42), "seed", 0, 2**32 - 1))


def configure_environment(root: Path, options: dict) -> Path:
    work_dir = root / "temp" / "index-tts" / options["job_id"]
    locations = {
        "HF_HOME": root / "cache" / "huggingface",
        "HF_HUB_CACHE": options["model_dir"] / "hf_cache",
        "HUGGINGFACE_HUB_CACHE": options["model_dir"] / "hf_cache",
        "TORCH_HOME": root / "cache" / "torch",
        "MODELSCOPE_CACHE": root / "cache" / "modelscope",
        "NLTK_DATA": root / "cache" / "nltk",
        "NUMBA_CACHE_DIR": root / "cache" / "numba" / "index-tts",
        "MPLCONFIGDIR": root / "cache" / "matplotlib" / "index-tts",
        "XDG_CACHE_HOME": root / "cache" / "index-tts",
        "TEMP": work_dir, "TMP": work_dir, "TMPDIR": work_dir,
    }
    for key, path in locations.items():
        path.mkdir(parents=True, exist_ok=True)
        os.environ[key] = str(path)
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      HF_DATASETS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1",
                      HF_HUB_DISABLE_IMPLICIT_TOKEN="1",
                      TOKENIZERS_PARALLELISM="false", PYTHONDONTWRITEBYTECODE="1")
    # Relative artifacts from third-party libraries stay in this request's N: temp.
    os.chdir(work_dir)
    return work_dir


def validate_model_config(model_dir: Path) -> None:
    import yaml

    config = yaml.safe_load((model_dir / "config.yaml").read_text(encoding="utf-8-sig"))
    if not isinstance(config, dict) or str(config.get("version")) != "2.5":
        raise ValueError("Local config.yaml is not IndexTTS-2.5")
    for key, expected in CONFIG_FILES.items():
        if config.get(key) != expected:
            raise ValueError(f"Unexpected model config path: {key}")
    if config.get("s2mel", {}).get("preprocess_params", {}).get("sr") != 22050:
        raise ValueError("IndexTTS-2.5 output sample rate must be 22050 Hz")


def synthesize(request: dict, root: Path) -> dict:
    if sys.version_info[:2] not in ((3, 10), (3, 11)):
        raise RuntimeError("IndexTTS-2.5 requires a separate Python 3.10 or 3.11 environment")
    options = validate_request(request, root)
    work_dir = configure_environment(root, options)
    validate_model_config(options["model_dir"])
    # Only this dedicated subprocess can import the incompatible IndexTTS stack.
    sys.path.insert(0, str(options["source_dir"]))
    import numpy as np
    import torch
    from indextts.infer_v2_5 import IndexTTS2

    # Upstream overwrites HF_HUB_CACHE during import; all model paths below are
    # explicit local directories, and this restores our absolute cache setting.
    os.environ["HF_HUB_CACHE"] = str(options["model_dir"] / "hf_cache")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable in the separate IndexTTS environment")
    if not torch.cuda.is_bf16_supported():
        raise RuntimeError("This IndexTTS-2.5 profile requires BF16 CUDA support")
    random.seed(options["seed"])
    np.random.seed(options["seed"])
    torch.manual_seed(options["seed"])
    torch.cuda.manual_seed_all(options["seed"])
    import soundfile as sf

    reference, reference_rate = sf.read(options["reference_audio"], dtype="float32", always_2d=True)
    if (reference.size == 0 or not np.isfinite(reference).all()
            or float(np.max(np.abs(reference))) < 1e-5
            or not 8000 <= reference_rate <= 192000):
        raise ValueError("Reference audio is empty, silent, non-finite or has an invalid sample rate")
    start = time.monotonic()
    # Every upstream branch that downloads auxiliaries is avoided by preflight.
    # No QwenEmotion, DeepSpeed, custom CUDA extension, accelerator or compilation.
    model = IndexTTS2(cfg_path=str(options["model_dir"] / "config.yaml"),
                      model_dir=str(options["model_dir"]), device="cuda:0",
                      use_bf16=True, use_cuda_kernel=False, use_deepspeed=False,
                      use_accel=False, use_torch_compile=False, use_qwen_emo=False)
    temporary_audio = work_dir / "generated.wav"
    if temporary_audio.exists():
        raise FileExistsError(f"Refusing to overwrite worker artifact: {temporary_audio}")
    model.infer(spk_audio_prompt=options["reference_audio"], text=options["text"],
                output_path=str(temporary_audio), lang=options["lang"],
                duration_factor=options["duration_factor"], use_emo_text=False,
                use_random=False, stream_return=False, text_normalization=True)
    with wave.open(str(temporary_audio), "rb") as audio:
        frames, sample_rate = audio.getnframes(), audio.getframerate()
        if (audio.getsampwidth() != 2 or audio.getnchannels() != 1
                or audio.getcomptype() != "NONE" or sample_rate != 22050 or frames <= 0):
            raise RuntimeError("IndexTTS must produce nonempty mono 22050 Hz PCM16 WAV")
        raw = audio.readframes(frames)
    if len(raw) != frames * 2:
        raise RuntimeError("IndexTTS output is truncated")
    waveform = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    peak = float(np.max(np.abs(waveform)))
    rms = float(np.sqrt(np.mean(waveform * waveform)))
    if peak < 1e-5 or rms < 1e-7:
        raise RuntimeError("IndexTTS output is silent")
    options["output"].parent.mkdir(parents=True, exist_ok=True)
    with temporary_audio.open("rb") as src, options["output"].open("xb") as dst:
        shutil.copyfileobj(src, dst)
    return dict(ok=True, job_id=options["job_id"], output=str(options["output"]),
                sample_rate=sample_rate, channels=1, frames=frames,
                duration_seconds=frames / sample_rate, peak=peak, rms=rms,
                model=MODEL_NAME, model_revision=MODEL_REVISION,
                source_revision=SOURCE_REVISION, language=options["language"],
                seed=options["seed"], duration_factor=options["duration_factor"],
                elapsed_seconds=round(time.monotonic() - start, 3))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    root = Path(os.environ.get("MEDIA_STUDIO_ROOT", DEFAULT_ROOT)).resolve()
    try:
        result_path = within(args.result, root / "temp" / "index-tts")
        request_path = within(args.request, root / "temp" / "index-tts")
        if result_path.exists():
            raise FileExistsError(f"Result file already exists: {result_path}")
        if request_path.parent != result_path.parent:
            raise ValueError("Request and result must belong to the same job directory")
        request = json.loads(request_path.read_text(encoding="utf-8-sig"))
        if request_path.parent.name != request.get("job_id"):
            raise ValueError("Request job_id does not match its directory")
        with contextlib.redirect_stdout(sys.stderr):
            result = synthesize(request, root)
    except Exception as exc:
        traceback.print_exc(file=sys.stderr)
        result = dict(ok=False, error=type(exc).__name__, message=str(exc))
    try:
        result_path = within(args.result, root / "temp" / "index-tts")
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
