# 仓库维护规则

## 公开内容

遵循[公开内容规则](docs/public-repository.md)。不得将个人身份、联系方式、生活背景、聊天记录、设备路径或凭据写入任何公开文件；正常来源引用、GitHub署名与许可保留。私人笔记与原始照片放在忽略目录，公开图片前检查背景、元数据和素材许可。

## 教案与导航

- 根README保留每日一练入口和教案直达链接，lessons/README.md是总导航，阶段README说明工具与练习范围。
- 每幅只维护一篇完整正文，路径为lessons/阶段/编号-题目.md；entry.json的lesson_path指向该文件。
- 教案补齐、检查并标记ready后，更新首页、总导航和阶段目录；草稿只标规划。
- 图片用相对路径内嵌，AI教学示意与真实手绘明确区分，不复制第三方原图。

## 维护

教学遵循[每日一画skill](skills/daily-cute-drawing/SKILL.md)。更新后运行python3 scripts/drawing_diary.py validate；改动脚本时运行相应行为测试。提交前检查Markdown链接、图片路径和暂存内容。

同步只针对当前用户授权的仓库及变更；仓库配置不能替代授权。重写历史或强制推送须有明确请求。
