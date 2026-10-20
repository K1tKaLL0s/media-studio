# 按交付层级选择字段

## 无时码文字分镜

可用字段：shot ID、所属场景、镜头作用、主体/环境、景别与视点、起点→变化→终点、角色动作、摄影机动作、对白/声音意图、前后衔接。
选择足够执行的字段；不为简单一镜填写无关摄影参数。

例：S03，女孩伸手递出最后一张车票；中近景侧面；起点握票在胸前→犹豫后递到孩子面前→孩子抬眼；镜头固定，手的动作引导注意；站内广播在画外继续。
它比“忧伤、电影感、慢镜头”更能给出可见事件，也保留表演余地。
若执行工具只做静图，首尾动作应拆成状态参考，不称已生成连续递票动作。

## 漫画分格

可用字段：页/格ID、阅读次序、格大小作用、可见动作、气泡/旁白、格间推断、翻页或视觉落点。
先判断一格呈现什么关键状态，不能在同一状态中要求互斥动作同时发生。
对白气泡的说话人、阅读顺序和指向应清楚。
格宽、留白及翻页可以改变主观阅读节奏，但不等于精确秒数。
改成视频时重新安排动作持续和剪切，不把每格直接指定固定时长。

## 时码表与声音提示

可用字段：shot ID、start、end、duration、frame_start、frame_end_exclusive、画面、对白/环境/效果/音乐cue、转场、time_basis。
frame_end_exclusive表示末帧不含：下一镜可以从前一镜该值开始。
time_basis可写actual_audio、scratch_read或estimate，避免临时数字伪装实测。

例如24fps下：镜头A [0,48)为2秒，B [48,120)为3秒，总长120帧/5秒。
这只演示区间算法；真正驻留时长由表演、信息量、阅读和音源决定，不照抄示例。
有重叠的转场需说明两条画面轨道和重叠长度，总时长按时间轴计算，不能简单相加素材长度。

声音cue可写：对象/音源、画内或画外、进入退出、功能、与画面关系、实际素材/临时占位。
“先听到下一场广播再切画面”是声音先行；“人物离画后留脚步”可保持空间连续。
只有现有素材或实际制作支持时才交付声音文件；文字cue不代表音频已完成。

## 两次不同的检查

静态接触表检查镜头顺序、角色和空间一致性。
按实际速度播放预演，才检查驻留、动作、换气、字幕可读和声音进出。
前者不能替代后者；未听音时不评声音自然度和混音平衡。

## 依据

[ScreenSkills：简单分镜](https://www.screenskills.com/starting-your-career/lesson-plans-and-classroom-resources/simple-storyboards-why-and-how-to-make-them/)：无对白初稿的视觉可读性；不同媒介用途。
[StudioBinder：Storyboard Arrows](https://www.youtube.com/watch?v=3MK9umqHihc)：本轮只观察官方预览约180–220秒的离散画面，可见Dolly In箭头；没有听旁白。
[ScreenSkills：Head of story](https://www.screenskills.com/job-profiles/browse/animation/pre-production/head-of-story/)：通过面板、animatic与修订协调叙事。
