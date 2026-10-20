"""Loopback-only daily Media Studio API; no torch or Comfy imports."""
from __future__ import annotations

import argparse
import asyncio
from collections import OrderedDict, deque
from copy import deepcopy
import ctypes
import hashlib
import ipaddress
import json
import logging
import mimetypes
import os
from pathlib import Path, PurePosixPath
import re
import time
from urllib.parse import quote, urlsplit
import uuid

import aiohttp
from aiohttp import web
import psutil

LOG = logging.getLogger("media-studio-gateway")
MIB, GIB = 1024 ** 2, 1024 ** 3
UPLOAD_LIMIT = 32 * MIB
MEDIA = {".png": ("image", "image/png"), ".jpg": ("image", "image/jpeg"),
         ".jpeg": ("image", "image/jpeg"), ".webp": ("image", "image/webp"),
         ".wav": ("audio", "audio/wav"), ".flac": ("audio", "audio/flac"),
         ".mp4": ("video", "video/mp4")}
LANGUAGES = ["Auto", "Chinese", "English", "Japanese", "Korean", "German",
             "French", "Russian", "Portuguese", "Spanish", "Italian"]
SPEAKERS = ["Vivian", "Serena", "Uncle_Fu", "Dylan", "Eric", "Ryan", "Aiden", "Ono_Anna", "Sohee"]
GATEWAY_KEY = web.AppKey("gateway", object)


class ApiError(Exception):
    def __init__(self, code, message, status=400, details=None):
        self.code, self.message, self.status, self.details = code, message, status, details
        super().__init__(message)


def text(zh, en):
    return {"zh": zh, "en": en}


def field(name, kind, zh, en, default=None, lo=None, hi=None, step=None,
          options=None, required=True, description=None):
    return {"name": name, "type": kind, "default": default, "min": lo, "max": hi,
            "step": step, "options": options or [], "labels": text(zh, en),
            "description": description or text(zh, en), "required": required}


