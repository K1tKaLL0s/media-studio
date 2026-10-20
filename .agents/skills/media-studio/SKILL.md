---
name: media-studio
description: 在本机 N 盘媒体工作台生成和编辑图片、合成或克隆说话音频、生成短视频、渲染歌词 PV/MV，并由 Codex 或 DSH 调用同一批 Comfy 工作流。用于实际创作和返工；普通教程问答、翻唱或歌声合成不自动启动这些生成器。
---

# 本地媒体工作台

本公开源码包不含模型、虚拟环境、缓存或私有生成素材。${MEDIA_STUDIO_ROOT} 表示用户配置的仓库根目录；先按仓库安装说明准备依赖和本地模型，再检查实际服务与工具。下面保留的历史版本和验收记录不证明当前克隆已经安装或在线。

工作区为 MEDIA_STUDIO_ROOT 指定的仓库根目录，服务为 http://127.0.0.1:8188。使用该目录已经安装、验证的工作流与模型；技能文件本身不证明服务、模型或新工具已加载。只运行本次请求需要的模式。

按任务读取一项参考；组合创作时才读取多项：

| 任务 | 参考 |
| --- | --- |
| 二次元立绘、场景、通用图片、参考图编辑 | [image.md](references/image.md) |
| 中文/英文等配音、预置音色、参考音频克隆 | [voice.md](references/voice.md) |
| 文生短片、参考图短片、分镜逐段生成 | [video.md](references/video.md) |
| 已有歌曲与歌词的文字 PV/MV、模板 demo | [mv.md](references/mv.md) |

新歌曲／新 MV 创作先按 mv.md 的阶段路由完整读取本地作者 SKILL.md 与逐项参考，再准备项目；渲染节点只接收准备好的项目。

创作起点在工作区 prompts/presets.json。它是提示词与字段绑定表，不是可以直接提交的 Comfy API 工作流。先读选定的完整 API JSON，再按 bindings 修改本次任务副本；绑定目标为数组时，把同一值同步写入各目标。required_inputs 的 null 是尚未提供的材料，填齐前不能提交。用户明确的角色、文字、风格、种子和参考材料优先于预设。

## 调用与真实结果

1. 核对 config/models.json、workflows/api 中实际文件及本次引用材料。读取当前服务的节点 schema，确认 class_type、输入字段、模型文件与本次工作流一致；缺项就报告缺项，不以同名远程模型替代。输入原件保留，修改副本和任务记录放在 N 盘。
2. 宿主已注册并发现官方本地 comfy-mcp 后，先用 server_info() 核对运行状态、工作区、url 与可能出现的 comfy_target，均须对应本机 127.0.0.1:8188；非本机目标就停止。validate_workflow(workflow_path=本次副本绝对路径) 只有明确返回 valid=true 才算预检通过，缺失或异常不算通过。run_workflow(workflow_path=同一副本, wait=False, confirm_spend=False) 提交，记录真实 prompt_id；它不接受 params/overrides，先按 bindings 修改任务 JSON 副本。以 job(action="status", prompt_id=...) 跟踪，或 job(action="wait", prompt_id=..., timeout_seconds=25) 有界等待；timed_out 只是等待到期，不是任务失败，不能因此重复提交。出错用 job(action="error", prompt_id=...)，取消仅用 job(action="cancel", prompt_id=本任务ID)；查队列用 job(action="queue")，不传 prompt_id。成功后 fetch_outputs(prompt_id=..., out_dir=N盘本次任务目录) 收集。工具未出现在宿主目录里就用下面的 CLI，不伪造调用。
3. 同一块 8GB GPU 每次只运行一个生成任务。先用参考里的小预览，检查后只修改未达标之处。需要换模型时等待当前任务结束并释放驻留模型；语音和 MV 外部 worker 也遵守本机任务互斥。
4. 将 prompt_id、工作流副本、模型版本/哈希记录、提示词、种子、参数、源材料路径和输出位置一起保存。以终态成功和可解码/可播放产物验收；提交成功、退出码、文件名或模型自述都不能独立证明内容正确。

