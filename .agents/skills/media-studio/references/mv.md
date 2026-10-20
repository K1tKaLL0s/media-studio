# 歌词 PV/MV

workflows/api/mv.json 调用 MediaStudioMV，渲染已经准备好的项目。它不负责写歌、唱歌、把任意视频一键换人，也不自动分析新歌曲并生成新分镜。原样 demo 验证通过只能证明渲染链可运行。

API JSON 的节点 1 为 MediaStudioMV，inputs 为 project_name、quality（preview/final）、filename_prefix、timeout_seconds。project_name 是工作区 projects 内的项目名，不能传工作区外路径；初始项目 pv-demo。quality 选择原有渲染器的半分辨率预览或正式输出；节点固定单 worker，并生成独立任务名。每次显式调用都重新渲染，先查已有任务结果再重试，不能用重复提交代替等待。

固定模板：runtime/vocaloid-style-mv-pipeline，作者提交 13b380dab077d4c8ea956825c9693c720e0c2b91。首个 pv-demo 保留 engine/core、engine/scenes、engine/timeline.js、tools/render_final.mjs 原样。已有 demo 准备完成时，直接用 mv.json 即可；不要每次调用重新 setup 或覆盖项目。

## 新 MV／从歌曲开始创作

收到“给这首歌做 MV/PV”“从歌曲做歌词动画”等新项目请求时，先完整读取已安装的[作者 SKILL.md](../../../../upstream/vocaloid-style-mv/skills/vocaloid-style-mv/SKILL.md)，再读其 [01-workflow.md](../../../../upstream/vocaloid-style-mv/skills/vocaloid-style-mv/references/01-workflow.md)。它们是创作方法与阶段验收的原文；不能只写 brief 后直接调用 mv.json，也不能把本文摘要代替原文。以下引用均为该固定作者版本的本地文件，进入相应阶段时读取对应全文。

新项目使用 projects 下独立目录，保留用户音轨、官方歌词／LRC、来源和署名原文；不改 pv-demo，也不直接修改 runtime 内作者模板。先检查已有材料，缺少会改变创作的音轨、歌词、署名或方向才提出最小问题；已问未答时记录“待答问题—暂停范围—恢复条件”，暂停依赖分支。概念、角色主参考、首帧和首个完整预览要展示给用户；若已请求选择，就等待真实回答，不能用作者“可自行选择”的建议覆盖该等待。

按作者真实阶段推进：

| 顺序 | 进入阶段时读的原文 | 本项目应形成的结果 |
| --- | --- | --- |
| 1. 建立项目与歌曲分析 | 已读 01；再读 [03-audio-and-lyrics.md](../../../../upstream/vocaloid-style-mv/skills/vocaloid-style-mv/references/03-audio-and-lyrics.md) | 从 scripts/new_project.py 建立独立项目；用专用分析环境准备 audio/song.wav、analysis/audio.json、节拍／小节、人工听校的 sections.json、envelope_30fps.json 和 lyrics_mv.lrc。有准确 LRC 就复用；无时序才对齐，歌词文字以用户提供的官方原文为准，不能用 ASR 猜词覆盖它。 |
| 2. 从歌词确定概念 | [02-creative-direction.md](../../../../upstream/vocaloid-style-mv/skills/vocaloid-style-mv/references/02-creative-direction.md) | docs/CONCEPT.md：主题、情绪弧、分段配色、意象、角色与关键时刻。先展示概念再做角色素材；白昼／海边等明亮片必须读其中 §13，调整夜景默认字色、泛光和色调，不套用 demo 的夜景。 |
| 3. 角色与素材 | [04-asset-generation.md](../../../../upstream/vocaloid-style-mv/skills/vocaloid-style-mv/references/04-asset-generation.md)，并按需读本平台 [image.md](image.md) | docs/CHARACTER.md、共享风格描述、主参考候选接触表与 assets/char/REF_master.png；后续姿态固定同一主参考，背景／道具服从分镜。优先调用本平台已验收的本地图片工作流，逐张看图和检查透明边缘。 |
| 4. 分镜与时间轴 | 回读 01 的 Storyboard；读 [05-engine.md](../../../../upstream/vocaloid-style-mv/skills/vocaloid-style-mv/references/05-engine.md)、[06-jizura.md](../../../../upstream/vocaloid-style-mv/skills/vocaloid-style-mv/references/06-jizura.md) | docs/STORYBOARD.md 逐镜头对应时间、歌词、场景和动作，再编写该项目 engine/timeline.js。剪切使用 audio.json 的真实节拍／小节，不能按固定 BPM 猜全曲；为每镜头指定歌词 plan、转场和后期。 |
| 5. 制作镜头与字面 | 继续按 05、06 查实际场景 API／歌词方案 | 优先复用已有 scene，再为歌曲关键时刻改写独立 scene；动画是歌曲时间 t 的纯函数，随机数固定种子。先抽每镜头中点与转场关键帧，避免先渲染整片才发现布局问题。 |
| 6. 复核与交付 | [09-qa-and-lessons.md](../../../../upstream/vocaloid-style-mv/skills/vocaloid-style-mv/references/09-qa-and-lessons.md)，再读 [08-render-and-delivery.md](../../../../upstream/vocaloid-style-mv/skills/vocaloid-style-mv/references/08-render-and-delivery.md) | 逐镜头静帧、运动处密集抽帧、完整预览与试听、错段返工，再输出所需画幅与编码；检查无 demo 残留标题／署名。9:16 是重新布局，只有需要该交付时才做。 |

