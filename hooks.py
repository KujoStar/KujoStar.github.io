"""MkDocs lifecycle. All generated files go into site/, never docs/."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from site_builder import Site

site = None


def on_pre_build(config):
    global site
    site = Site(ROOT, config)


def on_page_markdown(markdown, page, config, files):
    return site.prepare(markdown, page)


def on_page_content(html, page, config, files):
    return site.capture(html, page)


def on_post_build(config):
    site.write_output()


def on_serve(server, config, builder):
    server.watch(str(ROOT / "data"))
    server.watch(str(ROOT / "overrides"))
    server.watch(str(ROOT / "site_builder.py"))
    return server
