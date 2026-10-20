# 视频模型档案

查验日期：2026-10-20。重点是本机Wan。云端是未接入的有限档案，示例仅示意请求形状，未执行，不代表权限、计费或效果验证。

## 本地 Wan2.2 TI2V-5B

同一权重支持T2V/I2V，基础入口video.json与video-i2v.json。不是Wan全部版本的统称，也不是S2V-14B。当前图只接首帧，无尾帧、多参考、声音或精确动作轨迹控制。
Comfy教程说5B可用原生卸载适配8GB；这是官方适配陈述，不等于本机所有分辨率/时长均已实跑。

| 本地任务副本输入 | 现行值/含义 |
| --- | --- |
| 4.inputs.text / 5.inputs.text | 正提示 / 负条件 |
| 6.inputs.width/height/length | 基础T2V 1280×704、I2V 704×1280 / 17帧 |
| 8.inputs.seed/steps/cfg | 种子 / 20步 / CFG5 |
| 7.inputs.shift | 8，当前图约定 |
| 10.inputs.fps | 24，封装播放帧率 |
| I2V另填12.inputs.image | 已上传且真实存在的首帧名字 |

2026-10-20只读回查N盘API：另有workflows/api/video-quality-49.json（1280×704）与video-i2v-quality-official.json（704×1280），均49帧、20步、CFG5、shift8、24fps；后者当前示例图为REPLACE_WITH_UPLOADED_IMAGE.png（待用户上传的首帧占位），实际任务仍应上传用户自己的图。主进程报告这两个配置终态成功、时长2.0417秒，耗时约3391/4198秒；本代理未重放GPU或代替主进程看过成片。技术成功不代表完整眨眼、全部动作和所有质量项通过。
优先使用已验官方画幅。旧E暂存的512×288曾生成严重彩条，不能再当通用省显存起点；只降低尺寸可能改变模型表现。
尺寸约束为32倍数、帧数4n+1。17/24≈0.708秒，49/24≈2.0417秒。目标5秒可推算121帧≈5.04秒；精确5.000秒可后期裁1帧并记录。121帧合法不证明8GB显存、速度或时序质量通过，不能用17或49帧冒充5秒交付。
上游Wan5B配置默认50步、shift5、CFG5、121帧/24fps；当前Comfy小预览20步/shift8并非同一“官方默认”。不要混改采样体系或用家族其他模型参数替代。

I2V正例：
~~~
The character stands on the shoreline. A gentle breeze moves the hair tips and coat hem; small waves advance behind the character. The camera slowly dollies closer from a medium shot. The character keeps the same face, clothing and pose. One continuous shot with restrained movement.
~~~

可选短负条件：abrupt cuts, warped face, duplicated limbs, flicker。只针对实际目标；若要锁定相机就不加入camera movement等与需求相冲的排除词。
反例：17帧要求跑步、转身、起飞、绕拍与两句对白；把“5 seconds, music”写入正提示就称时长/音轨已实现；把Anima CFG1套入Wan。

T2V需补主体、场景、光线和构图；I2V主要补运动但保留关键身份约束。先改成海边首帧再动画，通常比让原图同时换景、转身、变装与运镜更容易验收；这是创作判断，不是已实测成功率。
实际执行读取当前media-studio、presets与完整API；先替换占位输入。上游prompt扩写有DashScope/本地Qwen路线，当前工作流未启用，不能自动外传或加装。

