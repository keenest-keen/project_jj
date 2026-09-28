"""Главная страница + пагинация."""
from __future__ import annotations
from pathlib import Path

from jinja2 import Environment

from core.models import Post
from core.paginator import paginate
from core.stats import Stats
import config

from core.renderer import write_page, base_context

def generate(env, posts_desc, stats):
    pages = paginate(posts_desc)
    tpl = env.get_template("list.html")
    from core import runtime

    for page in pages:
        html = tpl.render(
            page=page,
            page_kind="index",
            page_title=None,
            is_private=runtime.IS_PRIVATE,
            **base_context(base="", nav_active="index.html"),
        )
        write_page(config.OUTPUT_DIR / page.url, html)
        stats.pages_index += 1