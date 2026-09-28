"""Индивидуальные страницы постов."""
from __future__ import annotations

from jinja2 import Environment

from core.cuts import render_full
from core.models import Post
from core.renderer import write_page, base_context
from core.stats import Stats
from core import runtime
import config


def generate(env: Environment, posts_desc: list[Post], stats: Stats) -> None:
    tpl = env.get_template("post.html")
    # posts_desc — «свежие первыми».
    # newer = более новый пост (i-1), older = более старый (i+1).
    n = len(posts_desc)
    for i, p in enumerate(posts_desc):
        newer = posts_desc[i - 1] if i > 0 else None
        older = posts_desc[i + 1] if i + 1 < n else None
        html = tpl.render(
            post=p,
            full_html=render_full(p),
            newer=newer,
            older=older,
            is_private=runtime.IS_PRIVATE,
            show_original=runtime.IS_PRIVATE and config.SHOW_ORIGINAL_URL_PRIVATE,
            **base_context(base="", nav_active=""),
        )
        write_page(config.OUTPUT_DIR / p.filename, html)
        stats.pages_post += 1