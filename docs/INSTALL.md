# 安装与恢复

这是从已配置的 Windows 本地工作台整理出的源码包。以下步骤用于恢复所需目录和依赖，没有在本次公开副本上执行。版本记录是原安装的固定快照，不能代替新机器上的安装、ABI/CUDA 检查和逐项生成验收。

## 1. 前置条件与目录

原环境使用 Windows x64、NVIDIA GPU、Python 3.12、单独的 Python 3.10（IndexTTS）、Node.js 24.14.1、Git、ffmpeg/ffprobe 9.0.2，以及已安装的 Edge。PV 上游要求 Node.js 20+、Python 3.10+。请先确认驱动与所选 PyTorch CUDA 构建兼容。

在空间充足的磁盘克隆本仓库。所有命令从仓库根目录运行：

```powershell
$studio = (Get-Location).Path
. .\scripts\studio-env.ps1
```

启动环境脚本只设置当前进程的缓存、TEMP/TMP 和运行路径；它不会修改系统虚拟内存或全局缓存设置。Python、pip、Node 等安装工具也应从这个进程调用，避免安装阶段退回系统盘缓存。`cache/`、`temp/`、`models/`、`input/`、`output/`、`projects/` 和虚拟环境不应提交到 Git。

`config/runtime-paths.example.json` 是配置模板，保留 Node/浏览器等可用默认选项。Python worker 与节点从项目位置推导根目录，并默认使用根目录内各用途的虚拟环境。需要覆盖默认程序位置时，复制为不纳入版本控制的 `config/runtime-paths.json`，将相应 Python 字段填成这台机器上的程序绝对路径，Node 等支持 PATH 命令的选项可保留命令名。不要把原机器的路径粘入公共配置。可先用 `Get-Command python,node,git,ffmpeg,ffprobe,curl.exe` 检查可执行文件来源。

## 2. 取得固定上游源码

从 [UPSTREAM.md](UPSTREAM.md) 中的固定提交取得上游源码，放置为：

```text
runtime/ComfyUI/
runtime/Qwen3-TTS/
runtime/IndexTTS-2.5/
runtime/ACE-Step-1.5/
runtime/vocaloid-style-mv-pipeline/
runtime/JIZURA/
runtime/ffmpeg/bin/{ffmpeg.exe,ffprobe.exe}
```

`runtime/ComfyUI/` 已有本项目的 `custom_nodes/media_studio`，所以不能直接把它当空目录执行 `git clone`。先在临时目录获取固定 ComfyUI 源码，再合并到上述位置，保留项目节点；遇到同名冲突先比较，不覆盖项目适配器。第三方源码、二进制和示例素材不随本仓库发布，不需要为了恢复源码而复制整套旧运行环境。

Qwen3-TTS 固定源码版本为 0.1.1；IndexTTS 2.5 的工作台名称对应其 `infer_v2_5` 入口，不能用 PyPI 上同名包或较旧代码代替。Index 和 ACE worker 直接从指定的上游源码目录加载入口，不使用上游完整训练/WebUI 依赖集合。

## 3. Python 环境

为各用途建立独立环境：

```powershell
py -3.12 -m venv runtime/comfy-venv
py -3.12 -m venv runtime/tts-venv
py -3.12 -m venv runtime/pv-venv
py -3.12 -m venv runtime/control-venv
py -3.12 -m venv runtime/ace-venv
py -3.10 -m venv runtime/index-tts-venv
```

先确认这些 Python 版本确实已安装。不要在失败时改用另一个版本继续安装。所有依赖命令建议加 `--no-compile`，保留错误输出，并只对所选环境运行 `pip check`。

| 环境 | 原快照的关键版本与安装记录 |
| --- | --- |
| ComfyUI | Python 3.12；`torch 2.14.1+cu130`、`torchvision 0.29.1+cu130`；`config/comfy-requirements.lock.txt` |
| Qwen 预设/克隆/VoiceDesign | Python 3.12；`qwen-tts 0.1.1`、`transformers 4.57.3`、`gradio 5.50.0`、`torch 2.14.1+cu130`、`torchaudio 2.11.0+cu130`；`config/tts-requirements.lock.txt` |
| ACE-Step | Python 3.12；`torch/torchaudio 2.7.1+cu128`、`transformers 4.57.6`、`diffusers 0.37.1`；`ace-inference-requirements-20261020.txt` 和 `ace-installed-versions-20261020.lock.txt` |
| IndexTTS | Python 3.10；`torch/torchaudio 2.8.0+cu128`、`transformers 4.52.1`；`index-torch-requirements-20261020.txt`、`index-inference-requirements-20261020.txt`、`index-inference-constraints-20261020.txt` 和已安装版本记录 |
| PV | Python 3.12；`config/pv-requirements.lock.txt`；工程内 Playwright 实测版本 1.64.1 |
| 对话控制（可选） | 独立 `control-venv`；原版本 `comfy-cli 1.22.0`、`comfy-mcp 0.10.0`；`config/control-requirements.lock.txt` |

CUDA wheel 只从其对应的官方索引获取：`https://download.pytorch.org/whl/cu130` 或 `https://download.pytorch.org/whl/cu128`；普通依赖从 `https://pypi.org/simple` 获取。安装某个完整版本记录时，应先将 CUDA 根依赖按对应索引安装，再安装剩余固定依赖并核验版本。不要将整份锁交给仅有 PyPI 的解析器，然后用不带 CUDA 后缀的版本替代。

公开版本记录把旧机器的 `file://` wheel 路径转换为固定包版本，已有 wheel 摘要保留在 `config/wheel-provenance.json`。它们不是跨平台的、包含每个下载物哈希的 lock；原记录里保留的来源 URL、SHA 和模型清单可用于进一步核对。若某个固定版本已无法取得，停止该环境安装并记录缺项，不自动升级。

