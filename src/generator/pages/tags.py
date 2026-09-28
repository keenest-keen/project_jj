"""tags.html и страницы по тегам с пагинацией."""
from __future__ import annotations

from jinja2 import Environment

from core.models import Post, TagInfo
from core.paginator import paginate
from core.stats import Stats
from core import runtime
import config
from core.renderer import write_page, base_context
from core import runtime

def generate(env, posts_desc, tags, stats):
    _gen_tags_index(env, tags, stats)
    _gen_tag_pages(env, tags, stats)


def _gen_tags_index(env, tags, stats):
    tpl = env.get_template("tags.html")
    counts = [t.count for t in tags] or [1]
    cmin, cmax = min(counts), max(counts)

    def size(c):
        if cmax == cmin:
            return config.TAG_FONT_MAX
        return config.TAG_FONT_MIN + (config.TAG_FONT_MAX - config.TAG_FONT_MIN) * (c - cmin) / (cmax - cmin)

    tags_view = [{"tag": t, "size": round(size(t.count), 1)} for t in tags]

    # tags.html в корне
    html = tpl.render(tags_view=tags_view, is_private=runtime.IS_PRIVATE,
                      **base_context(base="", nav_active="tags.html"))
    write_page(config.OUTPUT_DIR / "tags.html", html)

    # tag/index.html (дубль, с правильным base)
    html = tpl.render(tags_view=tags_view, is_private=runtime.IS_PRIVATE,
                      **base_context(base="../", nav_active="tags.html"))
    write_page(config.OUTPUT_DIR / config.TAG_DIR_NAME / "index.html", html)

    stats.pages_static += 2


def _gen_tag_pages(env, tags, stats):
    tpl = env.get_template("list.html")
    for tag in tags:
        ordered = list(reversed(tag.posts))

        def url_for(offset, slug=tag.slug):
            return config.tag_url(slug, offset)

        pages = paginate(ordered, url_for=url_for)
        for page in pages:
            html = tpl.render(
                page=page,
                page_kind="tag",
                page_title=tag.name,
                is_private=runtime.IS_PRIVATE,
                **base_context(base="../", nav_active="tags.html"),
            )
            write_page(config.OUTPUT_DIR / page.url, html)
            stats.pages_tag += 1