def definitions():
    seed = lambda: field("seed", "integer", "种子", "Seed", 42, 0, 2**32-1, 1)
    steps = lambda n=20: field("steps", "integer", "采样步数", "Steps", n, 1, 100, 1)
    prompt = lambda: field("prompt", "textarea", "画面／动作描述", "Prompt", "", description=text("描述主体、构图、光线或一个动作。", "Describe the subject, composition, lighting or one action."))
    negative = lambda: field("negative_prompt", "textarea", "负提示词", "Negative prompt", "", required=False)
    dimensions = lambda video=False: [field("width", "integer", "宽度", "Width", 512, 128, 2048 if not video else 1280, 16),
                                     field("height", "integer", "高度", "Height", 288 if video else 512, 128, 2048 if not video else 1280, 16)]
    language = lambda: field("language", "select", "语言", "Language", "Chinese", options=LANGUAGES)
    tokens = lambda: field("max_new_tokens", "integer", "生成上限", "Token limit", 1024, 64, 4096, 64)
    speech = [field("text", "textarea", "要说的台词", "Speech text", ""), language(),
              field("speaker", "select", "音色", "Voice", "Vivian", options=SPEAKERS),
              field("instruct", "textarea", "说话风格", "Speaking style", "", required=False), seed(), tokens()]
    clone = [field("audio", "audio", "参考音频", "Reference audio"), field("text", "textarea", "新台词", "New speech text", ""),
             language(), field("reference_text", "textarea", "参考音频准确原文", "Exact reference transcript", ""), seed(), tokens()]
    video = lambda: [prompt(), negative(), *dimensions(True), field("length", "integer", "帧数（4n+1，24fps）", "Frames (4n+1 at 24fps)", 17, 5, 121, 4), seed(), steps()]
    design = [field("text", "textarea", "要说的台词", "Speech text", ""),
              field("instruct", "textarea", "音色描述", "Voice description", "A calm adult voice, clear articulation and a gentle pace."), language(), seed(), tokens()]
    index25 = [field("audio", "audio", "参考声音", "Reference voice"),
               field("text", "textarea", "新台词", "New speech text", ""),
               field("language", "select", "语言", "Language", "Chinese", options=["Chinese", "English", "Japanese", "Spanish", "Arabic"]),
               field("duration_factor", "number", "时长系数", "Duration factor", 1.0, 0.5, 2.0), seed()]
    yesno = {"true": text("是", "Yes"), "false": text("否", "No")}
    music = [field("caption", "textarea", "音乐描述", "Music description", "A quiet acoustic piano instrumental, gentle and unhurried"),
             field("lyrics", "textarea", "歌词", "Lyrics", "[Instrumental]", required=False),
             field("instrumental", "select", "纯音乐", "Instrumental", "true", options=["true", "false"]),
             field("vocal_language", "select", "演唱语言", "Vocal language", "unknown", options=["unknown", "zh", "en", "ja"]),
             field("duration_seconds", "integer", "时长（秒）", "Duration (seconds)", 30, 10, 120, 1),
             field("bpm", "integer", "速度（0为自动；否则30–300）", "BPM (0=auto; otherwise 30–300)", 0, 0, 300, 1),
             field("keyscale", "text", "调性（留空自动）", "Key / scale (empty=auto)", "", required=False),
             field("timesignature", "select", "拍号（留空自动）", "Time signature (empty=auto)", "", options=["", "2", "3", "4", "6"], required=False),
             field("thinking", "select", "启用0.6B音乐LM", "Use 0.6B music LM", "true", options=["true", "false"]), seed()]
    for setting in music:
        if setting["name"] in {"instrumental", "thinking"}: setting["option_labels"] = yesno
    return {
        "voice_design": (text("音色设计", "Voice design"), text("描述音色；静态接入，未运行验证。", "Describe a voice; statically integrated, not run."), "audio", design, {k: [("1", k)] for k in ["text", "instruct", "language", "seed", "max_new_tokens"]}),
        "speech_index25": (text("Index参考声音", "Index reference voice"), text("IndexTTS 2.5参考声音与时长控制；静态接入，未运行验证。", "IndexTTS 2.5 reference voice and duration control; statically integrated, not run."), "audio", index25, {"audio": [("1", "audio")], **{k: [("2", k)] for k in ["text", "language", "duration_factor", "seed"]}}),
        "music": (text("音乐生成", "Music generation"), text("ACE-Step 1.5 turbo＋0.6B LM；单段10–120秒，静态接入，未运行验证。", "ACE-Step 1.5 turbo + 0.6B LM; 10–120 seconds per segment, statically integrated, not run."), "audio", music, {k: [("1", k)] for k in ["caption", "lyrics", "instrumental", "vocal_language", "duration_seconds", "bpm", "keyscale", "timesignature", "thinking", "seed"]}),
        "speech": (text("预置声音", "Preset speech"), text("本机预置音色配音；未代替实际试听。", "Local preset speech; listening review remains necessary."), "audio", speech, {"text": [("1", "text")], "language": [("1", "language")], "speaker": [("1", "speaker")], "instruct": [("1", "instruct")], "seed": [("1", "seed")], "max_new_tokens": [("1", "max_new_tokens")]}),
        "speech_clone": (text("参考声音克隆", "Reference voice"), text("提供录音及准确原文，生成新台词。", "Supply a recording and exact transcript for new speech."), "audio", clone, {"audio": [("1", "audio")], **{k: [("2", k)] for k in ["text", "language", "reference_text", "seed", "max_new_tokens"]}}),
        "anime": (text("动漫插画", "Anime illustration"), text("Anima Turbo；检查签名、手与角色细节。", "Anima Turbo; review signatures, hands and character details."), "image", [prompt(), negative(), *dimensions(), seed(), steps(10)], {"prompt": [("4", "text")], "negative_prompt": [("5", "text")], "width": [("6", "width")], "height": [("6", "height")], "seed": [("7", "seed")], "steps": [("7", "steps")]}),
        "image": (text("通用图片", "General image"), text("FLUX Klein，默认512×512、4步。", "FLUX Klein, fixed 512×512 and initially 4 steps."), "image", [prompt(), seed(), steps(4)], {"prompt": [("4", "text")], "seed": [("7", "noise_seed")], "steps": [("9", "steps")]}),
        "image-edit": (text("参考图编辑", "Reference edit"), text("一次改一件事，保留原图并排检查。", "Change one thing; compare with the original."), "image", [prompt(), field("megapixels", "number", "参考图百万像素", "Reference megapixels", 0.25, 0.06, 1.0, None), seed(), steps(4), field("image", "image", "参考图片", "Reference image")], {"prompt": [("4", "text")], "megapixels": [("7", "megapixels")], "seed": [("13", "noise_seed")], "steps": [("15", "steps")], "image": [("6", "image")]}),
        "video": (text("文生视频（实验）", "Text to video (experimental)"), text("默认1280×704、17帧起步；长镜头耗时较高，画面需实审。", "Default 1280×704, initially 17 frames; longer shots are slow and require visual review."), "video", video(), {"prompt": [("4", "text")], "negative_prompt": [("5", "text")], "width": [("6", "width")], "height": [("6", "height")], "length": [("6", "length")], "seed": [("8", "seed")], "steps": [("8", "steps")]}),
        "video-i2v": (text("图生视频（实验）", "Image to video (experimental)"), text("默认704×1280；起始图按画幅居中裁切，检查角色和动作。", "Default 704×1280; the starting image is center-cropped to fit. Review identity and motion."), "video", [*video(), field("image", "image", "起始图片", "Starting image")], {"prompt": [("4", "text")], "negative_prompt": [("5", "text")], "width": [("6", "width")], "height": [("6", "height")], "length": [("6", "length")], "seed": [("8", "seed")], "steps": [("8", "steps")], "image": [("12", "image")]}),
        "mv": (text("歌词PV／MV", "Lyric PV / MV"), text("只渲染已准备并分析好的工程。", "Render an already prepared and analyzed project."), "video", [field("project_name", "select", "项目", "Project", "pv-demo", options=["pv-demo"]), field("quality", "select", "质量", "Quality", "preview", options=["preview", "final"]), field("filename_prefix", "text", "输出前缀", "Output prefix", "daily_mv")], {k: [("1", k)] for k in ["project_name", "quality", "filename_prefix"]}),
    }


def loopback_url(value):
    p = urlsplit(value)
    if p.scheme != "http" or p.hostname not in {"127.0.0.1", "localhost", "::1"} or p.username or p.password or p.path not in ("", "/") or p.query or p.fragment:
        raise ValueError("Backend must be a bare HTTP loopback URL")
    if not p.port or not 1 <= p.port <= 65535:
        raise ValueError("Backend must have an explicit valid port")
    return value.rstrip("/")


