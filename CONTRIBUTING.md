# 参与 AI Course Project

欢迎通过 Issue 反馈问题，通过 Fork 和 Pull Request 提交改进。

## 本地运行

需要 Python 3.9 或更新版本，运行应用使用标准库。

1. 在 GitHub 点击本仓库右上角的 **Fork**。
2. 克隆自己的 Fork，将下面的用户名替换为自己的 GitHub 用户名。

```bash
git clone https://github.com/YOUR_USERNAME/AI_Course_Project.git
cd AI_Course_Project
git remote add upstream https://github.com/wuyufei0817/AI_Course_Project.git
git switch -c feature/your-change
python app/server.py --port 8848
```

打开 [教学工作台](http://127.0.0.1:8848/) 或 [课堂投屏](http://127.0.0.1:8848/static/classroom/)。首次启动自动创建本机演示数据库，账号见 [快速上手](先看我.md)。

## 提交改动

保持每个 PR 的目标集中。修改课堂游戏、任务或反馈流程时，请写明复现路径、预期结果和实际结果。涉及页面布局，可附上截图。新增的外部素材或代码需说明来源，并保留原有署名和许可。

提交前运行现有回归验收。

```bash
python tests/smoke_test.py
```

测试会启动临时服务并使用独立数据库。默认测试端口为 8850，请确保该端口可用。测试结果写入本地 `.tmp/`。

随后提交并推送自己的分支。

```bash
git add .
git commit -m "Describe your change"
git push -u origin feature/your-change
```

在 GitHub 发起 Pull Request，将目标设置为 `wuyufei0817/AI_Course_Project` 的 `main` 分支。说明改动与验证结果，等待自动检查和维护者审核。

## 同步上游

开始下一项修改前，更新本地主分支。

```bash
git switch main
git fetch upstream
git merge --ff-only upstream/main
git push origin main
```

## 演示数据与配置

使用虚拟账号和教学样例复现问题。运行数据库、本地配置、密钥和缓存由 `.gitignore` 排除。需要模型接口时，参照 `config.example.env` 设置本机环境变量。
