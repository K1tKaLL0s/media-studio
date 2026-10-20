# 配音与声音克隆

先区分任务：TTS 是把给定文字说出来；声音克隆是让新文字使用参考音色；翻唱/歌声合成还需要旋律、音高和演唱处理，本项目这两个 Qwen 模型不提供翻唱。歌词 MV 的音轨也不会由 PV 渲染器自动创作。不要把唱歌请求改成朗读后称为完成。

| 模式 | 工作流与模型 | 字段合同 |
| --- | --- | --- |
| 预置音色/说话风格 | workflows/api/speech.json；Qwen3-TTS-12Hz-1.7B-CustomVoice | MediaStudioSpeech 为节点 1，SaveAudio 为 2 |
| 参考音频克隆 | workflows/api/speech_clone.json；Qwen3-TTS-12Hz-0.6B-Base | LoadAudio 为 1，MediaStudioSpeech 为 2，SaveAudio 为 3；2.reference_audio 已接 1 |

MediaStudioSpeech 的 inputs：mode=preset 或 clone、text、language、speaker、instruct、reference_audio_path、reference_text、seed、max_new_tokens、timeout_seconds。clone 可经原生 AUDIO 输入 reference_audio 传入，也可用 reference_audio_path；两者择一。工作流的 LoadAudio.audio 要填 Comfy input 中真实文件名。

preset 用 language=Chinese/English 等明确语言（不明确时 Auto），speaker 采用实际支持列表。中文起点 Serena 或 Vivian；英文起点 Ryan 或 Aiden。text 只放实际要说的话，instruct 单独放风格。例如 text：“窗外的雨已经停了。我们沿着河边，慢慢走回家。”，instruct：“用温暖、平静的语气讲述，语速舒缓，句尾自然停顿。” 不把角色设定、括号舞台说明或“请朗读”混进正文。

clone 必须有本次来源明确的参考音频和对应准确转写；选择干净、单人、无伴奏、音量稳定的一小段，不把背景音乐当音色特征。reference_text 是参考音频的原话，text 是新台词。该节点禁止 clone 的 instruct 非空；speaker 也不用于改变克隆音色。缺少材料时先索取并暂停克隆，不借用随机网络样本替用户决定。

先合成一两句核对发音、音色与风格；人名、数字、缩写或多音字先在单独句子测试。长稿按完整句子分段，保留原文顺序、标点和每段编号；各段固定模型、speaker/参考音频及风格。片段边界留自然停顿再拼接，不截断词音。max_new_tokens 默认 1024 是生成上限，不是“目标时长”；未说完时先缩短正文段落，不以裁掉结尾验收。

在 GPU 上串行执行，由后端释放 Comfy 驻留模型并启动独立 tts-venv。不要在 Comfy 主环境临时升级 Transformers。1.7B OOM 时先缩短分段并按已验证卸载方式重试。当前 worker 固定该模型，未提供自动回退或模型切换字段；持续失败时报告 OOM，由主进程先显式配置并验收 0.6B-CustomVoice 才能使用它，而且该版本不支持风格指令，不能假装 instruct 生效。

检查 output/speech 的 PCM16 WAV：可解码、非静音、真实采样率/声道/时长。SaveAudio 的前台预览可能是 FLAC，不能因此误报 WAV 丢失。实际试听逐字核对漏读、重复、尾音、长停顿、背景噪声以及克隆相似性；ASR 只能辅助查字，不能代替音色与自然度试听。没有试听能力时如实记录，保留待试听项。

依据：[Qwen 官方接口与模型](https://github.com/QwenLM/Qwen3-TTS)。本地 worker 使用固定本地模型目录，参考音频和正文不因此自动上传。
