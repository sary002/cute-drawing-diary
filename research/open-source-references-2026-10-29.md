# 开源参考项目与轻量学习流程｜2026-10-29

## 本轮结论

没有找到可以直接套用、同时覆盖“中文可爱小动物＋Touchmark36色＋20分钟纸笔练习＋轻量归档”的完整项目。更适合借鉴各自的一小部分，保留本项目简单的教案与记录结构。


## 已确认有许可的候选

| 项目 | 核实内容与许可 | 可以借鉴 | 对本阶段的适用边界 |
| --- | --- | --- | --- |
| [Doodle Noodle](https://github.com/ZachD-ae/Doodle_Noodle) | README说明每日题目、画布、个人作品集合；LICENSE为MIT | 一次给一个题目，完成后逐渐形成个人作品集 | 是数字绘画应用，不是纸笔课程；实现含登录、数据库、限时与连续天数，当前只借鉴选题和积累方式 |
| [thumbsup](https://github.com/thumbsup/thumbsup) | README说明从本地照片/视频文件夹生成静态画廊，子目录对应相册；LICENSE.md为MIT | 以后按初级、进阶文件夹整理成品，集中生成画廊 | 是展示工具，不教绘画；需额外运行环境，作品积累后再决定是否采用 |
| [Quick, Draw! Dataset](https://github.com/googlecreativelab/quickdraw-dataset) | README说明345类涂鸦、带笔画信息，数据CC BY 4.0；仓库已归档 | 动物/日常物品题目池，观察少量线条如何表达轮廓 | 属于开放数据，不是系统教学软件；大众速画质量不齐，不能直接当标准范画或马克笔上色课程 |

不用下载整套QuickDraw数据，也不用为每天画画先搭建网站。用现有纸笔与已准备的简单教案就可以开始。

## 适合按问题阅读的中文公开项目

[绘画基础手册 · glenzli/drawing-handbook](https://github.com/glenzli/drawing-handbook) 的README介绍了线条与形状、透视、明暗、色彩等基础模块，以及色轮和构图等交互内容；可按眼前的问题查线条、形状和色彩。它也能为本项目的阶段大纲提供参考。

核查仓库根目录、README、package.json及GitHub许可字段后，未找到明确开源许可证。因此列为公开阅读参考，不把它算作已经确认可复用代码或图片的开源模板。本轮仅核实内容范围，未逐章审校教学质量。

## 已排除的近似结果

[LearningToDraw](https://github.com/Ddaniela13/LearningToDraw) 实际是机器学习论文“Learning to Draw: Emergent Communication through Sketching”的代码，不是教人入门画画的课程。很多搜索结果的drawing也指程序绘图；没有因为名字相似就推荐给用户。

## 对当前项目的实际调整

- 日常只做：看一个简单教程 → 专心画约20分钟 → 想记录时说“画完了”。
- 完成登记无需照片、准确日期、用时或反思，未知信息保留null，不编造。
- 新增add-photo操作：已完成作品以后再补照片，保留当时完成记录与工具快照。
- 用户有空时可一次拍几张成品或一张合照，没有过程图不用补拍。
- 分享时默认单张成品或合集；不要求三页、每日发布或指标回访。
- 每幅题目仍使用现有色号和当前能力阶段，可重复练习或分两天完成。

具体规则见[当前工作流](../docs/workflow.md)，默认行为已同步到[skill](../skills/daily-cute-drawing/SKILL.md)。

## 核实来源

观察日期：2026-10-29。通过GitHub连接器读取官方仓库README、仓库元数据和许可证文件，结合网页检索发现候选；没有按星数推断教学质量或适用性。

- [Doodle Noodle README](https://github.com/ZachD-ae/Doodle_Noodle/blob/main/README.md) 与 [MIT许可](https://github.com/ZachD-ae/Doodle_Noodle/blob/main/LICENSE)
- [thumbsup README](https://github.com/thumbsup/thumbsup/blob/master/README.md) 与 [MIT许可](https://github.com/thumbsup/thumbsup/blob/master/LICENSE.md)
- [QuickDraw README及数据许可](https://github.com/googlecreativelab/quickdraw-dataset/blob/master/README.md#license)
- [绘画基础手册README](https://github.com/glenzli/drawing-handbook/blob/main/README.md)
