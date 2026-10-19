"""Validated content model and static page/index generation for NAGISA."""
from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import date, datetime
from pathlib import Path, PurePosixPath
from urllib.parse import quote, urlsplit

import yaml
from bs4 import BeautifulSoup
from mkdocs.exceptions import PluginError

SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
esc = lambda value: html.escape(str(value), quote=True)


def read_document(path):
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    match = re.match(r"\A---\n(.*?)\n---(?:\n|$)", text, re.S)
    if not match:
        raise ValueError(f"{path}: missing YAML front matter")
    meta = yaml.safe_load(match[1])
    if not isinstance(meta, dict):
        raise ValueError(f"{path}: metadata must be a mapping")
    return meta, text[match.end():].lstrip("\n")


def date_string(value, source):
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return date.fromisoformat(value).isoformat()
    raise ValueError(f"{source}: expected YYYY-MM-DD date, got {value!r}")


def read_catalog(path):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    categories = data.get("categories") if isinstance(data, dict) else None
    if not isinstance(categories, list):
        raise ValueError(f"{path}: categories must be a list")
    category_ids = set()
    for category in categories:
        validate_named(category, category_ids, path)
        children = category.get("children", [])
        if not isinstance(children, list):
            raise ValueError(f"{path}: children must be a list")
        category["children"] = children
        child_ids = set()
        for child in children:
            validate_named(child, child_ids, path)
            order = child.get("order", [])
            if not isinstance(order, list) or any(not isinstance(x, str) for x in order) or len(order) != len(set(order)):
                raise ValueError(f"{path}: invalid/duplicate article order")
    return categories


def validate_named(item, seen, source):
    if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not SLUG.fullmatch(item["id"]):
        raise ValueError(f"{source}: invalid category id")
    if item["id"] in seen or not isinstance(item.get("name"), str) or not item["name"].strip():
        raise ValueError(f"{source}: duplicate id or missing name: {item['id']}")
    seen.add(item["id"])


def read_home_quotes(path):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    quotes = data.get("quotes") if isinstance(data, dict) else None
    if not isinstance(quotes, list) or not quotes:
        raise ValueError(f"{path}: quotes must be a nonempty list")
    for item in quotes:
        if not isinstance(item, dict) or not isinstance(item.get("lang"), str) or not re.fullmatch(r"[a-zA-Z]+(?:-[a-zA-Z0-9]+)*", item["lang"]):
            raise ValueError(f"{path}: each quote needs a language code")
        lines = item.get("lines")
        if not isinstance(lines, list) or not lines or any(not isinstance(line, str) or not line.strip() for line in lines):
            raise ValueError(f"{path}: quote lines must contain nonempty text")
        item["lines"] = [line.strip() for line in lines]
    return quotes


def summary(body):
    paragraph = next((p for p in body.split("\n\n") if not p.startswith(("#", "<", "```", "$$"))), "")
    paragraph = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", paragraph)
    paragraph = re.sub(r"\$([^$]*)\$", r"\1", paragraph)
    paragraph = re.sub(r"[`*]", "", paragraph)
    return re.sub(r"\s+", " ", paragraph.replace("\\\n", " ")).strip()[:140]


def build_articles(root, categories):
    articles, seen = [], set()
    placements = {(c["id"], s["id"]): (c, s) for c in categories for s in c["children"]}
    for path in sorted((root / "docs/blog").rglob("*.md")):
        if path.name == "index.md":
            continue
        parts = path.relative_to(root / "docs/blog").parts
        if len(parts) != 3 or tuple(parts[:2]) not in placements:
            raise ValueError(f"{path}: article must belong to a configured category/subcategory")
        meta, body = read_document(path)
        aid, title = meta.get("id"), meta.get("title")
        if not isinstance(aid, str) or not SLUG.fullmatch(aid) or aid in seen:
            raise ValueError(f"{path}: missing, invalid or duplicate article id {aid!r}")
        if not isinstance(title, str) or not title.strip():
            raise ValueError(f"{path}: title is required")
        tags = meta.get("tags", [])
        if not isinstance(tags, list) or any(not isinstance(t, str) or not t.strip() for t in tags):
            raise ValueError(f"{path}: tags must be a list of nonempty strings")
        if "comments" in meta and not isinstance(meta["comments"], bool):
            raise ValueError(f"{path}: comments must be true or false")
        published = date_string(meta.get("date"), path)
        updated = date_string(meta.get("updated", published), path)
        if updated < published:
            raise ValueError(f"{path}: updated precedes date")
        if "description" in meta and not isinstance(meta["description"], str):
            raise ValueError(f"{path}: description must be text")
        category, child = placements[tuple(parts[:2])]
        src = path.relative_to(root / "docs").as_posix()
        articles.append({"id": aid, "title": title, "source": src, "url": "/" + src[:-3] + "/", "date": published, "updated": updated, "tags": list(dict.fromkeys(tags)), "category": category["name"], "subcategory": child["name"], "category_id": category["id"], "subcategory_id": child["id"], "description": meta.get("description") or summary(body), "body": body, "comments": meta.get("comments", True)})
        seen.add(aid)
    for category in categories:
        for child in category["children"]:
            members = {a["id"] for a in articles if (a["category_id"], a["subcategory_id"]) == (category["id"], child["id"])}
            unknown = set(child.get("order", [])) - members
            if unknown:
                raise ValueError(f"Unknown article IDs in series order: {unknown}")
    return articles


