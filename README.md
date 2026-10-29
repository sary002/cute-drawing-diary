# 每天画点可爱的

每天约20分钟，用现有马克笔从简单小动物开始。**当前优先安心学画：不边画边拍，不要求每天发帖。**

学习流程v0.2。首幅小鸡教程已备好。

开源仓库：[sary002/cute-drawing-diary](https://github.com/sary002/cute-drawing-diary)。代码与skill使用[MIT](LICENSE)，原创学习内容使用[CC BY 4.0](LICENSE-CONTENT.md)；AI参考与第三方内容的适用范围见[许可与来源](docs/licensing.md)。

![AI生成的小鸡练习参考](entries/beginner/001-chick/reference/finished.png)

上图为AI生成的教学参考。

## 每天只需要这样

1. 说“今天画什么”，拿到 [小鸡教程](entries/beginner/001-chick/lesson.md) 这样的一份简单画法和准确色号。
2. 专心画约20分钟，期间不用拍过程，不需要计时。
3. 想记录时说“画完了”即可。照片、用时、感受都可省略；可以重复练同一幅。

以后想整理时，一次拍几张成品或一张合照就够了，也可以暂时不拍。想发小红书时再整理单张成品或合集。照片与发布不影响完成学习。

当前工具：[36色工具档案](config/tools/touchmark-student-36-v1.json)；16.5×16.5cm马克笔纸，铅笔，0.15/0.5/1.0mm针管笔和粗勾线笔。笔头、实际色卡、针管笔耐酒精性待实测。

## 项目积累什么

先积累教案、准确色号、阶段和工具快照、AI参考来源与可选的完成记录。手绘照片日后补充，保留原始记录；不要求为了归档重新画、补拍过程或写每日文案。

[轻量每日流程](docs/workflow.md) · [阶段设置](config/stages.json) · [首轮7幅](curriculum/beginner.json) · [开源参考项目](research/open-source-references-2026-10-29.md) · [历史小红书调研](research/xiaohongshu-2026-10-29.md) · [可选分享](docs/xiaohongshu-template.md) · [Skill](skills/daily-cute-drawing/SKILL.md) · [公开仓库准备](docs/public-repository.md)

阶段与工具版本分开：36色也能进阶。新工具创建新版本，旧作品保留原配置。不以购买、拍照、发帖或连续天数作为升级条件。

## 可选本地命令

日常可以只通过对话推进，不用运行命令。以下只供维护项目时使用，Python 3.10+，无第三方依赖：

```sh
python3 scripts/drawing_diary.py status
python3 scripts/drawing_diary.py next
# 仅在确实画完后运行；没有日期、照片、用时也能登记
python3 scripts/drawing_diary.py record 001-chick
# 日后可为已完成作品补一张成品照，不改变完成记录
python3 scripts/drawing_diary.py add-photo 001-chick --photo /path/to/my-chick.jpg
python3 scripts/drawing_diary.py index
python3 scripts/drawing_diary.py validate
```

已知真实日期、用时或反馈时，record可加--date、--minutes、--liked、--improve。照片原件默认放被忽略的practice/private/，不会自动发布；想公开时另存检查后的副本。


维护后验证：`python3 -m unittest discover -s tests -v`。

[作品索引](entries/INDEX.md)：练习完成、照片归档和发布分别记录。