def loopback_host(value):
    if not isinstance(value, str) or not re.fullmatch(r"(?:127\.0\.0\.1|localhost|\[::1\]):[0-9]{1,5}", value):
        raise ValueError("Extra Host must be a loopback name and port")
    loopback_url("http://"+value)
    return value


class Settings:
    def __init__(self, root, config=None):
        self.root = Path(root).resolve()
        data = config or {}
        self.host = data.get("host", "127.0.0.1")
        self.port = data.get("port", 8190)
        if self.host != "127.0.0.1" or type(self.port) is not int or not 1 <= self.port <= 65535:
            raise ValueError("Gateway binding must be 127.0.0.1 with a valid port")
        self.backend = loopback_url(data.get("backend_url", "http://127.0.0.1:8188"))
        self.native_client_url = loopback_url(data.get("native_client_url", self.backend))
        self.origins = {f"http://127.0.0.1:{self.port}", f"http://localhost:{self.port}"}
        for origin in data.get("allowed_origins", []):
            p = urlsplit(origin)
            if p.scheme != "https" or not p.netloc or p.path or p.query or p.fragment or p.username or p.password or "*" in origin:
                raise ValueError("Allowed origins must be exact HTTPS origins")
            self.origins.add(origin)
        self.hosts = {f"127.0.0.1:{self.port}", f"localhost:{self.port}"}
        for host in data.get("additional_hosts", []):
            self.hosts.add(loopback_host(host))
        for origin in data.get("additional_loopback_origins", []):
            checked = loopback_url(origin)
            if checked != origin:
                raise ValueError("Loopback origins must have no trailing slash")
            self.origins.add(checked)
        self.idle_seconds = 30


def media_path(root, area, relative, must_exist=True):
    if area not in {"input", "output"} or not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative or "\x00" in relative:
        raise ApiError("INVALID_VALUE", "Invalid media path")
    logical = PurePosixPath(relative)
    if logical.is_absolute() or any(p in {"..", "."} or p.startswith(".") for p in logical.parts):
        raise ApiError("INVALID_VALUE", "Media path escapes its allowed directory")
    base = (root / area).resolve()
    p = (base / Path(*logical.parts)).resolve()
    if not p.is_relative_to(base) or p.suffix.lower() not in MEDIA:
        raise ApiError("INVALID_VALUE", "Unsupported or escaping media path")
    if must_exist and not p.is_file():
        raise ApiError("MISSING_ASSET", "Media file does not exist", 404)
    return p


def asset_url(area, relative):
    return "/api/asset?type=" + area + "&path=" + quote(relative, safe="")


def file_signature(data):
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return ".wav"
    if data.startswith(b"fLaC"):
        return ".flac"
    raise ApiError("UNSUPPORTED_MEDIA", "Allowed files: PNG, JPEG, WebP, WAV or FLAC", 415)


class Resources:
    def __init__(self, settings):
        self.settings = settings

    def sample(self):
        vm = psutil.virtual_memory()
        result = dict(available_bytes=int(vm.available), commit_bytes=None, commit_limit_bytes=None,
                      commit_headroom_bytes=None, commit_percent=None, comfy_private_bytes=None,
                      comfy_pid=None, comfy_created=None, advisory=os.name != "nt", source="psutil")
        try:
            if os.name == "nt":
                class Perf(ctypes.Structure):
                    _fields_ = [("cb", ctypes.c_ulong), *[(n, ctypes.c_size_t) for n in ["CommitTotal", "CommitLimit", "CommitPeak", "PhysicalTotal", "PhysicalAvailable", "SystemCache", "KernelTotal", "KernelPaged", "KernelNonpaged", "PageSize"]], ("HandleCount", ctypes.c_ulong), ("ProcessCount", ctypes.c_ulong), ("ThreadCount", ctypes.c_ulong)]
                info = Perf(); info.cb = ctypes.sizeof(info)
                api = ctypes.WinDLL("psapi", use_last_error=True)
                if not api.GetPerformanceInfo(ctypes.byref(info), info.cb):
                    raise OSError("GetPerformanceInfo failed")
                total, limit = int(info.CommitTotal * info.PageSize), int(info.CommitLimit * info.PageSize)
                result.update(commit_bytes=total, commit_limit_bytes=limit, commit_headroom_bytes=limit-total,
                              commit_percent=100*total/limit, source="Windows GetPerformanceInfo / psutil")
            elif Path("/proc/meminfo").is_file():
                fields = {line.split(":")[0]: int(line.split()[1])*1024 for line in Path("/proc/meminfo").read_text().splitlines() if ":" in line}
                total, limit = fields["Committed_AS"], fields["CommitLimit"]
                result.update(commit_bytes=total, commit_limit_bytes=limit, commit_headroom_bytes=limit-total, commit_percent=100*total/limit, source="Linux advisory commit accounting / psutil")
        except (OSError, KeyError, ValueError):
            result["advisory"] = True
        try:
            port = urlsplit(self.settings.backend).port
            matches = {c.pid for c in psutil.net_connections(kind="tcp") if c.status == psutil.CONN_LISTEN and c.laddr.port == port and c.laddr.ip in {"127.0.0.1", "::1"} and c.pid}
            if len(matches) == 1:
                proc = psutil.Process(matches.pop()); created = proc.create_time()
                cwd = Path(proc.cwd()).resolve()
                command = proc.cmdline()
                if cwd == (self.settings.root / "runtime/ComfyUI").resolve() and any(Path(x).name == "main.py" for x in command):
                    memory = proc.memory_info()
                    private = getattr(memory, "private", None)
                    if private is None and os.name != "nt":
                        private = getattr(proc.memory_full_info(), "uss", None)
                    if proc.create_time() == created and proc.is_running():
                        result.update(comfy_pid=proc.pid, comfy_created=created, comfy_private_bytes=private)
        except (psutil.Error, OSError, ValueError):
            pass
        if result["comfy_pid"] is None:
            result["advisory"] = True
        return result