TTS lock 中 `qwen-tts` 已指向官方 Git 的固定提交。也可先准备固定的 `runtime/Qwen3-TTS`，在依赖就绪后用 `pip install --no-deps` 安装该目录，保持源码提交与版本一致。不要让未固定的 Gradio 版本重新解析整个语音环境。

IndexTTS 以 `config/index-installed-versions-20261020.lock.txt` 的实际版本快照为恢复基准，先按对应官方 cu128 索引安装 CUDA 根依赖，再安装其余固定版本。旧 inference requirements / constraints 是所选路径的计划与来源记录，不能混入与实际快照冲突的版本。不要对上游目录普通执行 `pip install .`，这会引入此工作台未使用的训练、WebUI 和加速依赖。旧 inference 文件的开头可能保留“静态计划”注释；已安装版本快照和验证文档描述的是后来完成的元数据检查，均不表示模型推理通过。

ACE 同样使用精简 inference requirements 和固定源码，不安装完整训练/Gradio 依赖集合。不要把三个语音/音乐环境合并，尤其不要跨环境混用 Torch 版本。

## 4. 模型与输入

按 `config/models.json`、`config/models-tts.json`、`config/models-additions-20261020.json` 中的固定仓库 revision、文件路径、大小和摘要恢复到 `models/`。视觉与新增清单的 `path` 相对于工作台根目录；`models-tts.json` 的嵌套文件路径相对于每项 `target_dir`。公开副本不包含权重，模型是否存在必须在本机重新检查；清单中的历史验证记录不代表新副本已有该文件。

原 Qwen 预设使用 `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice`，克隆使用 `Qwen/Qwen3-TTS-12Hz-0.6B-Base`，分别恢复到 `models/tts/` 下的同名目录。VoiceDesign 也是独立型号，不可用 CustomVoice 或 Base 替换。

视觉工作流按 `config/models.json` 对应路径恢复 Anima、FLUX.2 Klein 和 Wan 的扩散模型、文本编码器及 VAE。IndexTTS 和 ACE 还需要清单指定的辅助模型。官方模型仓库的条款可能不同，先核对对应许可再下载和使用。

`scripts/fetch-file.py` 接受固定 URL、预期大小和 SHA；使用前先读其 `--help`，明确传入适合本机的 curl 程序与代理选项，不依赖旧机代理。它不是模型目录的自动扫描或自动下载器。

工作流中的 `REPLACE_WITH_UPLOADED_IMAGE.png`、`reference.wav` 和 PV 项目名都是待填输入。仅修改本次任务副本；先把有权使用的材料放入本机 input 或通过已连接的上传入口导入，再填写返回的真实文件名。不要把私人素材或声纹材料提交到仓库。

## 5. PV/MV 工程

仓库的 `upstream/vocaloid-style-mv/` 保留原作者 Skill、参考和 MIT 许可，不包含工程 template。恢复完整上游后，从固定的 `runtime/vocaloid-style-mv-pipeline/skills/vocaloid-style-mv/SKILL.md` 开始，完整读取原作者阶段指引和需要的 references。仓库中的 `media-studio` Skill 是执行桥接层，不能替代原作者的工程模板与创作流程。

使用原作者 `scripts/new_project.py` 在 `projects/` 下建立新工程，不覆盖已有工程。示例（输入文件需由使用者准备）：

```powershell
& .\runtime\pv-venv\Scripts\python.exe .\runtime\vocaloid-style-mv-pipeline\skills\vocaloid-style-mv\scripts\new_project.py .\projects\my-mv --song .\input\song.wav --lyrics .\input\lyrics.lrc
```

模板的 setup 会安装 Node/Playwright 与 Python 依赖、下载字体，并取得/构建 JIZURA。恢复固定快照时先核对模板、固定依赖和 JIZURA 提交，再自行执行需要的 setup 步骤；本次发布没有替使用者执行这些下载。设置 `JIZURA_DIR` 指向固定 `runtime/JIZURA`，避免重复获取。沿用已安装的 Edge/Chrome 通道时无需再下载一整套浏览器。

配置 PV Python、Node、ffmpeg/ffprobe 和浏览器通道后，先在工程内运行 `tools/check_env.py --webgl`，检查必需项；再分析音频、检查静帧，最后调用 `tools/render_final.mjs`。字体依各自 OFL 等许可处理；歌曲、歌词和插画也分别保留授权与署名。项目材料和成片仅留在本机。

## 6. 启动与逐项验收

确认依赖与模型完整，且本机端口未被另一实例占用后：

```powershell
& .\scripts\start-comfy.ps1
```

ComfyUI 监听 `127.0.0.1:8188`。需要网页网关时，在另一个同样设置好环境的终端执行：

```powershell
& .\scripts\start-gateway.ps1
```

网关默认监听 `127.0.0.1:8190`。`config/gateway.json` 使用本地后端与明确的 allowed origins；仅为自己实际使用的前端添加必要 origin，不开放到公网。

导入 `workflows/api/` 中所需工作流，先检查节点 schema、模型枚举和输入文件，再做小预览。8GB GPU 一次只运行一个生成任务。记录真实任务 ID，以终态、可解码产物和实际画面/试听验收；预检成功、安装成功或进程退出 0 都不独立证明创作质量。VoiceDesign、IndexTTS 和 ACE 需从首次推理验收开始，不沿用其他型号的成功结论。

配套 Skills 的目录说明见其随附文档。安装到宿主技能目录前检查同名冲突；不要覆盖宿主已有个人技能，也不要将宿主 token、MCP 登录配置或会话数据库带进仓库。
