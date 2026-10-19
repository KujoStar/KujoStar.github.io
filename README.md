# NAGISA's Blog

<https://kujostar.github.io/> · MkDocs Material

## 本地预览

使用 Python 3.11。在仓库目录运行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-cache-dir -r requirements.txt
.\.venv\Scripts\python.exe -m mkdocs serve --dev-addr 127.0.0.1:8000
```

已有 `.venv` 时直接运行最后一行。预览地址为 <http://127.0.0.1:8000/>。
Markdown、配置和模板保存后自动重建；修改 Python 代码后重启预览。

## 写文章

分类配置在 `data/site-catalog.yml`。每个大类的 `children` 列出子类，例如：

```yaml
- id: teaching
  name: 助教工作
  children:
    - id: programming
      name: 程序设计
```

对应的文章目录为 `docs/blog/teaching/programming/`。新建 `first-note.md`：

```markdown
---
id: teaching-programming-first-note
title: 第一次答疑
date: 2026-10-19
tags: [助教, 程序设计]
---

正文
```

- `id` 全站唯一，使用小写字母、数字和连字符；评论按此 ID 关联。
- `date` 为发布日期；可选的 `updated` 为更新日期，格式均为 `YYYY-MM-DD`。
- `tags` 可选，`comments: false` 关闭该文章的评论。
- 文章按日期倒序排列；子类可用 `order: [文章ID1, 文章ID2]` 指定章节顺序。
- 空大类使用 `children: []`；空子类可以先配置，再添加文章。
- `index.md` 用作目录页，文章使用其他文件名。
- 移动文章时保留 `id`，并在 `data/redirects.json` 中添加旧路径到新路径的映射。

## 修改页面

| 内容 | 文件 |
|---|---|
| 首页候选标题 | `data/home-quotes.yml` |
| 导航头像 | `docs/assets/avatar.jpg` |
| 浏览器图标 | `docs/assets/favicon.png`、`docs/favicon.ico` |
| 全站背景图片 | `docs/assets/background.webp` |
| 分类和顺序 | `data/site-catalog.yml` |
| 友链名称、描述、头像和网址 | `data/friends.yml` |
| 站名、域名、评论配置 | `mkdocs.yml` |
| 页面模板 | `overrides/` |
| 颜色、字体、排版 | `docs/stylesheets/site.css` |
| 搜索和页面交互 | `docs/javascripts/` |

搜索快捷键为 `Ctrl+Enter`（macOS 为 `⌘+Enter`），`Esc` 关闭。
公式使用 MathJax，PDF 预览使用 PDF.js。

背景透明度在 `docs/stylesheets/site.css` 的 `--background-opacity` 中调整：浅色主题为 `0.14`，
深色主题为 `0.12`；文章页使用对应值的 60%。背景图居中铺满屏幕，随屏幕比例裁切。

首页每次加载会从 `data/home-quotes.yml` 的 `quotes` 中随机选一句，并播放一次打字动画。
每项的 `lang` 填 `en` 或 `zh-CN`，`lines` 中每一项对应一行，最后一行使用强调色；窄屏会自动换行。
复制现有条目即可增加候选。开启系统的“减少动画”时直接显示全文。

友链在 `data/friends.yml` 中维护：`name` 是标题，`description` 是个人描述，
`avatar` 是头像地址，`url` 是博客地址。头像和博客地址使用 HTTPS。
`avatar` 和 `description` 可以省略或留空。未填头像时使用 [默认头像](https://kujostar.github.io/assets/default-avatar.jpg)，
未填描述时显示“这个人不懒，但是也什么都没留下。”。

## 评论

giscus 连接本站仓库的 Announcements 讨论分类，映射方式为 `specific`，标识为 `nagisa:<文章id>`。
访客通过 GitHub 登录后留言，评论可在仓库 Discussions 中管理。

更换评论仓库时，在新仓库开启 Discussions 并安装 [giscus](https://github.com/apps/giscus)，
通过 [配置页](https://giscus.app/zh-CN) 获取仓库与分类 ID，更新 `mkdocs.yml` 的 `extra.giscus`。

## 检查与发布

JavaScript 测试使用 Node.js 24。

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_*.py"
node --test tests/*.test.js
.\.venv\Scripts\python.exe -m mkdocs build --strict
.\.venv\Scripts\python.exe -B scripts/check_site.py
```

提交并推送到 `main` 后，GitHub Actions 自动检查和发布。PR 运行检查。
构建结果位于 `site/`；工作流在 `.github/workflows/pages.yml`。

## 旧站

`legacy/` 保存 Hexo 旧站，原始提交为 `b6e6e0046cc825289f49662d66c3fec9957a03b5`。
迁移清单在 `data/migration-manifest.json`，旧网址映射在 `data/redirects.json`。
`scripts/check_site.py` 会核对旧文正文、代码、公式、附件及链接。
修订旧文后，相应更新迁移校验。
删除迁移文章时，将清单中对应条目的 `removed` 设为 `true`，并调整旧网址跳转。

恢复旧站时，可从原始提交恢复文件并将 Pages 发布来源改回分支部署。
迁移和验收记录见 [MIGRATION.md](MIGRATION.md) 与 [VALIDATION.md](VALIDATION.md)。

## 致谢

布局参考 [zdd14990 的个人网站](https://zdd14990.github.io/)。
使用 [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)、[MathJax](https://www.mathjax.org/)、[PDF.js](https://mozilla.github.io/pdf.js/) 和 [giscus](https://giscus.app/)。