class Pressure:
    """A window belongs to one owned prompt AND one port/creation identity."""
    def __init__(self):
        self.samples = deque()
        self.evidence = deque(maxlen=32)
        self.identity = None
        self.low_since = None
        self.last_observed = None

    def observe(self, job_id, sample, now):
        identity = (job_id, sample.get("comfy_pid"), sample.get("comfy_created"))
        gap = self.last_observed is not None and (now-self.last_observed > 5 or now < self.last_observed)
        if identity != self.identity or gap:
            self.samples.clear(); self.evidence.clear(); self.low_since = None; self.identity = identity
        self.last_observed = now
        if sample.get("comfy_pid") is None:
            return None
        self.evidence.append({"observed_monotonic": now, **sample})
        available = sample.get("available_bytes")
        if available is not None and available < 512*MIB:
            self.low_since = now if self.low_since is None else self.low_since
        else:
            self.low_since = None
        if self.low_since is not None and now-self.low_since >= 30:
            return "Available memory stayed below 512 MiB for 30 seconds"
        private = sample.get("comfy_private_bytes")
        if private is not None:
            self.samples.append((now, private))
            while len(self.samples) > 1 and self.samples[1][0] <= now-30:
                self.samples.popleft()
            if self.samples and now-self.samples[0][0] >= 30 and (sample.get("commit_percent") or 0) >= 98 and private-self.samples[0][1] >= 256*MIB:
                return "Commit >=98% and this Comfy process Private grew >=256 MiB over 30 seconds"
        else:
            self.samples.clear()
        return None


class Backend:
    def __init__(self, settings):
        self.url, self.session = settings.backend, None

    async def request(self, method, path, payload=None):
        try:
            async with self.session.request(method, self.url+path, json=payload) as response:
                raw = await response.read()
                data = json.loads(raw) if raw else {}
                if response.status >= 400:
                    raise ApiError("VALIDATION_FAILED", "Backend rejected the workflow", response.status if response.status < 500 else 502, data)
                return data
        except ApiError:
            raise
        except (aiohttp.ClientError, TimeoutError, ValueError) as exc:
            raise ApiError("BACKEND_UNAVAILABLE", "The loopback backend did not respond", 503, type(exc).__name__) from exc