依据：[Comfy原生5B教程](https://docs.comfy.org/tutorials/video/wan/wan2_2)、[Wan仓库](https://github.com/Wan-Video/Wan2.2)、[TI2V函数](https://github.com/Wan-Video/Wan2.2/blob/main/wan/textimage2video.py)、[5B配置](https://github.com/Wan-Video/Wan2.2/blob/main/wan/configs/wan_ti2v_5B.py)。
权重来源：[Comfy重打包](https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged)，固定revision ee6f4a40737a995bf5818954cfce6d59443b0f04；精确下载及校验以工作区config/models.json为准。

## 有限云端比较

| 具体入口 | 时长/参考/音频 | negative与CFG |
| --- | --- | --- |
| Runway gen4.5 API | 2–10整数秒；I2V首帧，T2V另一个端点 | 此分支未列negative/CFG/audio字段，不承诺原生有声 |
| Google Cloud veo-3.1-generate-001 | Cloud文档支持T2V、首尾帧及声音能力，字段按该入口核对 | 教程列negativePrompt，不借Comfy CFG |
| Gemini veo-3.1-*-preview | 文档列4/6/8秒及原生音频；将2026-10-22停用 | 不把Cloud或Runway字段跨传 |
| Kling4.0网页 | 3–30秒，素材角色、事件/音频；Omni与Keyframes入口不可混合 | 指南建议少用否定；4.0 API未核实 |
| Sora2 / sora-2-pro | Videos API已2026-09-24关闭 | 只保留历史导演方法，不构造当前执行请求 |

### Runway gen4.5

I2V提示集中写动作、环境运动、镜头方向和速度；T2V还要交代画面状态。不要无谓复述首帧并引入不同外观。以少量明确动作起步，按输出返工。
当前OpenAPI的gen4.5分支：I2V需要promptImage，T2V没有它；duration为2–10整数。官方quickstart有“从image_to_video省略图做T2V”的示例，与机器schema冲突，本档选择明确的两个端点，不假定省图通过。

未执行I2V示例：
~~~
POST /v1/image_to_video
X-Runway-Version: 2024-11-06
{
  "model": "gen4.5",
  "promptImage": "https://example.com/authorized-character.png",
  "promptText": "A gentle breeze moves the hair tips and coat hem. A slow, steady push-in. The character holds the pose.",
  "ratio": "1280:720",
  "duration": 5
}
~~~

T2V改/v1/text_to_video并删除promptImage。I2V目前首帧最多1张；不能把同服务Veo的首尾帧、negativePrompt或audio字段加到gen4.5。
依据：[官方OpenAPI](https://docs.dev.runwayml.com/openapi.json)、[T2V讲解](https://help.runwayml.com/hc/en-us/articles/42460036199443-Text-to-Video-Prompting-Guide)、[I2V讲解](https://help.runwayml.com/hc/en-us/articles/48324313115155-Image-to-Video-Prompting-Guide)、[通用迭代讲解](https://help.runwayml.com/hc/en-us/articles/46182941379347-Introduction-to-Prompting)、[有冲突的quickstart](https://docs.dev.runwayml.com/guides/using-the-api/)。

### Veo的服务区别

Gemini API的3.1 preview停用日是2026-10-22；Google Cloud教程另列veo-3.1-generate-001，不能据前者判定所有Veo关闭。选定服务后重新核对模型与账户地区可用性。
Cloud教程列negativePrompt，语义为要排除的内容；尺寸、时长、声音字段依该服务模型schema，不能直接搬Gemini SDK或Runway ratio/audio写法。

Cloud教程字段子集（未执行，不是完整schema）：
~~~
POST .../publishers/google/models/veo-3.1-generate-001:predictLongRunning
{
  "instances": [{"prompt": "A paper boat drifts across a still pond. Slow lateral tracking. Quiet ripples and distant birds; no dialogue."}],
  "parameters": {"sampleCount": 1, "aspectRatio": "16:9", "negativePrompt": "abrupt cuts, subtitles"}
}
~~~

提示将视觉动作与音频分开写；特定角色的对白清楚归属且长度与镜头相容。声音能力不保证逐字口型或可用于现有本地Wan。
依据：[Cloud文字生成](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/generate-videos-from-text)、[Cloud首尾帧](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/generate-videos-from-first-and-last-frames)、[Gemini Veo指南](https://ai.google.dev/gemini-api/docs/veo?hl=en)、[Gemini停用清单](https://ai.google.dev/gemini-api/docs/deprecations?hl=en)。

### Kling4.0网页

2026-10-14官方指南把入口分为Omni Reference与Keyframes。用真实绑定的@Image1等编号说明身份、场景或动作角色，再写事件和音频；编号不是已上传的文件。
本档只确认网页3–30秒与有声创作说明，不虚构kling-v4、请求字段或端点。本次公开API可检索正文仍以3.0/Omni为题，旧版negative_prompt/mode/sound与新版settings也不同。
指南正文HDR写coming soon，表格又写支持，因此不承诺HDR现成可交付。

网页自写例：
~~~
@Image1 supplies the character identity and clothing. Keep the face structure, hair and navy coat.
0–3 s: The character stands on a quiet shore; a breeze moves only the hair tips and coat hem.
3–5 s: A restrained push-in reveals small waves behind the character.
Audio: soft surf only, no dialogue, no subtitles, no background music.
~~~

具体可见描述优于“高级、有质感”；避免长串否定。官方指南对不需要字幕/音乐有单独提醒，不把“所有否定无效”说成绝对规则。
依据：[Kling4官方讲解](https://kling.ai/quickstart/kling-4-model-user-guide)、[当前公开3.0API页](https://kling.ai/document-api/apiReference/model/textToVideo)、[旧字段页](https://kling.ai/document-api/api/video/3-0-omni/text-to-video/legacy)。动态API页面本次web正文提取受限，搜索索引正文只作接口版本冲突证据。

### Sora历史方法

旧Sora指南把镜头、动作、对白/声音分开，建议可容纳的短对白和逐次小改。这种导演说明可借鉴，时长和角色API不能作为当前接口。
API reference与deprecations明确Videos API / Sora2于2026-09-24关闭；旧guide仍示范16/20秒，而保留reference schema只列4/8/12秒。采用停用结论，不选择任何一组作当前可执行参数。
依据：[停用通知](https://developers.openai.com/api/docs/deprecations)、[关闭的API reference](https://developers.openai.com/api/reference/resources/videos/methods/create)、[历史提示指南](https://developers.openai.com/cookbook/examples/sora/sora2_prompting_guide)。

## 执行与验收

商业云端均未接入、未上传、未获本次支出授权；具体请求审阅与确认后才能调用。不能把本地失败变成自动付费兜底。
看实际视频才判断运动与身份，试听才判断声音；metadata/validate通过或抽样静帧不证明自然、流畅或同步。保留请求、种子、模型、参考、设置、输出及证据范围。
