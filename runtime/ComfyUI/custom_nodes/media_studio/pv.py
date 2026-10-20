"""Render a prepared local MV project through its existing renderer."""
import json
import os
from pathlib import Path
import re
import shutil
import uuid

import folder_paths
import comfy.model_management as model_management
from comfy_api.latest import InputImpl, io, ui
from .speech import DEFAULT_ROOT, _run_worker, _runtime_executable, _runtime_option


def studio_root():
    configured = os.environ.get("MEDIA_STUDIO_ROOT")
    return Path(configured or DEFAULT_ROOT).resolve()


def child_environment(root):
    env = os.environ.copy()
    directories = {
        "TEMP": "temp", "TMP": "temp", "TMPDIR": "temp",
        "PIP_CACHE_DIR": "cache/pip", "npm_config_cache": "cache/npm",
        "PLAYWRIGHT_BROWSERS_PATH": "cache/playwright",
        "MPLCONFIGDIR": "cache/matplotlib", "NUMBA_CACHE_DIR": "cache/numba",
        "PYTHONPYCACHEPREFIX": "cache/pycache", "TORCH_HOME": "cache/torch",
        "CUDA_CACHE_PATH": "cache/cuda", "TORCHINDUCTOR_CACHE_DIR": "cache/inductor",
    }
    for name, relative in directories.items():
        path = root / relative
        path.mkdir(parents=True, exist_ok=True)
        env[name] = str(path)
    env["PYTHON"] = str(_runtime_executable(root, "pv_python"))
    env["FFMPEG"] = str(_runtime_executable(root, "ffmpeg"))
    env["FFPROBE"] = str(_runtime_executable(root, "ffprobe"))
    env["BROWSER_CHANNEL"] = _runtime_option(root, "browser_channel", "msedge" if os.name == "nt" else "chrome")
    env["BROWSER_ANGLE"] = _runtime_option(root, "browser_angle", "d3d11" if os.name == "nt" else "")
    env["COMFY_WHERE"] = "local"
    env["PATH"] = os.pathsep.join([
        str(Path(env["FFMPEG"]).parent), str(Path(env["PYTHON"]).parent),
        env.get("PATH", ""),
    ])
    return env


class MediaStudioMV(io.ComfyNode):
    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        # Projects are edited outside the graph; every explicit run must render them again.
        return float("nan")

    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="MediaStudioMV", display_name="PV / MV Render",
            category="Media Studio", is_output_node=True,
            inputs=[
                io.String.Input("project_name", default="pv-demo"),
                io.Combo.Input("quality", options=["preview", "final"]),
                io.String.Input("filename_prefix", default="mv"),
                io.Int.Input("timeout_seconds", default=3600, min=60, max=14400),
            ],
            outputs=[io.Video.Output("video")],
        )

    @classmethod
    def execute(cls, project_name, quality, filename_prefix, timeout_seconds):
        root = studio_root()
        projects = (root / "projects").resolve()
        project = (projects / project_name).resolve()
        if not project.is_relative_to(projects) or project == projects:
            raise ValueError("Choose a project inside Media Studio's projects directory.")
        if quality not in ("preview", "final"):
            raise ValueError("Quality must be preview or final.")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,40}", filename_prefix):
            raise ValueError("Use a short filename prefix with letters, digits, underscores or hyphens.")
        renderer = project / "tools/render_final.mjs"
        if not renderer.is_file() or not (project / "analysis/audio.json").is_file():
            raise ValueError("Prepare and analyze this MV project before rendering it.")
        node = _runtime_executable(root, "node")
        env = child_environment(root)
        for executable in (node, Path(env["PYTHON"]), Path(env["FFMPEG"]), Path(env["FFPROBE"])):
            if not executable.is_file():
                raise FileNotFoundError(f"Required executable is missing: {executable}")
        model_management.unload_all_models()
        model_management.soft_empty_cache()
        job_id = uuid.uuid4().hex[:12]
        name = f"{filename_prefix}_{job_id}"
        logs = root / "logs"
        logs.mkdir(exist_ok=True)
        log_path = logs / f"mv-{job_id}.log"
        command = [str(node), str(renderer), "--name", name, "--workers", "1"]
        if quality == "preview":
            command.append("--preview")
        returncode = _run_worker(command, project, env, log_path, int(timeout_seconds))
        if returncode:
            raise RuntimeError(f"MV renderer exited with code {returncode}. See {log_path}")
        source = project / "render" / f"{name}.mp4"
        if not source.is_file() or source.stat().st_size == 0:
            raise RuntimeError(f"Renderer produced no complete video. See {log_path}")
        destination_dir = Path(folder_paths.get_output_directory()) / "mv"
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / source.name
        try:
            os.link(source, destination)
        except OSError:
            shutil.copy2(source, destination)
        (logs / f"mv-{job_id}.json").write_text(json.dumps({
            "job_id": job_id, "project": str(project), "quality": quality,
            "output": str(destination), "log": str(log_path),
        }, indent=2), encoding="utf-8")
        video = InputImpl.VideoFromFile(str(destination))
        preview = ui.PreviewVideo([ui.SavedResult(destination.name, "mv", io.FolderType.output)])
        return io.NodeOutput(video, ui=preview)
