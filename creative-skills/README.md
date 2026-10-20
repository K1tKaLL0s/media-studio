# 媒体创作技能

本仓库在 `.agents/skills/` 提供 12 项技能。`media-studio` 衔接本地工作流；另外 11 项负责创作方法、提示词、导演与审美。源码、技能文件和模型清单不代表模型已经安装或服务正在运行；模型、运行环境、缓存及私有素材均须另行准备。

| 技能 | 用途 |
| --- | --- |
| media-director | 多阶段创作总控与交接 |
| media-story | 故事、大纲、剧本与事实型导览 |
| media-storyboard | 文字分镜、漫画分格与 animatic |
| media-directing | 调度、摄影、剪辑与音画关系 |
| media-image-prompts | 图像模型提示与参数适配 |
| media-video-prompts | 单镜运动与视频模型适配 |
| media-voice | 说话表演、授权参考声音与试听检查 |
| media-music | 配乐、歌词、作曲草案和声音剪辑 |
| media-look-realism | 写实光线、空间与材质 |
| media-look-anime | 二次元角色、线色形与一致性 |
| media-look-web | 网页视觉层级与状态辨识 |
| media-studio | 本地媒体工作流执行与产物验收 |

## 使用与手工安装

先阅读仓库根目录的安装说明，设置 `MEDIA_STUDIO_ROOT` 为克隆所在的仓库根目录。技能中的 `${MEDIA_STUDIO_ROOT}` 是该配置的路径占位符；Markdown 不会自动展开环境变量，执行前应以实际配置替换或用 `Join-Path $env:MEDIA_STUDIO_ROOT ...` 取得路径。安装所需软件、模型和服务后，仍须逐次核对真实工具与服务状态。保留原运行工作区，公开源码副本不会自动接管它。

若宿主支持从项目的 `.agents/skills` 发现技能，打开本仓库并刷新技能列表。若需手工安装，只把选定的同名目录复制到宿主的用户技能目录；目标已存在时先比较，不能覆盖已有改稿。例如在 PowerShell 中安装一项：

```powershell
$repo = (Get-Location).Path
$name = 'media-director'
$source = Join-Path $repo ".agents/skills/$name"
$skillsHome = Join-Path $env:USERPROFILE '.codex/skills'
$target = Join-Path $skillsHome $name
if (Test-Path -LiteralPath $target) { throw '技能目录已存在，请先比较后手工处理。' }
New-Item -ItemType Directory -Path $skillsHome -Force | Out-Null
Copy-Item -LiteralPath $source -Destination $target -Recurse
```

保留本仓库的目录结构。手工复制只安装技能文字，不复制它依赖的仓库源码和作者文档；涉及工作流或 MV 时仍应从 MEDIA_STUDIO_ROOT 指定的仓库读取依赖。可明确指定仓库中的 `SKILL.md` 完整路径让代理读取，以便相对链接按仓库内结构解析。安装或文件存在不等于宿主已经发现，也不证明媒体生成验收通过。

MV 方法依赖已随仓库保存的[作者技能](../upstream/vocaloid-style-mv/skills/vocaloid-style-mv/SKILL.md)及其参考；作者模板与渲染源码是否准备好，另按根目录安装说明检查。`frontend-design`、Product Design、Figma 等是按任务选用的外部技能，本仓库不复制它们。

## 许可与来源

这里的[既有 MIT 许可](LICENSE)只覆盖上表前 11 项创作技能及本创作包的原创文字；不由此给独立的 `media-studio` 执行技能或整座仓库新增许可证。该执行技能随用户项目公开，未在本次发布中附加新的许可授权。作者 MV 技能沿用其自己的 [MIT 许可](../upstream/vocaloid-style-mv/LICENSE)和[第三方说明](../upstream/vocaloid-style-mv/THIRD_PARTY_NOTICES.md)。

[第三方来源说明](THIRD-PARTY-NOTICES.md)与 `sources/` 保留公开 URL、固定版本、可用哈希及观察边界。原研究视频、预览帧、网页缓存、宿主状态和本地证据文件不随仓库分发，其原机器路径已经移除。不得把引用来源、作品、声音、字体或模型一并视为 MIT。

`manifest.json` 只列上述 11 项创作技能的当前发布副本文件哈希，不涵盖 `media-studio` 或作者 MV 技能。原机器上的历史检查不能代替当前克隆的安装与内容验收。