当前控制环境为 comfy-cli 1.22.0、comfy-mcp 0.10.0，已完成独立 stdio initialize/tools/list，实际 39 个工具；这只验证控制协议，不代表后端在线、宿主已加载或媒体生成已通过。宿主注册名为 media-studio-local。实际任务仍以本会话工具 schema 和服务状态为准；server_info 的版本新旧建议不能自动触发更新、切版或安装节点，固定版本保持本项目约定。

参考图片／音频若未进入 Comfy input，可用 upload_file(paths=[源文件绝对路径], overwrite=False)，按返回的实际文件名填写 LoadImage／LoadAudio，不沿用模板占位。只有处理前端格式工作流时才考虑 list_workflow_slots 和 set_workflow_slot：槽地址须取实际返回的 address，结构化 overrides 保留值类型；stdout=True 默认只返回改后内容，必须保存为任务副本才可提交，不能假定原文件已修改。这里已有 API 模板直接按 bindings 修改副本即可。

本地 CLI 备用语法已用上述安装版本的真实 --help 核对。程序固定为 ${MEDIA_STUDIO_ROOT}\runtime\control-venv\Scripts\comfy.exe；不要调用 PATH 上来源不明的同名程序。先按仓库安装说明配置宿主的 mcp_servers.media-studio-local.env，再从实际已激活的同名宿主注册项逐项复用完整进程环境；保留 N 盘 USERPROFILE、APPDATA、LOCALAPPDATA、缓存、TEMP/TMP、代理隔离、遥测禁用等字段。配置缺失就报告缺项，不能只设 COMFY_WHERE 后裸跑。所有调用固定 local，工作目录为上述工作区：

    $env:COMFY_WHERE = 'local'
    & $Comfy --json --where local --skip-prompt validate --workflow $JobWorkflow
    & $Comfy --json --where local --skip-prompt run --workflow $JobWorkflow --no-watch
    & $Comfy --json --where local --skip-prompt jobs status $PromptId

$Comfy、$JobWorkflow、$PromptId 分别是上述程序路径、本次任务 JSON 绝对路径和真实返回 ID。run 默认提交后返回，由本任务跟踪，不重复提交；--workflow 不能与仅供内置默认图的 --prompt／--set 混用。validate 必须检查有效性判定，命令退出成功不等于工作流有效。若已安装版本不支持列出的命令或 --where，报告版本差异，不删掉本地路由参数继续。结果文件默认在本项目 output，按返回历史定位，不猜最新文件就是本次结果。

## 创作与停止边界

先保留用户源材料和需求，再选一个能验收的最小结果。角色跨镜头时固定角色描述、参考图、模型及版本；相同种子只帮助复现，不保证跨模型或跨分辨率身份一致。长音频按句、长视频按镜头分别验收，失败只返工受影响片段。

付费云端、Partner/API 节点或外传材料须先得到对应用户确认，当前默认入口不作自动付费兜底。工作流出现远程调用节点时先停下核对，不能因 --where local 就认定图内所有节点在本地执行。

如果已经向用户提出会改变目标、材料、风格或执行范围的问题，记录“待答问题—暂停范围—恢复条件”，在真实回答、明确撤回或明确授权自主决定前停止依赖它的调用和交付。没有问题待答且任务范围明确时采用合理起点，不额外制造确认。

错误、OOM、超时或取消都保留本次日志和输入；检查该 prompt_id 后再决定重试，避免重复提交。只取消本任务；外部 worker 还要确认其拥有的子进程已退出。不要用丢失音轨、缩短成片、替换模型等方式掩盖失败。

完成时交付可打开的本地成果、对应工作流/参数记录，并用具体画面或试听证据说明达标与欠缺。未实际看过/听过就明确写出验证范围，不称“自然”“一致”或“高质量”。

依据：[Comfy 本地 MCP](https://docs.comfy.org/agent-tools/mcp#local-comfy-mcp-connection)、[官方 CLI](https://docs.comfy.org/comfy-cli/getting-started)。本项目的实际版本与节点定义优先于在线文档示例。
