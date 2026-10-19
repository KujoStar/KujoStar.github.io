import json
import sys
import tempfile
import unittest
from pathlib import Path

import markdown
import yaml
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from site_builder import build_articles, read_catalog, read_document, date_string, ordered_articles
from scripts.migrate_legacy import convert_body, legacy_body
from scripts.check_site import normalized_prose, normalized_code


class CatalogTests(unittest.TestCase):
    def test_initial_placement_and_series(self):
        categories = read_catalog(ROOT / "data/site-catalog.yml")
        articles = build_articles(ROOT, categories)
        self.assertEqual([c["name"] for c in categories], ["课程笔记", "助教工作", "论文阅读", "科研项目", "随笔日记"])
        self.assertGreaterEqual(len(articles), 16)
        members = ordered_articles(articles, categories[0], categories[0]["children"][1])
        self.assertEqual([a["id"] for a in members[:2]], ["probability-theory-notes-1", "probability-theory-notes-2"])

    def test_empty_categories_and_new_subcategory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog = root / "catalog.yml"
            catalog.write_text(yaml.safe_dump({"categories": [{"id": "teaching", "name": "助教工作", "children": [{"id": "new-course", "name": "新课程"}]}]}, allow_unicode=True), encoding="utf-8")
            categories = read_catalog(catalog)
            self.assertEqual(build_articles(root, categories), [])
            folder = root / "docs/blog/teaching/new-course"
            folder.mkdir(parents=True)
            (folder / "first.md").write_text("---\nid: first\ntitle: New\ndate: 2026-10-19\ntags: [中文, Python]\n---\n\nHello", encoding="utf-8")
            articles = build_articles(root, categories)
            self.assertEqual(articles[0]["subcategory"], "新课程")
            self.assertEqual(articles[0]["url"], "/blog/teaching/new-course/first/")
            (folder / "duplicate.md").write_text((folder / "first.md").read_text(encoding="utf-8"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                build_articles(root, categories)

    def test_invalid_catalog_and_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "catalog.yml"
            for categories in ([{"id": "../escape", "name": "Bad"}], [{"id": "valid", "name": "A"}, {"id": "valid", "name": "B"}]):
                path.write_text(yaml.safe_dump({"categories": categories}), encoding="utf-8")
                with self.assertRaises(ValueError):
                    read_catalog(path)
        for value in ("2026-02-30", "2026-1-1", None, True):
            with self.assertRaises(ValueError):
                date_string(value, "test")

    def test_unmapped_content_and_invalid_metadata_fail(self):
        categories = [{"id": "notes", "name": "Notes", "children": [{"id": "a", "name": "A"}]}]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "docs/blog/notes/a"
            folder.mkdir(parents=True)
            path = folder / "example.md"
            base = {"id": "one", "title": "One", "date": "2026-10-19"}
            for fields in ({"updated": "2025-10-19"}, {"tags": "not-a-list"}, {"comments": "false"}, {"id": "../x"}):
                path.write_text("---\n" + yaml.safe_dump({**base, **fields}) + "---\nText", encoding="utf-8")
                with self.assertRaises(ValueError):
                    build_articles(root, categories)
            path.write_text("---\n" + yaml.safe_dump(base) + "---\nText", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "configured"):
                build_articles(root, [])


class MigrationTests(unittest.TestCase):
    def test_all_legacy_content_renders_without_loss(self):
        manifest = json.loads((ROOT / "data/migration-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["articles"]), 16)
        for article in manifest["articles"]:
            with self.subTest(article=article["id"]):
                _, old = legacy_body(ROOT / article["source"])
                meta, body = read_document(ROOT / article["destination"])
                rendered = markdown.markdown(body, extensions=["attr_list", "tables", "sane_lists", "pymdownx.superfences", "pymdownx.highlight", "pymdownx.arithmatex"], extension_configs={"pymdownx.highlight": {"stripnl": False}, "pymdownx.arithmatex": {"generic": True}})
                new = BeautifulSoup(rendered, "html.parser")
                self.assertEqual(normalized_prose(old), normalized_prose(new))
                old_code = [normalized_code("\n".join(l.get_text() for l in f.select("td.code .line"))) for f in old.select("figure.highlight")]
                new_code = [normalized_code(c.get_text()) for c in new.select("div.highlight pre code")]
                self.assertEqual(old_code, new_code)
                self.assertEqual(meta["title"], article["title"])
                for anchor in article["headings"]:
                    self.assertIsNotNone(new.find(id=anchor))

    def test_nested_code_blank_input_and_math(self):
        old = BeautifulSoup('<article><ol><li>First <figure class="highlight text"><table><td class="code"><pre><span class="line"> </span><br><span class="line">1 &lt; 2</span></pre></td></table></figure><p>Continue</p></li><li>Second $x_1 \\leq 2$</li></ol></article>', "html.parser")
        body = convert_body(old)
        rendered = markdown.markdown(body, extensions=["sane_lists", "pymdownx.superfences", "pymdownx.highlight"], extension_configs={"pymdownx.highlight": {"stripnl": False}})
        new = BeautifulSoup(rendered, "html.parser")
        self.assertEqual(len(new.select("ol > li")), 2)
        self.assertEqual(normalized_prose(old), normalized_prose(new))
        self.assertTrue(new.select_one("pre code").get_text().startswith("\n"))


class CommentTests(unittest.TestCase):
    def test_move_keeps_discussion_id_and_opt_out_hides_widget(self):
        env = Environment(loader=FileSystemLoader(ROOT / "overrides"), autoescape=select_autoescape())
        template = env.get_template("partials/content.html")
        article = {"id": "stable-note", "title": "One", "date": "2026-10-19", "updated": "2026-10-19", "category_id": "course-notes", "subcategory_id": "example", "category": "Notes", "subcategory": "Example", "tags": [], "comments": True}
        giscus = {"enabled": True, "repo": "KujoStar/KujoStar.github.io", "repo_id": "test-repo", "category": "Announcements", "category_id": "test-category"}

        def render():
            page = {"content": "<p>Hello</p>", "meta": {"article": article, "reading_minutes": 1, "neighbors": {"previous": None, "next": None, "series": False}}}
            return BeautifulSoup(template.render(page=page, config={"extra": {"giscus": giscus}}), "html.parser")

        first = json.loads(render().select_one("[data-giscus-config]")["data-giscus-config"])
        article["category_id"] = "research"
        article["subcategory_id"] = "new-place"
        moved = json.loads(render().select_one("[data-giscus-config]")["data-giscus-config"])
        self.assertEqual(first["term"], "nagisa:stable-note")
        self.assertEqual(first, moved)
        article["comments"] = False
        self.assertIsNone(render().select_one("[data-giscus-config]"))
        article["comments"] = True
        giscus["enabled"] = False
        self.assertIsNone(render().select_one("[data-giscus-config]"))


if __name__ == "__main__":
    unittest.main()
