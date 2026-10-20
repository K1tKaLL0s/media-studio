# 在现有腾讯云 Linux 主机接续

本指南面向你已有、已能通过 SSH 登录的 Linux GPU 主机和已挂载数据盘。本次交付不创建云实例、云开发任务或新存储，不部署服务、不安装依赖，也不运行模型。以下命令是恢复入口，Linux 兼容性与生成效果仍需在目标主机验收。

Windows 的 `.cmd`、`.ps1` 启动器不能直接在 Linux 执行。仓库的 Windows 依赖快照也不能原样当作 Linux wheel lock；尤其 Torch/CUDA、IndexTTS 文本规范化依赖、音频库和浏览器组件需要按 Linux 平台重新解析、固定并核验。

## 1. 指定源码与数据位置

克隆本仓库到源码目录，并选择已有挂载数据盘上的目录。下例路径仅为示例，须先通过 `df -h` 确认它们实际落在预期挂载盘：

```bash
repo=/data/src/media-studio
data=/data/media-studio
# 首次获取；已有 checkout 则使用它，不重复执行 clone。
git clone https://github.com/K1tKaLL0s/media-studio.git "$repo"
cd "$repo"
test -d "$data" || { echo '请先准备已有数据盘上的目标目录'; exit 1; }
df -h "$repo" "$data"
python3 scripts/prepare-linux-data.py --data-dir "$data"
python3 scripts/prepare-linux-data.py --data-dir "$data" --apply
```

`--data-dir` 必须是已存在目录的绝对路径；源码根与数据根必须是互不嵌套的独立目录。准备脚本默认只显示计划；明确加 `--apply` 后才在 Linux 将仓库内 `models`、`cache`、`temp`、`input`、`output`、`projects`、`user`、`logs` 链接到指定数据根下的对应目录。数据盘文件系统需要支持符号链接和硬链接；本指南面向本机挂载的数据盘，不以对象存储挂载代替本地文件系统。已有且指向同一位置的链接可重复使用；遇到已有普通文件、目录或指向其他位置的链接会停止，不覆盖或迁移它们。先自行检查冲突再重试。

源码、`scripts/`、`config/`、`workflows/` 与 `runtime/` 仍在源码目录；运行数据通过链接进入指定数据盘。这不是一个仅设置环境变量就会生效的数据根开关。不要只导出 `MEDIA_STUDIO_DATA_DIR` 并假定所有代码已改用它。

源码和虚拟环境也建议放在空间充足的已有挂载盘。不要将模型或环境复制回系统盘，也不要把它们加入 Git。

## 2. 自动下载固定模型

模型下载器使用仓库清单中的固定 revision、文件大小和官方摘要。先列出分组并查看计划：

```bash
python3 scripts/download-models.py --list
python3 scripts/download-models.py --group anime --group tts-preset --data-dir "$data"
```

可重复指定 `--group`，可选 `anime`、`flux`、`wan`、`tts-preset`、`tts-clone`、`voice-design`、`index-tts`、`music`、`all`。按实际需要选择，避免为试用一个功能下载全部模型。未指定 `--download` 时只做下载计划和磁盘预检，不传输权重。

阅读对应模型许可后，明确执行下载：

```bash
python3 scripts/download-models.py --group anime --group tts-preset --data-dir "$data" --download
```

下载操作不会改变模型的既有许可条款，也不会自动接受上游 gated access。下载器默认预留 5 GiB 空间，可通过 `--reserve-gib` 设置适合当前盘的预留量；预留并不包含未来生成产物、环境安装和缓存增长。

已存在文件只有在完整大小及摘要校验通过后才跳过。断点保存在同一目标目录的 `.part` 文件中，服务器支持 HTTP Range 时续传；不支持时重新写同一个临时文件。完整文件通过预期大小与官方 LFS SHA-256 或 Git blob SHA-1 校验后才原子发布，失败不把半成品当作模型。

仅验证已有文件：

```bash
python3 scripts/download-models.py --group anime --group tts-preset --data-dir "$data" --verify-only
```

下载完成不是模型推理通过。VoiceDesign、IndexTTS 和 ACE-Step 仍需要各自的首次加载、GPU 适配与音频验收。`models/` 及其断点文件都不入 Git。

## 3. 准备 Linux 运行依赖

运行依赖安装命令前，先执行第 4 节的环境变量与缓存目录设置段。

按 [来源清单](UPSTREAM.md) 的固定提交获取 ComfyUI、Qwen3-TTS 以及实际需要的 IndexTTS、ACE-Step、PV 和 JIZURA 源码，放到 [INSTALL.md](INSTALL.md) 指定的 `runtime/` 目录。ComfyUI 目录已含本项目节点，合并固定上游源码时保留 `custom_nodes/media_studio`，遇到冲突先比较。

为所选功能建立独立虚拟环境。Linux 可执行文件位于 `bin/python`，不是 Windows 的 `Scripts/python.exe`。例如：

```bash
python3.12 -m venv runtime/comfy-venv
python3.12 -m venv runtime/tts-venv
# 仅在需要这些功能时创建：
python3.10 -m venv runtime/index-tts-venv
python3.12 -m venv runtime/ace-venv
python3.12 -m venv runtime/pv-venv
```

先确认目标主机实际有相应 Python 版本、可用 NVIDIA 驱动和 CUDA 兼容性。以固定上游源码的 Linux 依赖标记为依据，为 Linux 选定兼容的官方 PyTorch CUDA wheel，再生成该主机的固定依赖记录并安装。Windows 的 `cu128`/`cu130` 版本记录是参考证据，不能保证对应 Linux 轮子、驱动或 ABI 已通过。

