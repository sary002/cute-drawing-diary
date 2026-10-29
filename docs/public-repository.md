# 公开内容与维护

## 隐私规则

所有受Git跟踪的文档、配置、提示词、图片、文件名和提交说明都按公开内容处理。

- 不写个人身份、联系方式、生活背景、聊天记录、设备路径、账号凭据及私下沟通过程。
- 教学保留必要的纸张规格、色号和不含身份信息的作品记录；来源链接、GitHub署名与许可声明正常保留。
- 私人笔记放在仓库外或被忽略的.local/，原始照片放在被忽略的entries/对应作品/practice/private/。已被Git跟踪的文件不受新增忽略规则保护。
- 照片公开前检查背景信息、定位等元数据与素材许可，取得明确公开授权后再使用处理过的副本。
- 提交前检查实际暂存内容；发现个人信息先移除或脱敏。

## 导航与教案

入口为[首页](../README.md) → [每日一练总目录](../lessons/README.md) → 阶段目录 → 当日教案。每篇教案正文只维护一份，图片使用相对路径内嵌。

新增教案完成并标记ready后，同步更新首页、总目录和阶段目录。草稿与未来选题不列为可跟画教程。

## 本地维护

Python 3.10+，无需第三方依赖。以下命令均在项目根目录执行：

```sh
python3 scripts/drawing_diary.py status
python3 scripts/drawing_diary.py next
# 实际画完后可登记；日期、照片、用时与反馈均可省略
python3 scripts/drawing_diary.py record 001-chick
python3 scripts/drawing_diary.py add-photo 001-chick --photo .local/my-chick.jpg
python3 scripts/drawing_diary.py index
python3 scripts/drawing_diary.py validate
python3 -m unittest discover -s tests -v
git diff --cached
```

entry.json是公开文件，只写不含身份信息的绘画反馈，不编造实际用时或完成状态。同步限于当前用户授权的远程和变更范围；重写历史、强制推送及其他平台发布须有对应的明确授权。
