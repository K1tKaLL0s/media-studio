# 来源与许可

这里只记录本项目已有的固定来源，第三方运行环境与模型权重均未打包。每个软件、模型、字体和素材分别遵守其原有条款；公开仓库不改变这些条款，也没有新增覆盖全部文件的开源许可证。

## 软件与技能

| 项目 | 固定来源 | 已有许可与范围 |
| --- | --- | --- |
| ComfyUI 0.42.1 | [comfyanonymous/ComfyUI @ 63be2f9b82ad0dac88a7ceaa28a9cf3154125a18](https://github.com/comfyanonymous/ComfyUI/tree/63be2f9b82ad0dac88a7ceaa28a9cf3154125a18) | 上游 GPL v3；主程序另取 |
| Qwen3-TTS 0.1.1 | [Qwen/Qwen3-TTS @ 022e286b98fbec7e1e916cb940cdf532cd9f488e](https://github.com/Qwen/Qwen3-TTS/tree/022e286b98fbec7e1e916cb940cdf532cd9f488e) | Apache-2.0；主程序另取 |
| IndexTTS 2.5 入口 | [index-tts/index-tts @ d9e41aac89fd00b3d71497fddb287b7f24613712](https://github.com/index-tts/index-tts/tree/d9e41aac89fd00b3d71497fddb287b7f24613712) | bilibili Model Use License Agreement；保留其专有条件，不等同于 MIT/Apache |
| ACE-Step 1.5 | [ace-step/ACE-Step-1.5 @ ca1e85fe9430179831e6bc6be790c332190a3866](https://github.com/ace-step/ACE-Step-1.5/tree/ca1e85fe9430179831e6bc6be790c332190a3866) | 上游 MIT；主程序另取 |
| Vocaloid-style MV pipeline | [EGSECDA/vocaloid-style-mv-pipeline @ 13b380dab077d4c8ea956825c9693c720e0c2b91](https://github.com/EGSECDA/vocaloid-style-mv-pipeline/tree/13b380dab077d4c8ea956825c9693c720e0c2b91) | MIT，© 2026 NikusonP；`upstream/vocaloid-style-mv/` 仅保留 Skill、references 与许可，完整模板另取，不复制作者示例歌曲、歌词和影像 |
| JIZURA | [852wa/JIZURA @ fc16bfe43ea4a6c25a21f1caf04d17326de14f00](https://github.com/852wa/JIZURA/tree/fc16bfe43ea4a6c25a21f1caf04d17326de14f00) | MIT，© 2026 hakoniwa；另取并构建 |
| 11 项创作 media-* Skills | 项目原有 `creative-skills` 来源与 manifest、对应 `.agents/skills` | 原包已有 MIT，© 2026 Media Skills contributors；适用范围以原 LICENSE 和 THIRD-PARTY-NOTICES 为准 |
| media-studio 执行 Skill、自有适配器与网页 | 本项目源码 | 本次发布没有为其新增许可证；不要把创作技能包的 MIT 扩展套用到全部项目 |
| ffmpeg/ffprobe | 官方来源的 9.0.2 构建；二进制另取 | 具体 LGPL/GPL 条款取决于所选构建与编译选项，保留构建随附许可 |

源版本、存档摘要、模型来源和许可证据保留在 `config/` 中。原安装记录中的目录路径仅说明当时如何部署；公开副本的实际依赖仍需从这些固定来源取得。

## 模型

`config/models.json`、`config/models-tts.json` 与 `config/models-additions-20261020.json` 逐文件记录模型仓库、revision、目标路径、大小和可用摘要。许可文本与来源说明位于 `config/licenses/`。不要将工作流兼容性或下载成功当作许可结论。

| 模型类别 | 需要保留的区别 |
| --- | --- |
| Anima | 原清单记录 CircleStone Labs Non-Commercial License；模型使用范围与生成图像权利有区别，按所存许可全文核对 |
| FLUX.2 Klein、Wan、Qwen 和文本编码器 | 各模型仓库及其上游的许可分别适用；Comfy 重打包仓库 README 不能替代上游权利条款 |
| Qwen VoiceDesign、Qwen embedding | 固定来源声明 Apache-2.0；embedding 的来源证据说明未发现独立 LICENSE，保留 README/metadata 的公共出处和摘要（原文件未打包） |
| IndexTTS 及辅助模型 | IndexTTS 自有条款与 w2v-bert、campplus、BigVGAN 等辅助模型条款分别适用 |
| ACE-Step 及语言模型 | 依据清单中的各自固定仓库声明核对，不把主程序 MIT 自动套用到每项权重 |

本仓库不含上述权重，因此没有以 Git LFS、下载中转或其他方式重新分发模型。模型下载工具只提供校验机制。

## 私人材料与署名

生成图像、音视频、参考声线、私人提示、工程资产、日志、登录配置和用户数据均不属于本次公开内容。将来添加演示材料时，需独立确认歌曲、歌词、字体、图片、音色与角色材料的公开权利，并保留相应署名和来源。