IndexTTS 的 Windows 规范化依赖和 wheel ABI 不可直接搬用；ACE 上游也按平台选择不同 Torch 版本。不要在 Linux 执行 Windows lock 后通过忽略依赖错误继续。遇到没有对应 Linux 包的固定版本，应记录缺项并完成兼容性调整和独立验收，再启用该功能。

Node.js、ffmpeg、ffprobe 使用目标主机 PATH 中可核实的程序。PV 还需可用的无头浏览器/WebGL 环境、原作者模板和字体。仓库不含 `pv-demo` 或私人歌曲素材；先从固定上游建立自己的工程，再按作者 Skill 检查环境与渲染。Linux 上不能直接假定存在 Windows 的 `msedge` 浏览器通道。

## 4. 显式设置运行缓存与启动目录

在要运行服务的 shell 中设置以下环境。变量只影响当前进程及子进程，不修改系统级缓存配置：

```bash
export MEDIA_STUDIO_ROOT="$repo"
export PYTHONNOUSERSITE=1 PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1
export HF_HUB_DISABLE_TELEMETRY=1 DO_NOT_TRACK=1 COMFY_WHERE=local
export TEMP="$data/temp" TMP="$data/temp" TMPDIR="$data/temp"
export HF_HOME="$data/cache/huggingface"
export HF_HUB_CACHE="$HF_HOME/hub" HF_MODULES_CACHE="$HF_HOME/modules"
export TORCH_HOME="$data/cache/torch" XDG_CACHE_HOME="$data/cache"
export PIP_CACHE_DIR="$data/cache/pip" npm_config_cache="$data/cache/npm"
export MODELSCOPE_CACHE="$data/cache/modelscope"
export CUDA_CACHE_PATH="$data/cache/cuda"
export TORCHINDUCTOR_CACHE_DIR="$data/cache/inductor"
export TRITON_CACHE_DIR="$data/cache/triton"
export NUMBA_CACHE_DIR="$data/cache/numba" MPLCONFIGDIR="$data/cache/matplotlib"
export PLAYWRIGHT_BROWSERS_PATH="$data/cache/playwright"
mkdir -p "$TEMP" "$HF_HUB_CACHE" "$HF_MODULES_CACHE" "$TORCH_HOME" \
  "$PIP_CACHE_DIR" "$npm_config_cache" "$MODELSCOPE_CACHE" "$CUDA_CACHE_PATH" \
  "$TORCHINDUCTOR_CACHE_DIR" "$TRITON_CACHE_DIR" "$NUMBA_CACHE_DIR" \
  "$MPLCONFIGDIR" "$PLAYWRIGHT_BROWSERS_PATH"
```

如需覆盖 worker Python 或浏览器设置，在本机专用的 `config/runtime-paths.json` 中填 Linux 可执行路径；不要把带私人路径的配置提交到公共仓库。保持 `MEDIA_STUDIO_ROOT` 指向源码目录，数据目录由准备脚本的链接衔接。Linux 不要直接沿用 Windows 示例中的 `msedge` / `d3d11`；使用目标机器实际安装的 `browser_channel`（例如 `chrome`）和空字符串 `browser_angle`，或不设置这些字段以沿用代码的 Linux 默认值。

确认所需节点、环境、模型与输入完整，且端口未被另一实例占用后，手工启动 ComfyUI：

```bash
cd "$repo/runtime/ComfyUI"
"$repo/runtime/comfy-venv/bin/python" -s main.py \
  --listen 127.0.0.1 --port 8188 \
  --input-directory "$data/input" --output-directory "$data/output" \
  --user-directory "$data/user" --temp-directory "$data/temp" \
  --models-directory "$data/models" \
  --disable-auto-launch --offline --enable-assets \
  --fast-disk --disable-pinned-memory --disable-async-offload
```

上例沿用项目固定 ComfyUI 版本的参数；如果换版，先核对该版 `main.py --help`，不要静默丢弃路径参数。另一终端在相同环境下启动网关：

```bash
cd "$repo"
"$repo/runtime/comfy-venv/bin/python" -B -X utf8 scripts/studio_gateway.py --root "$repo"
```

网关从源码根读取工作流、网页与配置，通过数据链接访问输入、输出和项目。ComfyUI 和网关都只监听 loopback；无需向公网开放 8188/8190。

## 5. 从本机连接与验收

在自己的电脑使用已有 SSH 认证建立转发：

```bash
ssh -N -L 8188:127.0.0.1:8188 -L 8190:127.0.0.1:8190 user@GPU_HOST
```

随后在本机浏览器打开 `http://127.0.0.1:8188` 或 `http://127.0.0.1:8190`。将 `user@GPU_HOST` 替换成已有主机地址，不在仓库保存 SSH 私钥或登录信息。若本机端口已占用，先处理冲突；使用其他转发端口时，需要同时明确调整前端地址、Host/origin 配置，不能仅换端口后放宽全部 origin。

同一块 8GB GPU 每次只执行一个生成任务；多型号任务按顺序运行并确认前一个任务释放模型。先做小预览，再按真实任务 ID、终态、可解码产物和实际画面/试听验收。磁盘容量充足不保证 GPU 显存或主机提交内存足够。

输入、生成产物和 PV 工程保留在自己的数据盘，不推回公共 GitHub 仓库。现有网关使用同机文件；SSH 转发负责访问服务，不会自动同步自己电脑上的素材。
