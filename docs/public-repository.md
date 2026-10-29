# 公开仓库与同步

- 仓库名称：cute-drawing-diary
- 所有者：sary002
- 展示名：每天画点可爱的
目标地址：https://github.com/sary002/cute-drawing-diary

本项目公开分享可爱马克笔教案。代码、脚本、配置与skill采用MIT；原创学习内容采用CC BY 4.0，AI和第三方内容的来源范围见[许可说明](licensing.md)。

其他用户克隆后应设置自己的Git远程、config/project.json中的仓库地址和同步偏好；原作者在聊天中给出的同步授权不随克隆继承。

## 同步范围

助手完成本绘画项目的更新后，按“校验 → 提交 → 推送”处理常规同步。只同步本目录及已确认的远程，排除其他聊天产物、购物截图、原始私有照片、缓存和凭据。

用户方便时可以补拍成品或合照；图片原件先放practice/private/，对外副本在用户明确愿意公开后再加入。未来公开本人照片或手绘前，记录贡献者与许可。

公开仓库不等于自动发小红书。平台发帖按单独请求执行；当前没有后台文件监听或定时任务。

## 本地维护

进入本项目目录执行：

```sh
python3 scripts/drawing_diary.py validate
python3 -m unittest discover -s tests -v
git status --short
git add <本次要同步的文件>
git commit -m "Describe the drawing diary update"
git push
```

日常学习可以只在对话中进行，用户无需运行这些命令。首次发布进度以实际远程提交及校验结果为准。