def article_row(article):
    return f'''<li class="article-row" data-tags="{esc(json.dumps(article['tags'], ensure_ascii=False))}"><a href="{esc(article['url'])}"><span class="article-row-main"><span class="article-row-title">{esc(article['title'])}</span></span><time datetime="{article['date']}">{article['date'].replace('-', '.')}</time><span aria-hidden="true" class="row-arrow">↗</span></a></li>'''


def ordered_articles(articles, category, child):
    members = sorted([a for a in articles if (a["category_id"], a["subcategory_id"]) == (category["id"], child["id"])], key=lambda a: (a["date"], a["id"]), reverse=True)
    order = child.get("order", [])
    if order:
        members.sort(key=lambda a: order.index(a["id"]) if a["id"] in order else len(order))
    return members


class Site:
    def __init__(self, root, config):
        self.root, self.config = Path(root), config
        try:
            self.categories = read_catalog(self.root / "data/site-catalog.yml")
            self.home_quotes = read_home_quotes(self.root / "data/home-quotes.yml")
            self.articles = build_articles(self.root, self.categories)
            self.friends = yaml.safe_load((self.root / "data/friends.yml").read_text(encoding="utf-8"))["friends"]
            for friend in self.friends:
                if urlsplit(friend["url"]).scheme != "https" or not friend.get("name"):
                    raise ValueError("Friends need a name and HTTPS URL")
            self.redirects = json.loads((self.root / "data/redirects.json").read_text(encoding="utf-8"))
            giscus = config.get("extra", {}).get("giscus", {})
            if giscus.get("enabled") and any(not giscus.get(key) for key in ("repo", "repo_id", "category", "category_id")):
                raise ValueError("giscus is enabled but its repository/category IDs are missing")
        except (ValueError, KeyError, TypeError, yaml.YAMLError) as exc:
            raise PluginError(str(exc)) from exc
        self.by_source = {a["source"]: a for a in self.articles}
        self.rendered = {}

    def home(self):
        first = self.home_quotes[0]
        lines = "\n".join(f'<span class="quote-line{ " quote-ending" if i == len(first["lines"]) - 1 else ""}">{esc(line)}</span>' for i, line in enumerate(first["lines"]))
        return f'''<section class="home-hero">
<h1 lang="{esc(first['lang'])}" data-home-quotes="{esc(json.dumps(self.home_quotes, ensure_ascii=False))}">{lines}</h1>
<form class="home-search" role="search" data-home-search>
  <label class="sr-only" for="home-query">搜索</label><span aria-hidden="true">⌕</span>
  <input id="home-query" name="q" type="search" placeholder="Search..." autocomplete="off">
  <button type="submit" aria-label="搜索">↗</button>
</form>
</section>'''

    def catalog(self):
        out = ['<header class="page-heading"><h1>内容</h1></header><nav class="category-index" aria-label="内容分类">']
        for category in self.categories:
            count = sum(a["category_id"] == category["id"] for a in self.articles)
            out.append(f'<a class="category-card" href="#{category["id"]}"><strong>{esc(category["name"])}</strong><span class="category-count">{count} 篇 <span aria-hidden="true">↗</span></span></a>')
        out.append('</nav><div class="shelves">')
        for category in self.categories:
            out.append(f'<section class="shelf" id="{category["id"]}" data-shelf><header class="shelf-heading"><a class="shelf-back" href="#" aria-label="返回全部分类">← 全部分类</a><h2 tabindex="-1">{esc(category["name"])}</h2></header>')
            if not category["children"]:
                out.append('<div class="empty-state"><p>暂无文章</p></div>')
            else:
                out.append('<div class="book-grid">')
                for child in category["children"]:
                    members = ordered_articles(self.articles, category, child)
                    key = category["id"] + "--" + child["id"]
                    out.append(f'<details class="book" id="{key}"><summary class="book-cover"><span class="book-name">{esc(child["name"])}</span><span class="book-bottom"><span><b>{len(members)}</b> 篇</span><span aria-hidden="true">＋</span></span></summary><div class="book-contents"><div class="book-contents-heading"><h3>{esc(child["name"])}</h3><button class="book-close" type="button" aria-label="收起{esc(child["name"])}">收起 ×</button></div><ol class="article-list">')
                    out.extend(article_row(a) for a in members)
                    if not members:
                        out.append('<li class="empty-note">暂无文章</li>')
                    out.append('</ol></div></details>')
                out.append('</div>')
            out.append('</section>')
        out.append('</div>')
        return "\n".join(out)

    def tags(self):
        tags = sorted({tag for a in self.articles for tag in a["tags"]})
        out = ['<header class="page-heading"><h1>标签</h1></header><nav class="tag-filters" aria-label="按标签筛选"><a href="#" class="tag-filter" aria-current="true">全部</a>']
        for tag in tags:
            count = sum(tag in a["tags"] for a in self.articles)
            out.append(f'<a id="{esc(tag)}" href="#{quote(tag)}" class="tag-filter" data-tag="{esc(tag)}">{esc(tag)} <span>{count}</span></a>')
        out.append('</nav><p class="filter-status" role="status" aria-live="polite"></p><ol class="article-list tag-results">')
        out.extend(article_row(a) for a in sorted(self.articles, key=lambda a: (a["date"], a["id"]), reverse=True))
        out.append('</ol><p class="tag-empty" hidden>暂无文章</p>')
        return "\n".join(out)

    def friends_page(self):
        out = ['<header class="page-heading"><h1>友链</h1></header><ul class="friend-list">']
        for friend in self.friends:
            out.append(f'<li><a href="{esc(friend["url"])}" target="_blank" rel="noopener noreferrer"><strong>{esc(friend["name"])}</strong><span class="friend-arrow" aria-hidden="true">↗</span></a></li>')
        return "\n".join(out) + '</ul>'

    def prepare(self, markdown, page):
        source = page.file.src_uri
        article = self.by_source.get(source)
        page.meta["hide"] = ["navigation", "footer"] + ([] if article else ["toc"])
        page.meta["kind"] = "article" if article else "home" if page.is_homepage else "catalog" if source == "blog/index.md" else "tags" if source == "tags/index.md" else "page"
        if article:
            page.meta["article"] = article
            page.meta["description"] = article["description"]
            category = next(c for c in self.categories if c["id"] == article["category_id"])
            child = next(s for s in category["children"] if s["id"] == article["subcategory_id"])
            members = ordered_articles(self.articles, category, child)
            index = members.index(article)
            page.meta["neighbors"] = {"previous": members[index - 1] if index > 0 else None, "next": members[index + 1] if index + 1 < len(members) else None, "series": bool(child.get("order"))}
        for name, renderer in {"HOME": self.home, "CATALOG": self.catalog, "TAGS": self.tags, "FRIENDS": self.friends_page}.items():
            marker = f"[NAGISA:{name}]"
            if marker in markdown:
                markdown = markdown.replace(marker, renderer())
        return markdown

    def capture(self, content, page):
        soup = BeautifulSoup(content, "html.parser")
        page.meta["has_math"] = bool(soup.select(".arithmatex"))
        page.meta["has_pdf"] = bool(soup.select("[data-pdf-src]"))
        source = page.file.src_uri
        if source in self.by_source:
            for node in soup.select(".headerlink, .pdf-attachment"):
                node.decompose()
            text = soup.get_text(" ", strip=True)
            for delimiter in ("\\(", "\\)", "\\[", "\\]"):
                text = text.replace(delimiter, "")
            headings = [{"title": h.get_text(" ", strip=True), "anchor": h["id"]} for h in soup.select("h1[id],h2[id],h3[id],h4[id],h5[id],h6[id]")]
            self.rendered[source] = {"text": text, "headings": headings}
        return content

    def write_output(self):
        output = Path(self.config["site_dir"])
        assets = output / "assets"
        assets.mkdir(parents=True, exist_ok=True)
        catalog, full = [], []
        for article in self.articles:
            item = {k: article[k] for k in ("id", "title", "url", "date", "description", "tags", "category", "subcategory")}
            catalog.append(item)
            full.append({**item, **self.rendered.get(article["source"], {"text": "", "headings": []})})
        version = hashlib.sha256(json.dumps(full, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]
        for name, items in (("catalog", catalog), ("search", full)):
            (assets / f"{name}.json").write_text(json.dumps({"version": version, "items": items}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        base = self.config["site_url"].rstrip("/")
        for old, new in self.redirects.items():
            if not old.startswith("/") or not old.endswith("/") or ".." in PurePosixPath(old).parts or not new.startswith("/") or new.startswith("//"):
                raise PluginError(f"Unsafe redirect: {old} -> {new}")
            target = output / old.strip("/") / "index.html"
            if target.exists():
                raise PluginError(f"Redirect would overwrite an existing page: {old}")
            target.parent.mkdir(parents=True, exist_ok=True)
            encoded = quote(new, safe="/#%?=&")
            target.write_text(f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><link rel="canonical" href="{esc(base + encoded)}"><meta http-equiv="refresh" content="0;url={esc(encoded)}"><title>笔记已迁移 · NAGISA</title></head><body><p>这篇笔记已有新的地址：<a href="{esc(encoded)}">前往新页面</a></p><script>const destination = new URL({json.dumps(encoded)}, location.origin); destination.search = location.search; if (location.hash) destination.hash = location.hash; location.replace(destination.href);</script></body></html>', encoding="utf-8")
        (output / ".nojekyll").touch()
        (output / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n", encoding="utf-8")
