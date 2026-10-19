"""One-time, repeatable Hexo HTML -> Markdown migration. Never rewrites legacy/."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml
from bs4 import BeautifulSoup, NavigableString
from markdownify import MarkdownConverter

ROOT = Path(__file__).resolve().parents[1]
MATH = re.compile(r"(?<!\\)\$\$[\s\S]*?(?<!\\)\$\$|(?<!\\)\$(?!\$)[^$\n]*?(?<!\\)\$|\\\([\s\S]*?\\\)|\\\[[\s\S]*?\\\]")


class MkDocsConverter(MarkdownConverter):
    def convert_li(self, element, text, parent_tags):
        converted = super().convert_li(element, text, parent_tags)
        lines = converted.splitlines(keepends=True)
        match = re.match(r"(?:\d+\.|[-*+]) ", lines[0]) if lines else None
        if match and len(match[0]) < 4:
            width = len(match[0])
            # Python-Markdown needs four-space list continuations, unlike CommonMark.
            lines[1:] = [(" " * (4 - width) + line) if line.startswith(" " * width) else line for line in lines[1:]]
        return "".join(lines) + "\n"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def code_text(figure):
    lines = figure.select("td.code .line")
    return "\n".join(line.get_text() for line in lines) if lines else figure.get_text()


def legacy_body(path):
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    return soup, soup.select_one("#article-container")


def assignment(slug):
    if slug.startswith(("PA", "Lab")):
        return "course-notes", "data-structures-algorithms"
    if slug.startswith("Probability"):
        return "course-notes", "probability-statistics"
    return "journal", "site-notes" if slug == "hello-world" else "campus-life"


def convert_body(body):
    body = BeautifulSoup(str(body), "html.parser")
    replacements = {}
    block_tokens = set()

    def token(value, block=False):
        key = f"NAGISAPRESERVE{len(replacements):05d}TOKEN"
        replacements[key] = value
        if block:
            block_tokens.add(key)
        return NavigableString(f"\n\n{key}\n\n" if block else key)

    for link in body.select("a.headerlink"):
        link.decompose()
    for figure in body.select("figure.highlight"):
        code = code_text(figure)
        language = next((c for c in figure.get("class", []) if c != "highlight"), "text")
        language = {"c++": "cpp"}.get(language, language)
        fence = "`" * max(3, max((len(x) + 1 for x in re.findall(r"`+", code)), default=3))
        figure.replace_with(token(f"{fence}{language}\n{code}\n{fence}", True))
    for frame in body.select("iframe, embed, object"):
        src = frame.get("src", frame.get("data", ""))
        if src.startswith("/pdf/"):
            frame.replace_with(token(
                f'<div class="pdf-attachment" data-pdf-src="{src}">\n'
                f'<p class="pdf-links"><a href="{src}" target="_blank" rel="noopener">打开 PDF 原文件 ↗</a> '
                f'<a href="{src}" download>下载 PDF ↓</a></p>\n'
                f'<div class="pdf-preview"><p class="pdf-status" role="status">正在准备 PDF 预览……</p></div>\n'
                f'<noscript><p>请使用上方链接打开或下载完整 PDF。</p></noscript>\n</div>', True))
    for heading in body.select("h1,h2,h3,h4,h5,h6"):
        level = max(2, int(heading.name[1]))
        anchor = heading.get("id", "")
        value = "#" * level + " " + heading.get_text()
        if anchor:
            value += " {#" + anchor + "}"
        heading.replace_with(token(value, True))
    # Shield TeX before Markdown conversion can escape backslashes/underscores.
    for node in list(body.find_all(string=True)):
        if node.parent.name in ("code", "pre", "script", "style") or "NAGISAPRESERVE" in str(node):
            continue
        pieces, last = [], 0
        for match in MATH.finditer(str(node)):
            pieces.extend([str(node)[last:match.start()], str(token(match.group()))])
            last = match.end()
        if pieces:
            node.replace_with(NavigableString("".join(pieces) + str(node)[last:]))
    for script in body.select("script, style"):
        script.decompose()
    output = MkDocsConverter(heading_style="ATX", bullets="-", newline_style="SPACES").convert(str(body)).strip()
    for key, value in replacements.items():
        if key in block_tokens:
            # Restore every line at the placeholder's nesting level, not just its fence.
            output = re.sub(r"(?m)^([ \t]*)" + key + r"[ \t]*$", lambda m: "\n" + "\n".join(m[1] + line if line else "" for line in value.split("\n")) + "\n", output)
        else:
            output = output.replace(key, value)
    if "NAGISAPRESERVE" in output:
        raise ValueError("Unrestored migration placeholder")
    return output.strip() + "\n"


def migrate(root=ROOT, overwrite=False):
    legacy = root / "legacy"
    records, redirects = [], {}
    files = sorted([*legacy.glob("2022/**/index.html"), *legacy.glob("2023/**/index.html")])
    for source in files:
        soup, body = legacy_body(source)
        if body is None:
            raise ValueError(f"Missing article body: {source}")
        slug = source.parent.name
        article_id = slug.lower()
        category, child = assignment(slug)
        destination = root / "docs" / "blog" / category / child / (article_id + ".md")
        if destination.exists() and not overwrite:
            raise FileExistsError(f"Refusing to overwrite {destination}; use --overwrite explicitly")
        times = soup.select("#post-meta time") or soup.select("time")
        dates = [datetime.fromisoformat(t["datetime"].replace("Z", "+00:00")).astimezone(timezone(timedelta(hours=8))).date().isoformat() for t in times[:2]]
        title = soup.select_one("h1.post-title").get_text()
        tags = list(dict.fromkeys(a.get_text() for a in soup.select(".tag_share .tag-list a, .tag_share a.post-meta__tags")))
        if not tags:
            tags = ["DSA解题报告"] if category == "course-notes" and child.startswith("data-") else ["概统课程笔记"] if category == "course-notes" else ["杂谈和日记"] if child == "campus-life" else []
        metadata = {"id": article_id, "title": title, "date": dates[0], "updated": dates[-1], "tags": tags}
        content = convert_body(body)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("---\n" + yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False) + "---\n\n" + content, encoding="utf-8", newline="\n")
        old_url = "/" + source.parent.relative_to(legacy).as_posix() + "/"
        new_url = "/" + destination.relative_to(root / "docs").with_suffix("").as_posix() + "/"
        redirects[old_url] = new_url
        records.append({"id": article_id, "title": title, "source": source.relative_to(root).as_posix(), "destination": destination.relative_to(root).as_posix(), "old_url": old_url, "new_url": new_url, "source_sha256": sha(source.read_bytes()), "headings": [h.get("id") for h in body.select("h1,h2,h3,h4,h5,h6") if h.get("id")], "code_sha256": [sha(code_text(f).encode()) for f in body.select("figure.highlight")], "math": MATH.findall(body.get_text()), "date": dates[0], "updated": dates[-1]})
    for source in legacy.rglob("index.html"):
        relative = source.parent.relative_to(legacy).as_posix()
        url = "/" + relative + "/"
        if relative in (".", "tags") or url in redirects:
            continue
        if relative.startswith("categories/学习历程"):
            target = "/blog/#course-notes"
        elif relative.startswith("categories/心路历程"):
            target = "/blog/#journal"
        elif relative.startswith("tags/"):
            target = "/tags/#" + relative.split("/")[1]
        else:
            target = "/blog/"
        redirects[url] = target
    redirects.setdefault("/categories/", "/blog/")
    assets = []
    for directory in ("pdf", "medias", "img"):
        for source in sorted((legacy / directory).rglob("*")):
            if not source.is_file():
                continue
            relative = source.relative_to(legacy)
            target = root / "docs" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            assets.append({"path": relative.as_posix(), "sha256": sha(source.read_bytes()), "bytes": source.stat().st_size})
    (root / "data" / "migration-manifest.json").write_text(json.dumps({"baseline_commit": "b6e6e0046cc825289f49662d66c3fec9957a03b5", "articles": records, "assets": assets}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (root / "data" / "redirects.json").write_text(json.dumps(redirects, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Migrated {len(records)} articles, {len(assets)} assets; {len(redirects)} redirects.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overwrite", action="store_true", help="Explicitly regenerate migrated Markdown, discarding subsequent edits")
    migrate(overwrite=parser.parse_args().overwrite)
