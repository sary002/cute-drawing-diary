# 公开仓库与内容规则

本项目用于分享可跟画的可爱马克笔教案。所有受Git跟踪的内容都可能被任何人查看、复制和下载。

## 隐私与公开内容

**不要在公开文件中写入个人相关信息。** 此规则覆盖README、教案、配置、工具档案、作品记录、调研、skill、提示词、文件名、图片和提交说明。

- 不写真实姓名、私人昵称、电话、私人邮箱、家庭或工作地址、证件信息、其他平台账号及可关联身份的资料。
- 不写个人经历、生活安排、工作背景、健康或家庭情况；不复制聊天原文、个人偏好调查或私下授权经过。
- 不写带用户名的本机绝对路径、设备名称、个人目录结构和本机安装状态；示例使用相对路径或通用占位符。
- 不提交密码、令牌、Cookie、会话信息、私钥、登录二维码、订单、支付记录或购物截图。
- 不公开未处理的原始照片。先检查人脸、门牌、屏幕、快递单等背景，以及定位等元数据；公开副本还须有明确授权和素材许可。
- 教学只保留必要的纸张尺寸、工具规格、色号、造型方法，以及不含身份信息的作品编号和练习状态。用公共教程的口吻，不把个人聊天背景带入正文。
- 项目链接、第三方来源与许可要求的公开署名按必要范围保留，不据此补充或关联个人资料。

私人笔记和本机设置放在仓库外，或被忽略的.local/中；原始练习照片可放在被忽略的entries/对应作品/practice/private/中。忽略规则不会自动移除已经跟踪的文件，提交前仍需检查暂存内容。

代码、脚本、配置与skill采用MIT，原创学习内容采用CC BY 4.0；第三方与AI素材范围见[许可说明](licensing.md)。

## 导航维护

学习入口是：**[首页](../README.md) → [每日一练总目录](../lessons/README.md) → [入门版练习](../lessons/beginner/README.md) → 当日完整教案**。首页也提供具体教案的直达链接。

新增完整教案时同步更新首页、总目录与阶段目录。草稿和未来选题明确标注，不生成空链接，也不列为可跟画教程。每幅只维护一篇正文，图片通过相对路径直接显示在文档里。

## 同步范围

在当前用户明确授权后，按“校验 → 检查暂存内容 → 提交 → 推送”同步本项目及已确认的远程。普通更新沿用会话中已有的明确授权；克隆仓库及其配置不代表获得其他用户的授权。

只提交本项目所需内容，排除个人资料、其他任务产物、原始私有照片、缓存和凭据。公开GitHub与向其他平台发帖分别处理，不从仓库同步推导平台发布授权。

## 可选本地命令

日常跟画只需打开教案，不必运行命令。维护项目时使用Python 3.10+，无需第三方依赖：

```sh
python3 scripts/drawing_diary.py status
python3 scripts/drawing_diary.py next
# 仅在实际完成后登记；照片、日期、用时与反馈均可省略
python3 scripts/drawing_diary.py record 001-chick
# 日后补一张成品照，原件默认私有；不改写原完成记录
python3 scripts/drawing_diary.py add-photo 001-chick --photo .local/my-chick.jpg
python3 scripts/drawing_diary.py index
python3 scripts/drawing_diary.py validate
```

record的可选参数有--date、--minutes、--liked、--improve。entry.json是公开文件，反馈只写不含身份信息的绘画问题；私人笔记另存本地。计划用时不能当作实际用时，没有确认完成就保持原状态。

提交前检查：

```sh
python3 scripts/drawing_diary.py validate
python3 -m unittest discover -s tests -v
git status --short
git diff
# 只暂存检查过的本次文件，再查看实际将公开的内容
git add <本次要同步的文件>
git diff --cached
# 已获当前用户授权后执行
git commit -m "Describe the drawing diary update"
git push
```

发现个人信息时先从本次变更中移除或脱敏，再提交。若涉及已推送的内容，不擅自强推或改写历史；说明具体受影响范围后处理。