需要具体动效配方时才读 [effect-cookbook.md](../../../../upstream/vocaloid-style-mv/skills/vocaloid-style-mv/references/effect-cookbook.md)；只有选择了已授权且本机具备的 3D 镜头时才读 [07-blender-3d.md](../../../../upstream/vocaloid-style-mv/skills/vocaloid-style-mv/references/07-blender-3d.md)。不为补齐作者的可选路线自动安装 Blender、对齐依赖、模型或插件。作者 04 中的 tools/imagegen.py／Codex 原生图片示例、并发数量，以及 08 的上传命令都不是当前本地调用授权；收费云端生成、Partner/API 或外传素材须先确认。8GB GPU 仍只运行一个生成任务。

新项目会保留或修改程序文件：正式规划／写入这些文件前先读用户宿主与当前项目的代码执行规则，并交付该项目的机械执行书；涉及前端／时间轴 UI 代码时，使用已覆盖本次工作的实施模型、子代理与分工决定，未覆盖则先取得用户决定，不重复询问已明确授权的事项。作者原文的 scaffold／setup 命令不能绕过这些要求或 N 盘环境隔离；原样 demo 验收仍保持原模板。

创作 brief 用具体信息：歌曲时长与段落、核心情绪／叙事、固定角色外观、画幅、歌词文字与出现方式、关键节拍上的镜头动作。例如：“已有歌曲和 LRC；横屏。角色为短黑发、青绿色外套的原创信使。主歌用静态雨巷和少量萤火，副歌在落拍处切近景；歌词保持可读并避开人物脸。尾音结束后留两秒标题余像。” 这份 brief 只作为上述创作阶段的输入。

本平台 MediaStudioMV 节点只提供“准备后渲染”。新歌项目还没有 analysis/audio.json、已接受的分镜和匹配时间轴时，先按原文完成创作准备，不能把上传歌曲等同于已完成编排。

程序路线：新项目从作者 new_project.py 建立；专用 pv-venv 做分析，现成 Playwright/Edge+WebGL2 绘图，FFmpeg 编码。节点调用现有 render_final.mjs，参数为 --name 独立任务名 --workers 1，preview 时再加 --preview。不得从提示词生成任意 shell 命令。

先看均匀抽帧和主副歌/停拍/尾卡等关键帧，再看完整预览：歌词正确、行分割自然、字号可读、不遮挡脸、换镜跟节拍、角色与配色连续、无黑帧或漏素材。只返工错误镜头/歌词段，再渲染正式版。不要因一处错字重新生成全部角色素材。

demo 音频为 24 秒、48kHz、双声道；成片尾卡会超出歌曲，实际时长按 music_cut+2 秒和 stats.frames/fps 检查。正式版期望 1920×1080、30fps、H.264/AAC；预览约 960×540。以 ffprobe 帧数、stats 及实际播放共同验收。节点的原生 VIDEO 预览和 output/mv 成片应对应同一个任务；同卷硬链接可能只是同一份文件的两个入口，不重复计存储。

依据：[作者模板与命令](https://github.com/EGSECDA/vocaloid-style-mv-pipeline/tree/13b380dab077d4c8ea956825c9693c720e0c2b91/skills/vocaloid-style-mv)。模型图片、短视频和 TTS 可独立给 MV 提供素材，单独渲染 MV 时不自动触发这些生成器。
