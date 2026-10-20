# 图片生成与编辑

API 文件相对工作区：anime.json、image.json、image-edit.json 均在 workflows/api。先核对节点类型和模型；以下绑定是本项目工作流合同，不适用于随意导入的第三方 JSON。

| 工作流 | 模型与提示词 | 必要绑定 |
| --- | --- | --- |
| anime.json | Anima Turbo v1.1；小写标签、空格分词，可补具体英文叙述 | 正文 4.text；负文 5.text；尺寸 6.width/height；采样 7.seed/steps/cfg/sampler_name/scheduler；输出 9.filename_prefix |
| image.json | FLUX.2 Klein 4B FP8 distilled；完整自然语言描述主体、场景、光线与构图 | 正文 4.text；尺寸 6.width/height；种子 7.noise_seed；9.steps/width/height；10.cfg；输出 13.filename_prefix |
| image-edit.json | 同一 Klein；明确修改对象与保持不变的细节，一次先改一件事 | 正文 4.text；参考图 6.image；7.megapixels；种子 13.noise_seed；15.steps；16.cfg；输出 19.filename_prefix |

表中 A.field 指 API JSON 的节点 A 下 inputs.field。编辑的 image 字段填 Comfy input 已接收的文件名，不能把任意磁盘路径直接当上传文件名。输入材料保留原文件与来源。image.json 的节点 6 与 9 尺寸必须同步。

Anima Turbo 从 512×512 或相近像素量、8 步预览，10–12 步定稿，CFG=1；使用完整 Turbo 权重，不叠加旧 Turbo LoRA。预设采用 euler/simple。CFG=1 时不要依赖负提示词纠错；先把正确形状、人数和服装写进正提示。不要沿用 Base 的高 CFG 与长步数，也不要求模型绘制长段文字。

立绘例：safe, 1girl, solo, original character, full body, short black hair, amber eyes, teal jacket, white shirt, black trousers, simple pale gray background. She stands facing the viewer with both hands relaxed and fully visible. Clean anime linework, flat colors, even soft lighting, enough empty space around the entire silhouette.

Klein distilled 保持 4 步、CFG=1，保留现成 FLUX2Scheduler，不改成通用 KSampler 调度，不添加未连接的 negative_prompt。通用图例：A small teal ceramic mug on a warm oak desk beside a closed cream notebook. Soft morning light enters from the left; an uncluttered background, three-quarter product view, realistic ceramic texture, no lettering.

编辑例：Change only the ceramic mug from white to deep teal. Preserve its exact shape, handle, position, reflections, background objects, camera angle, and lighting. 先做这一个局部变化，合格后再串行修改；不要反复把已经失真的结果作为唯一参考。

检查主体数量、肢体/物件结构、裁切、文字与用户指定细节。编辑需与原图并排看改动及保持项；去背景任务要检查真实 alpha，白底不等于透明。角色系列保留一张已接受的母图和固定外观描述，逐张比较面孔、配色、服装、比例；只改姿态或场景变量。预览通过后再提高尺寸，每次只提高一档，8GB 显存不足时保留预览并降低像素量。

依据：[Anima 模型卡](https://huggingface.co/circlestone-labs/Anima)、[Klein 官方工作流](https://docs.comfy.org/tutorials/flux/flux-2-klein)。预设是本机起点，未声称这些参数在任意显卡上都通过。
