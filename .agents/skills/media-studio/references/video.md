# 短视频

使用 Wan2.2 TI2V-5B。workflows/api/video.json 为文生视频；video-i2v.json 为参考图生视频。Wan 的生成结果是画面短片；声音、字幕、完整 MV 合成是单独步骤，不能默认已经包含。

| 字段 | video.json 的 API 绑定 |
| --- | --- |
| 正/负提示词 | 4.inputs.text / 5.inputs.text |
| 尺寸及帧数 | 6.inputs.width / height / length |
| 种子、步数、CFG | 8.inputs.seed / steps / cfg |
| 输出帧率 | 10.inputs.fps |
| 输出名前缀 | 11.inputs.filename_prefix |
| 参考图变体 | video-i2v.json 的 12.inputs.image；6.inputs.start_image 已连接该节点 |

当前固定 Wan2.2 TI2V-5B 组合优先使用官方画幅 1280×704 或 704×1280。本机 512×288 的生成曾出现严重彩条；1280×704、17 帧经分块解码已可辨纸船与池塘，但仍有曝光/斑驳瑕疵，不应继续把小画幅写成固定省内存起点。先用 17 帧、24fps、20 步、CFG=5、单任务验证；17 帧仅约 0.71 秒，不能交成数秒镜头。帧数按 4n+1 增加（例如 49、81、121），目标时长用帧数/帧率核算。保持 VAEDecodeTiled 的 256/64/16/8 和本机已验收加载路径，按真实 Available、系统提交余量与任务压力串行提升；本段不宣称较长镜头或图生内容已经验收，也不承诺 720p 长片速度。参考图会按目标画幅居中缩放裁切，先核对主体构图。

提示词按“主体与外观＋唯一主要动作＋环境变化＋镜头动作”写成一段，避免在一个短片里要求多个场景和跳切。例如：A small paper boat floats slowly from left to right across a shallow puddle on a quiet stone street. Gentle ripples follow the boat; warm morning reflections remain stable. Locked-off camera at puddle level, one continuous shot, natural slow motion.

负提示词只针对实际风险，可从 flicker, warped objects, duplicated subject, sudden scene cut, unstable background, unreadable text 起步；不要堆成长篇。图生视频已由参考图决定外观时，重点写动作和镜头，不重复一段与原图冲突的外观描述。

长片按镜头保存独立 job、源图和种子，先审静帧再审运动。同一人物固定母图、服装与光线描述，必要时用前一镜头已接受的末帧作下一镜头参考；这是连续性办法，不保证身份绝对不漂移。先验收每个镜头，再送 MV/FFmpeg 合成；不要用插帧或重复帧冒充新生成的长镜头。

ffprobe 核对帧数、尺寸、fps、时长；查看首/中/末及均匀抽帧，再播放检查动作是否发生、主体是否变形、背景闪烁、镜头是否突然跳变。解码成功不等于语义成功。保存可复现的工作流与种子；只对失败镜头改一项提示，或在已确认的画幅内降低帧数后重试；新画幅要单独验证，不盲目缩小尺寸循环重提。

依据：[Wan2.2 原生工作流](https://docs.comfy.org/tutorials/video/wan/wan2_2)。模型支持本地卸载运行不代表本机已完成质量或性能验收。