class Gateway:
    def __init__(self, settings, backend=None, resources=None, clock=time.monotonic):
        self.settings = settings; self.backend = backend or Backend(settings)
        self.resources = resources or Resources(settings); self.clock = clock
        self.lock = asyncio.Lock(); self.jobs = OrderedDict(); self.requests = OrderedDict()
        self.pressure = Pressure(); self.last_activity = clock(); self.idle_armed = True
        self.last_freed_at = None; self.last_profile = None
        self.client_id = str(uuid.uuid4()); self.task = None

    def projects(self):
        parent = self.settings.root / "projects"
        return sorted(p.name for p in parent.iterdir() if p.is_dir() and p.resolve().is_relative_to(parent.resolve()) and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", p.name) and (p/"analysis/audio.json").is_file() and (p/"tools/render_final.mjs").is_file()) if parent.is_dir() else []

    def profile(self, key):
        data = definitions()
        if key not in data:
            raise ApiError("UNKNOWN_PROFILE", "Unknown workflow profile")
        label, description, kind, fields, bindings = deepcopy(data[key])
        workflow = json.loads((self.settings.root / "workflows/api" / (key+".json")).read_text("utf-8-sig"))
        for f in fields:
            if f["name"] == "project_name":
                f["options"] = self.projects()
            if f["name"] == "language":
                names = ["自动", "中文", "英语", "日语", "韩语", "德语", "法语", "俄语", "葡萄牙语", "西班牙语", "意大利语"]
                f["option_labels"] = {value: text(zh, value) for value, zh in zip(LANGUAGES, names)}
            if f["name"] == "quality":
                f["option_labels"] = {"preview": text("预览", "Preview"), "final": text("成片", "Final")}
            if f["type"] not in {"image", "audio"}:
                node, name = bindings[f["name"]][0]
                f["default"] = workflow[node]["inputs"][name]
                if key == "music" and f["name"] in {"instrumental", "thinking"}:
                    f["default"] = "true" if f["default"] else "false"
        return dict(key=key, label=label, description=description, experimental=key.startswith("video"), fields=fields, output_kind=kind), bindings, workflow

    def assets(self):
        result = {"images": [], "audio": []}
        base = self.settings.root / "input"
        if base.is_dir():
            for p in sorted(base.rglob("*")):
                if sum(map(len, result.values())) >= 500:
                    break
                if not p.is_file() or p.suffix.lower() not in MEDIA:
                    continue
                relative = p.relative_to(base).as_posix()
                try:
                    path = media_path(self.settings.root, "input", relative)
                except ApiError:
                    continue
                kind = MEDIA[path.suffix.lower()][0]
                if kind in {"image", "audio"}:
                    result["images" if kind == "image" else "audio"].append(dict(name=relative, url=asset_url("input", relative)))
        return result

    def compile(self, profile, values):
        info, bindings, workflow = self.profile(profile)
        if not isinstance(values, dict):
            raise ApiError("INVALID_REQUEST", "values must be an object")
        allowed = {f["name"]: f for f in info["fields"]}
        if set(values)-set(allowed):
            raise ApiError("UNKNOWN_FIELD", "Unknown profile field", details=sorted(set(values)-set(allowed)))
        for name, f in allowed.items():
            value = values.get(name, f["default"])
            kind = f["type"]
            if kind in {"integer", "number"}:
                if type(value) not in ({int} if kind == "integer" else {int, float}) or not f["min"] <= value <= f["max"]:
                    raise ApiError("INVALID_VALUE", f"Invalid {name}")
                if f["step"] and (value-f["min"]) % f["step"] != 0:
                    raise ApiError("INVALID_VALUE", f"Invalid step for {name}")
                if name == "length" and value % 4 != 1:
                    raise ApiError("INVALID_VALUE", "Video frame count must be 4n+1")
            else:
                if not isinstance(value, str) or len(value) > 16000 or (f["required"] and not value.strip()):
                    raise ApiError("INVALID_VALUE", f"Invalid {name}")
                if kind == "select" and value not in f["options"]:
                    raise ApiError("INVALID_PROJECT" if name == "project_name" else "INVALID_VALUE", f"Invalid {name}")
                if kind in {"image", "audio"}:
                    path = media_path(self.settings.root, "input", value)
                    if MEDIA[path.suffix.lower()][0] != kind:
                        raise ApiError("UNSUPPORTED_MEDIA", f"Wrong media type for {name}")
                if name == "filename_prefix" and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,40}", value):
                    raise ApiError("INVALID_VALUE", "Invalid output prefix")
            for node, target in bindings[name]:
                workflow[node]["inputs"][target] = (value == "true") if profile == "music" and name in {"instrumental", "thinking"} else value
        for node in workflow.values():
            if node.get("class_type") in {"SaveImage", "SaveAudio", "SaveVideo"}:
                node["inputs"]["filename_prefix"] = "gateway/"+profile
        return workflow

    async def queue(self):
        return await self.backend.request("GET", "/queue")

    @staticmethod
    def ids(queue, name):
        return {str(x[1]) for x in queue.get(name, []) if isinstance(x, list) and len(x) > 1}

    @staticmethod
    def empty(queue):
        return not queue.get("queue_running") and not queue.get("queue_pending")

    async def free(self):
        if not self.empty(await self.queue()):
            raise ApiError("BUSY", "The native queue is busy", 409)
        await self.backend.request("POST", "/free", {"free_memory": True, "unload_models": True})
        # Native /free exposes no flag-consumption acknowledgement. Observe an
        # idle/resource barrier without claiming an authoritative native ack.
        started = self.clock(); samples = deque(maxlen=3)
        while True:
            await asyncio.sleep(0.5)
            if not self.empty(await self.queue()):
                raise ApiError("BUSY", "Another native job started while freeing", 409)
            samples.append(await asyncio.to_thread(self.resources.sample))
            if self.clock()-started >= 2 and len(samples) == 3:
                identities = {(s.get("comfy_pid"), s.get("comfy_created")) for s in samples}
                stable = len(identities) == 1
                for key, tolerance in [("comfy_private_bytes", 16*MIB), ("available_bytes", 256*MIB), ("commit_bytes", 256*MIB)]:
                    values = [s.get(key) for s in samples]
                    if all(v is not None for v in values):
                        stable = stable and max(values)-min(values) <= tolerance
                if stable: break
            if self.clock()-started >= 10:
                raise ApiError("RELEASE_PENDING", "Release requested; idle resources have not settled yet", 503)
        self.last_freed_at = time.time(); self.idle_armed = False
        return {"ok": True, "release_requested": True, "observed_stable": True, "released": None,
                "verification": "observed_queue_and_resource_stability", "native_ack": False}

    def trim(self):
        while len(self.requests) > 256:
            _, record = self.requests.popitem(last=False)
            self.jobs.pop(record["job_id"], None)

    async def run(self, payload):
        if not isinstance(payload, dict) or set(payload) != {"profile", "values", "request_id"}:
            raise ApiError("INVALID_REQUEST", "Expected profile, values and request_id")
        try:
            rid = str(uuid.UUID(payload["request_id"]))
        except (ValueError, TypeError, AttributeError):
            raise ApiError("INVALID_REQUEST", "request_id must be a UUID")
        profile = payload["profile"]
        if not isinstance(profile, str):
            raise ApiError("UNKNOWN_PROFILE", "Unknown workflow profile")
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        async with self.lock:
            if rid in self.requests:
                record = self.requests[rid]
                if record["fingerprint"] != fingerprint:
                    raise ApiError("INVALID_REQUEST", "request_id was already used for different values", 409)
                return self.jobs[record["job_id"]]
            workflow = self.compile(profile, payload["values"])
            if not self.empty(await self.queue()):
                raise ApiError("BUSY", "The native queue is busy", 409)
            await self.free()
            sample = await asyncio.to_thread(self.resources.sample)
            if (sample.get("available_bytes") is not None and sample["available_bytes"] < GIB) or (sample.get("commit_headroom_bytes") is not None and sample["commit_headroom_bytes"] < 2*GIB):
                raise ApiError("LOW_RESOURCES", "Need at least 1 GiB available RAM and 2 GiB commit headroom", 409, sample)
            if not self.empty(await self.queue()):
                raise ApiError("BUSY", "A native task arrived before submission", 409)
            pid = str(uuid.uuid4()); now = time.time()
            job = dict(id=pid, prompt_id=pid, profile=profile, status="pending", outputs=[], error=None,
                       cancel_reason=None, created_at=now, updated_at=now, submission_unknown=False,
                       backend_identity={"pid": sample.get("comfy_pid"), "created": sample.get("comfy_created")})
            self.jobs[pid] = job; self.requests[rid] = {"fingerprint": fingerprint, "job_id": pid}
            self.trim(); self.last_activity = self.clock(); self.idle_armed = True
            try:
                response = await self.backend.request("POST", "/prompt", {"prompt": workflow, "prompt_id": pid, "client_id": self.client_id, "extra_data": {"media_studio_gateway": {"request_id": rid, "profile": profile}}})
                if response.get("prompt_id") != pid:
                    raise ApiError("SUBMISSION_UNCERTAIN", "Backend returned a different task identity", 502)
            except ApiError as exc:
                if exc.code == "VALIDATION_FAILED":
                    job.update(status="error", error={"code": exc.code, "message": exc.message, "details": exc.details})
                else:
                    job.update(status="unknown", submission_unknown=True, error={"code": "SUBMISSION_UNCERTAIN", "message": "Submission outcome is uncertain; retry the same request_id, never a new request"})
                raise
            self.last_profile = profile
            return job

    def output_media(self, outputs):
        result = []
        def walk(value):
            if isinstance(value, dict):
                if isinstance(value.get("filename"), str) and value.get("type", "output") == "output":
                    relative = "/".join(p for p in [value.get("subfolder", ""), value["filename"]] if p)
                    try:
                        path = media_path(self.settings.root, "output", relative)
                        kind, mime = MEDIA[path.suffix.lower()]
                        record = dict(kind=kind, name=relative, url=asset_url("output", relative), mime=mime)
                        if record not in result: result.append(record)
                    except ApiError:
                        pass
                for child in value.values(): walk(child)
            elif isinstance(value, list):
                for child in value: walk(child)
        walk(outputs)
        return result

    async def refresh(self, job):
        try:
            return await self._refresh(job)
        except ApiError as exc:
            if exc.code != "BACKEND_UNAVAILABLE":
                raise
            if job["status"] not in {"success", "error", "cancelled"}:
                job.update(status="unknown", error={"code": exc.code, "message": "Backend is unavailable; task outcome is unknown. No resubmission was attempted."}, updated_at=time.time())
            return job

    async def _refresh(self, job):
        queue = await self.queue(); pid = job["id"]
        if pid in self.ids(queue, "queue_running"):
            job.update(status="running", submission_unknown=False, error=None)
        elif pid in self.ids(queue, "queue_pending"):
            job.update(status="pending", submission_unknown=False, error=None)
        else:
            history = (await self.backend.request("GET", "/history/"+pid)).get(pid)
            if history:
                status = history.get("status", {}); messages = status.get("messages", [])
                names = [m[0] for m in messages if isinstance(m, list) and m]
                if "execution_interrupted" in names:
                    job.update(status="cancelled", outputs=[])
                elif status.get("completed") and "execution_success" in names:
                    outputs = self.output_media(history.get("outputs", {}))
                    job.update(status="success" if outputs else "error", outputs=outputs,
                               error=None if outputs else {"code": "NO_OUTPUT", "message": "Task completed without an allowed media output"})
                else:
                    errors = [m[1] for m in messages if isinstance(m, list) and len(m)>1 and m[0] == "execution_error"]
                    job.update(status="error", outputs=[], error={"code": "EXECUTION_ERROR", "message": "Backend execution failed", "details": errors})
            elif job["status"] not in {"success", "error", "cancelled"}:
                sample = await asyncio.to_thread(self.resources.sample)
                previous = job.get("backend_identity", {})
                current = {"pid": sample.get("comfy_pid"), "created": sample.get("comfy_created")}
                known = all(previous.get(k) is not None and current[k] is not None for k in ("pid", "created"))
                if known and previous != current:
                    job.update(status="error", outputs=[], error={"code": "BACKEND_RESTARTED", "message": "The verified backend process changed and this task is absent from queue/history.", "details": {"previous": previous, "current": current}})
                else:
                    job.update(status="unknown", error={"code": "LOST_TASK", "message": "Task is absent from queue/history; its outcome is unknown. No resubmission was attempted."})
        job["updated_at"] = time.time()
        return job

    async def cancel(self, job, reason=None):
        queue = await self.queue(); pid = job["id"]
        if pid in self.ids(queue, "queue_running"):
            await self.backend.request("POST", "/interrupt", {"prompt_id": pid})
            job["cancel_reason"] = reason or "user"
        elif pid in self.ids(queue, "queue_pending"):
            await self.backend.request("POST", "/queue", {"delete": [pid]})
            job.update(status="cancelled", cancel_reason=reason or "user", outputs=[])
        else:
            await self.refresh(job)
        return job

    async def maintain(self):
        while True:
            await asyncio.sleep(2)
            try:
                async with self.lock:
                    queue = await self.queue()
                    running = self.ids(queue, "queue_running")
                    owned = next((j for j in self.jobs.values() if j["id"] in running), None)
                    if not self.empty(queue):
                        self.last_activity = self.clock(); self.idle_armed = True
                    if owned:
                        sample = await asyncio.to_thread(self.resources.sample)
                        reason = self.pressure.observe(owned["id"], sample, self.clock())
                        if reason:
                            # A fresh listener/creation identity AND same native
                            # owned task must still match before targeted cancel.
                            fresh = await asyncio.to_thread(self.resources.sample)
                            if (sample.get("comfy_pid"), sample.get("comfy_created")) == (fresh.get("comfy_pid"), fresh.get("comfy_created")):
                                owned["protection_samples"] = [*self.pressure.evidence, {"fresh_identity_check": True, **fresh}]
                                await self.cancel(owned, reason)
                                LOG.warning("Owned task %s protection: %s", owned["id"], reason)
                    if self.empty(queue) and self.idle_armed and self.clock()-self.last_activity >= self.settings.idle_seconds:
                        await self.free()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                LOG.warning("Maintenance unavailable: %s", type(exc).__name__)


