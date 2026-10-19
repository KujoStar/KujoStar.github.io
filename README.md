# NAGISA's Blog

个人学习、教学、科研与生活记录。基于 MkDocs Material，采用暖白深蓝主题、两级书架目录和 Markdown 写作流程。

- 网站：<https://kujostar.github.io/>
- 所有日常修改都在 `docs/` 和 `data/` 中完成。
- `site/` 是构建输出，**不要编辑或提交**。
- `legacy/` 是 Hexo 旧站的完整快照，**不要编辑**，也不会发布到新网站。

## 本地预览

Windows PowerShell（仓库根目录）：

```powershell
# 第一次使用；已有本项目 .venv 时跳过这一行。
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-cache-dir -r requirements.txt
.\.venv\Scripts\python.exe -m mkdocs serve --dev-addr 127.0.0.1:8000
```

打开 <http://127.0.0.1:8000/>。不需要激活环境，不改变系统 Python 或其他 Conda/venv 环境。直接依赖固定版本，不需要 npm 或 node_modules；Node.js 24 仅用于运行搜索测试。当前项目独立环境约 100 MiB。

编辑 Markdown、分类和模板会自动重建。修改 Python 构建代码后，请停止并重新启动预览。

## 新增子类和文章

例如给“助教工作”增加“程序设计”子类，在 `data/site-catalog.yml` 的对应大类下写：

```yaml
  - id: teaching
    name: 助教工作
    description: 教学实践、习题讨论与答疑记录。
    children:
      - id: programming
        name: 程序设计
        description: 课程答疑与习题讨论。
```

然后创建 `docs/blog/teaching/programming/first-note.md`：

````markdown
---
id: teaching-programming-first-note
title: 第一次答疑记录
date: 2026-10-19
description: 本次答疑的主题与关键问题。
tags: [助教, 程序设计]
comments: true
---

## 问题与讨论

这里写正文，支持 $a^2 + b^2 = c^2$、表格、图片和代码。

```python
print("Hello")
```
````

规则：

- `id` 全站唯一，由小写字母、数字和连字符组成。创建后保持不变，评论按它关联。
- 大类和子类的 `id` 决定内容文件夹；中文 `name` 仅影响显示，可以单独改名。
- 普通列表按发布日期倒序，同一天按文章 ID 倒序；需要章节顺序时，在子类加入 `order: [文章ID1, 文章ID2]`，其他文章随后按日期排列。
- `updated` 是可选字段，只在内容实质更新时填写，不早于 `date`。日期按北京时间的日历日期维护。
- `description` 可选，建议填写一两句摘要；`tags` 可省略；`comments: false` 关闭单篇评论。
- 空大类使用 `children: []`；空子类可以先配置，稍后再添加文件。
- 文章文件名不能叫 `index.md`，它保留给目录页。
- 移动已有文章时，把原路径加入 `data/redirects.json`，同时保持文章 `id` 不变。

新文章不需要手工添加到导航、标签页或搜索索引。

## 站点名称、友链和主题

- `mkdocs.yml`：站名、作者、首页简介、网站地址与评论配置。
- `data/site-catalog.yml`：五大类、子类、顺序和说明。
- `data/friends.yml`：友链名称、HTTPS 地址、介绍。
- `docs/stylesheets/site.css`：浅色／深色颜色变量和页面排版。
- `overrides/`：导航、文章页、全站搜索、404 等模板。

搜索支持中文、英文、标题、分类、标签与正文；按 `Ctrl+Enter`（macOS 为 `⌘+Enter`）打开，`Esc` 关闭。完整正文索引只在第一次搜索时下载。浏览器中不会上传搜索词。

数学页面按需从 jsDelivr 加载 MathJax 3.2.2；网络不可用时保留可读的 TeX 源文，不将公式隐藏。字体采用本机字体回退，无额外网页字体下载。

PDF 页面接近视口时才加载 PDF.js 4.10.38，支持上一页／下一页和随屏幕缩放；它是浏览器端按需加载的资源，不增加 Python 环境依赖。原文件打开、下载链接始终可用，预览 CDN 失效也不影响下载。

## 启用评论

评论实现已接入，默认关闭，避免出现无效组件。

1. 在 <https://github.com/KujoStar/KujoStar.github.io/settings> 中启用 **Discussions**。
2. 在 <https://github.com/apps/giscus> 安装 giscus，只授权本站仓库。
3. 打开 <https://giscus.app/zh-CN>，选择本站仓库与 Announcements 分类，取得公开的 repository ID 和 category ID。
4. 在 `mkdocs.yml` 的 `extra.giscus` 填写 `repo_id`、`category_id`，并设置 `enabled: true`。

不需要个人访问令牌，也不要把任何密钥写进配置。关联方式由本站设置为 `specific`，使用 `nagisa:<文章id>`。不要改成 pathname，否则移动文章会改变关联。主题切换会同步评论主题。启用后在正式页面验证登录、评论和反应功能。

## 构建、检查和发布

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_*.py"
node --test tests/*.test.js
.\.venv\Scripts\python.exe -m mkdocs build --strict
.\.venv\Scripts\python.exe -B scripts/check_site.py
```

GitHub Pages 初次切换：在 <https://github.com/KujoStar/KujoStar.github.io/settings/pages> 中把 **Build and deployment → Source** 设为 **GitHub Actions**。将重构分支合入 `main` 后，工作流会验证并上传 `site/`，由官方 Pages 部署任务发布。PR 仅验证和上传产物，不发布；也可在 Actions 中从 `main` 手动运行。

公开工作流使用 GitHub 自动提供的权限，不需要部署密钥。生产域名保持 <https://kujostar.github.io/>。根路径部署是当前约定；若以后改成带子路径的 project Pages，须统一调整根相对链接并重新验证。

上线后检查首页、一个带锚点的旧文章地址、两个 PDF、搜索和评论。发布前应在本地确认展示效果。当前实现不会自动替你进行 GitHub 应用授权。

## 旧站迁移与恢复

原始版本提交为 `b6e6e0046cc825289f49662d66c3fec9957a03b5`。

- 原始 HTML、CSS、JavaScript、图片和 PDF 完整保存在 `legacy/`。
- `data/migration-manifest.json` 记录 16 篇文章、90 个代码块、附件哈希及原标题锚点。
- `data/redirects.json` 维护 34 个旧入口，自动生成目录地址和对应 `index.html` 的跳转页。
- `scripts/check_site.py` 将构建后的正文、公式、代码、日期、图片和锚点与旧站逐篇核对，检查静态文件的 SHA-256。
- `scripts/migrate_legacy.py` 是一次性迁移工具。**日常写作不要运行它**；默认拒绝覆盖已有 Markdown。`--overwrite` 会重建迁移文件并覆盖后续编辑，仅用于重新迁移。

有意修订旧文章时，应保留 `legacy/`，并明确调整对应迁移断言；新增文章不受旧文逐字核对约束。

可将 `legacy/` 作为原网站静态目录直接预览，或从上面的原始提交提取旧站以恢复部署。恢复上线时需同步恢复旧版 Pages 发布方式；仅切换代码但保留新的 Actions 设置不会自动恢复旧站。

## 致谢

布局参考自 [zdd14990 的个人网站](https://zdd14990.github.io/)，经作者同意参考其实现；仅借鉴通用布局与交互，没有迁移其文章和分类。框架为 [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)，数学排版使用 [MathJax](https://www.mathjax.org/)，评论使用 [giscus](https://giscus.app/)。
