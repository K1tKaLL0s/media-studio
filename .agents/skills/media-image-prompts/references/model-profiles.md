# 图片模型档案

查验日期：2026-10-20。只读准备材料，所有例子均为本次自写、未生成测试。下述本地参数来自已保存API，不表示GPU或长任务通过。

## 本地选择与字段

| 精确模型/模式 | 提示与采样边界 | 当前工作流 |
| --- | --- | --- |
| Anima 完整 Turbo v1.1 | 标签可混自然语言；CFG1、8–12步，不叠旧Turbo LoRA | anime.json，T2I |
| FLUX.2 Klein4B distilled FP8 | 4步、CFG1、Flux2Scheduler；连贯场景或编辑指令 | image.json、image-edit.json |

执行根目录为 ${MEDIA_STUDIO_ROOT}。先读当前 prompts/presets.json、完整 workflows/api/*.json，按实际bindings准备副本，不提交本文件中的局部字段表。

| 文件 | 关键输入 |
| --- | --- |
| anime.json | 4.inputs.text；6.inputs.width/height；7.inputs.seed/steps/cfg |
| image.json | 4.inputs.text；6与9的width/height同步；7.inputs.noise_seed；9.inputs.steps；10.inputs.cfg |
| image-edit.json | 4.inputs.text；6.inputs.image；7.inputs.megapixels；13.inputs.noise_seed；15.inputs.steps；16.inputs.cfg |

以上是当前约定的索引，若运行图改变，以实际文件为准。编辑当前只接单张图，约0.25MP参考预算、尺寸取16倍数；它是参考条件编辑，不是可任意设置denoise的普通img2img。

## Anima Turbo v1.1

模型卡支持小写标签、空格代替下划线（score标签例外）及自然语言混合；纯自然语言需要足够明确。Base/Aesthetic/Turbo的不同段落不能混为同一设置。
当前CFG1的负分支默认不参与常规采样，不能承诺负词修手、去文字或去水印。正提示写出人数、姿态、识别点、环境和取景。评分标签不是通用质量标准。
模型定位为插画/二次元，写实和长文字渲染不应当其强项。

正例：
~~~
1girl, solo, original character, silver bob cut, blue eyes, navy coat, standing, seaside, medium shot, three-quarter view, clean lineart, cel shading, safe. A young adult stands on a quiet shore. Her full head and both hands stay inside the frame; the right side is open for later lettering.
~~~

反例：“masterpiece”重复十遍，却没有人数/姿态；用Base的CFG4–5与30–50步跑完整Turbo；为了负提示有效擅自提高CFG。动作、裁切或衣服缺陷先针对正提示返工。

依据：[模型卡](https://huggingface.co/circlestone-labs/Anima)、[Comfy教程](https://docs.comfy.org/tutorials/image/anima/anima)、[CFG1源码](https://github.com/Comfy-Org/ComfyUI/blob/63be2f9b82ad0dac88a7ceaa28a9cf3154125a18/comfy/samplers.py)。
固定权重来源revision：f973fc41ec7545364ac9776c2440285f43ff2a30；实际文件为anima-turbo-v1.1.safetensors。不要仅凭模型卡总标题猜所加载版本。

## FLUX.2 Klein4B distilled FP8

描述主体、动作/姿态、光源方向和软硬、材质与空间关系；Klein官方没有自动prompt扩写。不要把SD式标签堆或MJ尾参数当默认写法。
4B官方示例为guidance_scale=1、4步；FP8仓库指向同一4B模型。Base4B/9B、pro/flex/max的设置不适用于该蒸馏流程。
官方多参考能力与当前单图本地入口分别记录；新增多图不能只在提示里声称已上传。

生图正例：
~~~
A matte ceramic cup sits on a pale stone ledge beside a window. Soft morning light enters from the left, creating a short diffuse shadow. The cup occupies the lower left of a square editorial composition, leaving the upper right clear for typography.
~~~

编辑正例：
~~~
Change only the cup body to deep blue. Preserve the handle shape, rim, glaze texture, viewpoint, stone ledge, background and lighting.
~~~

反例：“make it premium --ar 16:9 negative_prompt=bad quality”。尺寸应设置字段，修改目标应具体。当前CFG1/零负条件不是给用户调负词的入口；文字渲染仍需逐字检查。

依据：[4B官方模型卡](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B)、[官方FP8](https://huggingface.co/black-forest-labs/FLUX.2-klein-4b-fp8)、[Klein提示段](https://docs.bfl.ai/guides/prompting_unified_reference)、[Comfy原生示例](https://docs.comfy.org/tutorials/flux/flux-2-klein)。
FP8固定来源revision：5b4408e59397a4a37ccb46afe426d8ed86379441。FLUX.2官方云端的参考数量、自动扩写与控制字段必须按具体子型号区分。

## 少量云端档案

| 范围 | 已核实控制 | 使用边界 |
| --- | --- | --- |
| GPT Image2.5 Flare / Sunburst | 生图/编辑；size、quality独立；无Images API negative_prompt/CFG/steps字段 | 未接入；不能把Responses主模型名当图像模型 |
| Midjourney V8.2 | --ar/--no/--v等置末尾；V8.X参考编辑用Edit Model | UI/Discord语法，不是HTTP通用schema |
| Niji7 | 专用二次元版本，官方描述更按字面与更清晰线条 | 不把V8.2引用能力自动套给Niji |
| Imagen4 generate-001系列 | 历史T2I；不支持negative/参考编辑 | 已停用资料，不生成当前执行请求 |

### GPT Image2.5

支持质量auto/low/medium/high/xhigh/max，但同标签不保证跨型号相同效果或速度；本档只用普通1024²示例。编辑描述“改什么/保留什么”，多个参考要分配角色。原生排除意图可写自然语言，不能发明negative_prompt。

未执行请求形状：
~~~
POST /v1/images/generations
{
  "model": "gpt-image-2.5-flare",
  "prompt": "A square editorial photograph of a ceramic cup on pale stone. Soft window light from the left. Leave the upper third clear for later lettering.",
  "size": "1024x1024",
  "quality": "medium",
  "output_format": "png"
}
~~~

编辑使用Images edits与真实图像输入，不能只把源图路径塞入上述T2I请求。透明素材还需background=transparent和支持透明的格式，最终检查alpha边缘。
依据：[图像提示指南](https://developers.openai.com/api/docs/guides/image-prompting)、[Images API](https://developers.openai.com/api/reference/resources/images/methods/generate)、[生成/编辑指南](https://developers.openai.com/api/docs/guides/image-generation)。

### Midjourney

可复制的网页/Discord文本示例：
~~~
A silver-haired adult in a navy coat on a quiet shoreline, restrained blue and warm ivory palette, clear silhouette, space for a title --ar 16:9 --v 8.2 --no text watermark
~~~

V8.X用Edit Model附参考；V7的--oref/--ow和V6的--cref/--cw有版本边界。--no也不等于本地Comfy的负节点。没核实官方HTTP接入时不给出第三方/imagine伪API。
依据：[Version](https://docs.midjourney.com/hc/en-us/articles/32199405667853-Version)、[参数](https://docs.midjourney.com/hc/en-us/articles/32859204029709-Parameter-List)、[Omni范围](https://docs.midjourney.com/hc/en-us/articles/36285124473997-Omni-Reference)、[Edit Model说明](https://docs.midjourney.com/hc/en-us/articles/33329329805581-Modifying-Your-Creations)。

### Imagen的停用与字段差异

Gemini Imagen页明确已关闭，deprecations列Imagen4于2026-08-17停用；Cloud Imagen4模型卡另列2026-06-30停用。服务不同，不能把停用日期混为一个。
早期Imagen3可用的negative不适用于imagen-3.0-generate-002及以后；Imagen4也不是imagen-3.0-capability-001的编辑接口。保留历史提示方法，不以残留示例承诺可调用；用户选择新Google模型时另查其当前文档，不自动改名。
依据：[Imagen现状](https://ai.google.dev/gemini-api/docs/imagen?hl=en)、[停用清单](https://ai.google.dev/gemini-api/docs/deprecations?hl=en)、[Cloud模型卡](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/imagen/4-0-generate)、[负提示范围](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/image/omit-content-using-a-negative-prompt?hl=en)。

## 调用与证据边界

本档无云端凭据、上传或支出授权。实际调用前明确服务/精确模型、可用地区、数量与预算、外传材料和用途，确认后才执行；已有明确授权无需重复问。
提示词是创作说明，不是身份锁、质量保证或实际运行证据。生成后逐图检查；保留模型/参数/参考与输出记录。仅看示例、标题、摘要或validate不能证明成片质量。
