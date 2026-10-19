"""Check built links, SEO, search consistency and source-to-render migration fidelity."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://kujostar.github.io"


def soup(path):
    return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")


def normalized_code(text):
    # Highlighting expands tabs and may drop trailing spaces, but not empty input lines.
    return "\n".join(line.rstrip() for line in text.expandtabs(4).splitlines()).rstrip("\n")


def normalized_prose(node):
    node = BeautifulSoup(str(node), "html.parser")
    for element in node.select("figure.highlight, div.highlight, .headerlink, .pdf-attachment, iframe, embed, object, script, style"):
        element.decompose()
    text = node.get_text()
    for delimiter in ("\\(", "\\)", "\\[", "\\]", "$"):
        text = text.replace(delimiter, "")
    return re.sub(r"\s+", "", text)


def migration_errors(root=ROOT):
    errors = []
    manifest = json.loads((root / "data/migration-manifest.json").read_text(encoding="utf-8"))
    for article in manifest["articles"]:
        source = root / article["source"]
        target = root / "site" / article["new_url"].strip("/") / "index.html"
        if hashlib.sha256(source.read_bytes()).hexdigest() != article["source_sha256"]:
            errors.append(f"Legacy snapshot changed: {source}")
        if article.get("removed"):
            if (root / article["destination"]).exists() or (target.is_file() and soup(target).select_one("#article-body")):
                errors.append(f"Removed article is still published: {article['id']}")
            continue
        if not target.is_file():
            errors.append(f"Missing migrated page: {target}")
            continue
        old = soup(source).select_one("#article-container")
        document = soup(target)
        new = document.select_one("#article-body")
        if new is None:
            errors.append(f"Missing article body: {article['id']}")
            continue
        if normalized_prose(old) != normalized_prose(new):
            errors.append(f"Prose or formula changed: {article['id']}")
        old_code = [normalized_code("\n".join(line.get_text() for line in figure.select("td.code .line"))) for figure in old.select("figure.highlight")]
        new_code = [normalized_code(code.get_text()) for code in new.select("div.highlight pre code")]
        if old_code != new_code:
            errors.append(f"Code or testcase changed: {article['id']} ({len(old_code)} -> {len(new_code)} blocks)")
        ids = {e.get("id") for e in document.select("[id]")}
        for anchor in article["headings"]:
            if anchor not in ids:
                errors.append(f"Lost legacy anchor: {article['id']}#{anchor}")
        for img in old.select("img[src]"):
            if not any(n.get("src") == img["src"] for n in new.select("img[src]")):
                errors.append(f"Lost image: {article['id']} {img['src']}")
        if document.select_one(".article-heading h1").get_text() != article["title"]:
            errors.append(f"Title changed: {article['id']}")
        dates = {t.get("datetime") for t in document.select(".article-meta time")}
        if article["date"] not in dates or article["updated"] not in dates:
            errors.append(f"Dates changed: {article['id']}")
    for asset in manifest["assets"]:
        for location in ("docs", "site"):
            path = root / location / asset["path"]
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != asset["sha256"]:
                errors.append(f"Missing/changed asset: {path}")
    return errors


def check_site(root=ROOT):
    errors = migration_errors(root)
    site = root / "site"
    pages = {path: soup(path) for path in site.rglob("*.html")}
    redirects = json.loads((root / "data/redirects.json").read_text(encoding="utf-8"))
    for old, new in redirects.items():
        path = site / old.strip("/") / "index.html"
        if path not in pages:
            errors.append(f"Missing redirect: {old}")
            continue
        page = pages[path]
        canonical = page.select_one('link[rel="canonical"]')
        if not canonical or unquote(canonical["href"]) != BASE + new:
            errors.append(f"Wrong redirect canonical: {old}")
    for path, page in pages.items():
        relative = path.relative_to(site).as_posix()
        current = BASE + "/" + relative
        ids = [n["id"] for n in page.select("[id]")]
        if len(ids) != len(set(ids)):
            errors.append(f"Duplicate HTML ids: {relative}")
        if "NAGISAPRESERVE" in str(page) or "[NAGISA:" in str(page):
            errors.append(f"Unrendered placeholder: {relative}")
        for element in page.select("a[href], link[href], img[src], script[src], iframe[src]"):
            ref = element.get("href", element.get("src", ""))
            if not ref or ref.startswith(("data:", "mailto:", "javascript:")):
                continue
            parsed = urlsplit(urljoin(current, ref))
            if parsed.netloc.lower() != "kujostar.github.io":
                continue
            target = site / unquote(parsed.path).lstrip("/")
            if target.is_dir():
                target = target / "index.html"
            if not target.is_file():
                errors.append(f"Broken link: {relative} -> {ref}")
            elif parsed.fragment and target in pages:
                anchor = unquote(parsed.fragment)
                if pages[target].find(id=anchor) is None:
                    errors.append(f"Missing anchor: {relative} -> {ref}")
    light = json.loads((site / "assets/catalog.json").read_text(encoding="utf-8"))
    full = json.loads((site / "assets/search.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "data/migration-manifest.json").read_text(encoding="utf-8"))
    removed_ids = {a["id"] for a in manifest["articles"] if a.get("removed")}
    if removed_ids & {i["id"] for index in (light, full) for i in index["items"]}:
        errors.append("Removed articles remain in the search index")
    if light["version"] != full["version"] or {i["id"] for i in light["items"]} != {i["id"] for i in full["items"]}:
        errors.append("Search index versions/IDs disagree")
    for item in full["items"]:
        path = site / item["url"].strip("/") / "index.html"
        page = pages.get(path)
        if page is None or not item["text"]:
            errors.append(f"Invalid search document: {item['id']}")
            continue
        if page.select_one('link[rel="canonical"]')["href"] != BASE + item["url"]:
            errors.append(f"Canonical mismatch: {item['id']}")
        for heading in item["headings"]:
            if not page.find(id=heading["anchor"]):
                errors.append(f"Invalid search anchor: {item['id']}")
    archive = pages.get(site / "archives/index.html")
    if archive is None:
        errors.append("Missing archive page")
    else:
        expected = sorted(full["items"], key=lambda a: (a["date"], a["id"]), reverse=True)
        entries = archive.select(".archive-entry")
        if [entry.select_one("a")["href"] for entry in entries] != [a["url"] for a in expected]:
            errors.append("Archive must include every article in descending publication order")
        for entry, article in zip(entries, expected):
            if entry.select_one("time")["datetime"] != article["date"] or entry.select_one(".archive-title").get_text() != article["title"]:
                errors.append(f"Archive title/date mismatch: {article['id']}")
            if entry.select_one(".archive-category").get_text() != f"{article['category']} / {article['subcategory']}":
                errors.append(f"Archive category mismatch: {article['id']}")
        if [a.get_text(strip=True) for a in archive.select(".nav-links a:not(.nav-github)")] != ["首页", "内容", "归档", "标签", "友链"]:
            errors.append("Archive navigation order is incorrect")
    if errors:
        raise AssertionError("\n".join(errors))
    return f"OK: {len(full['items'])} articles; {len(redirects)} redirects; {len(pages)} HTML pages; migration, assets, links, anchors, SEO, search and archives checked."


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(check_site())