def create_app(settings, backend=None, resources=None, maintenance=True):
    gateway = Gateway(settings, backend, resources)

    @web.middleware
    async def guard(request, handler):
        origin = request.headers.get("Origin")
        api = request.path.startswith("/api/")
        allowed_origin = False
        try:
            if request.headers.getall("Host", []) != [request.host] or request.host.lower() not in settings.hosts:
                raise ApiError("FORBIDDEN_HOST", "Host is not allowed", 403)
            if len(request.headers.getall("Origin", [])) > 1 or (origin is not None and origin not in settings.origins):
                raise ApiError("FORBIDDEN_ORIGIN", "Origin is not allowed", 403)
            allowed_origin = origin in settings.origins if origin else False
            if request.method == "OPTIONS" and api:
                if request.headers.get("Access-Control-Request-Method", "GET") not in {"GET", "POST"}:
                    raise ApiError("FORBIDDEN_ORIGIN", "Method is not allowed", 403)
                requested = {x.strip().lower() for x in request.headers.get("Access-Control-Request-Headers", "").split(",") if x.strip()}
                if requested - {"content-type"}:
                    raise ApiError("FORBIDDEN_ORIGIN", "Request headers are not allowed", 403)
                response = web.Response(status=204)
            else:
                response = await handler(request)
        except ApiError as exc:
            error = {"code": exc.code, "message": exc.message}
            if exc.details is not None: error["details"] = exc.details
            response = web.json_response({"ok": False, "error": error}, status=exc.status)
        except web.HTTPException as exc:
            response = web.json_response({"ok": False, "error": {"code": "UPLOAD_TOO_LARGE" if exc.status == 413 else "NOT_FOUND", "message": exc.reason}}, status=exc.status)
        except Exception:
            LOG.exception("Gateway request failed")
            response = web.json_response({"ok": False, "error": {"code": "INTERNAL_ERROR", "message": "Gateway request failed"}}, status=500)
        response.headers["X-Content-Type-Options"] = "nosniff"
        if api:
            response.headers["Cache-Control"] = "no-store"
            response.headers["Vary"] = "Origin"
            if allowed_origin:
                response.headers["Access-Control-Allow-Origin"] = origin
                if request.method == "OPTIONS":
                    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
                    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
                    response.headers["Access-Control-Allow-Private-Network"] = "true"
        return response

    app = web.Application(middlewares=[guard], client_max_size=UPLOAD_LIMIT+65536)
    app[GATEWAY_KEY] = gateway

    async def body(request):
        if request.content_type != "application/json" or (request.content_length or 0) > 65536:
            raise ApiError("BAD_JSON", "Expected a small application/json body")
        try:
            raw = await request.read()
            if len(raw)>65536: raise ValueError()
            return json.loads(raw)
        except (ValueError, UnicodeError):
            raise ApiError("BAD_JSON", "Invalid JSON")

    async def catalog(request):
        return web.json_response(dict(ok=True, version=1, profiles=[gateway.profile(k)[0] for k in definitions()], assets=gateway.assets(), projects=gateway.projects(), limits={"upload_bytes": UPLOAD_LIMIT, "idle_free_seconds": 30}))

    async def status(request):
        resources = await asyncio.to_thread(gateway.resources.sample)
        try:
            q = await gateway.queue(); online = True
            queue = dict(running=len(q.get("queue_running", [])), pending=len(q.get("queue_pending", [])))
            ids = gateway.ids(q, "queue_running") | gateway.ids(q, "queue_pending")
            owned = next((j for j in gateway.jobs.values() if j["id"] in ids), None)
            if owned: await gateway.refresh(owned)
        except ApiError:
            online=False; queue=dict(running=None, pending=None); owned=None
        resources["gpu"] = None
        if online:
            try:
                stats = await gateway.backend.request("GET", "/system_stats")
                devices = [{k: d.get(k) for k in ("name", "vram_total", "vram_free")} for d in stats.get("devices", []) if isinstance(d, dict)]
                resources["gpu"] = {"devices": devices, "source": "native /system_stats"}
            except ApiError:
                pass
        return web.json_response(dict(ok=True, backend={"online": online, "url": settings.backend, "client_url": settings.native_client_url}, queue=queue, resources=resources, active_job=owned, idle_free={"seconds": 30, "armed": gateway.idle_armed, "last_freed_at": gateway.last_freed_at}))

    async def run(request):
        job = await gateway.run(await body(request))
        return web.json_response({"ok": True, "job": job}, status=202)

    def owned(request):
        key = request.match_info["job_id"]
        try: key = str(uuid.UUID(key))
        except ValueError: raise ApiError("UNKNOWN_JOB", "Unknown gateway task", 404)
        if key not in gateway.jobs: raise ApiError("UNKNOWN_JOB", "Unknown gateway task", 404)
        return gateway.jobs[key]

    async def job(request):
        return web.json_response({"ok": True, "job": await gateway.refresh(owned(request))})

    async def cancel(request):
        async with gateway.lock:
            result = await gateway.cancel(owned(request))
        return web.json_response({"ok": True, "job": result})

    async def free(request):
        async with gateway.lock:
            result = await gateway.free()
        return web.json_response(result)

    async def upload(request):
        if not request.content_type.startswith("multipart/"):
            raise ApiError("UNSUPPORTED_MEDIA", "Use multipart form-data", 415)
        reader = await request.multipart(); part = await reader.next()
        if part is None or part.name != "file" or not part.filename:
            raise ApiError("INVALID_REQUEST", "Expected exactly one file field")
        data=bytearray()
        while True:
            chunk=await part.read_chunk(65536)
            if not chunk: break
            data.extend(chunk)
            if len(data)>UPLOAD_LIMIT: raise ApiError("UPLOAD_TOO_LARGE", "File exceeds 32 MiB", 413)
        if await reader.next() is not None: raise ApiError("INVALID_REQUEST", "Expected exactly one file")
        suffix=file_signature(data)
        original=Path(part.filename).suffix.lower()
        if original != suffix and not (original==".jpeg" and suffix==".jpg"):
            raise ApiError("UNSUPPORTED_MEDIA", "File extension and signature do not match", 415)
        relative="uploads/"+str(uuid.uuid4())+suffix; path=media_path(settings.root,"input",relative,False)
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open("xb") as f: f.write(data)
        return web.json_response({"ok": True,"asset":{"name":relative,"kind":MEDIA[suffix][0],"url":asset_url("input",relative)}})

    async def asset(request):
        if set(request.query) != {"type","path"}: raise ApiError("INVALID_VALUE","Expected type and path")
        p=media_path(settings.root,request.query["type"],request.query["path"])
        response=web.FileResponse(p);response.content_type=MEDIA[p.suffix.lower()][1]
        return response

    async def static(request):
        name=request.match_info.get("path","") or "index.html"
        base=(settings.root/"web/dist").resolve();p=(base/name).resolve()
        if not p.is_relative_to(base) or any(x.startswith(".") for x in Path(name).parts) or p.suffix.lower() not in {".html",".js",".css",".svg",".png",".ico"} or not p.is_file():
            raise ApiError("NOT_FOUND","Static file not found",404)
        return web.FileResponse(p)

    app.router.add_get("/api/catalog",catalog);app.router.add_get("/api/status",status)
    app.router.add_post("/api/run",run);app.router.add_get("/api/jobs/{job_id}",job)
    app.router.add_post("/api/jobs/{job_id}/cancel",cancel);app.router.add_post("/api/free",free)
    app.router.add_post("/api/upload",upload);app.router.add_get("/api/asset",asset)
    async def preflight(request):
        return web.Response(status=204)
    app.router.add_route("OPTIONS","/api/{tail:.*}",preflight)
    app.router.add_get("/{path:.*}",static)

    async def startup(app):
        if isinstance(gateway.backend,Backend):
            gateway.backend.session=aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20),trust_env=False)
        if maintenance: gateway.task=asyncio.create_task(gateway.maintain())
    async def cleanup(app):
        if gateway.task:
            gateway.task.cancel()
            try: await gateway.task
            except asyncio.CancelledError: pass
        if isinstance(gateway.backend,Backend) and gateway.backend.session:
            await gateway.backend.session.close()
    app.on_startup.append(startup);app.on_cleanup.append(cleanup)
    return app


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--root",default=os.environ.get("MEDIA_STUDIO_ROOT",str(Path(__file__).resolve().parents[1])));parser.add_argument("--config")
    args=parser.parse_args();root=Path(args.root).resolve();config=Path(args.config) if args.config else root/"config/gateway.json"
    data=json.loads(config.read_text("utf-8-sig")) if config.is_file() else {}
    settings=Settings(root,data);logging.basicConfig(level=logging.INFO)
    web.run_app(create_app(settings),host=settings.host,port=settings.port,print=lambda msg: LOG.info(msg),access_log=None)


if __name__=="__main__":main()
