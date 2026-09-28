"""profile.html."""
from __future__ import annotations

from jinja2 import Environment

from core.models import Post
from core.renderer import write_page, base_context
from core.stats import Stats
from core import runtime
import config


def generate(env: Environment, posts_desc: list[Post], stats: Stats) -> None:
    tpl = env.get_template("profile.html")
    last = posts_desc[0] if posts_desc else None
    html = tpl.render(
        title=config.PROFILE_TITLE,
        fields=config.PROFILE_FIELDS,
        total_posts=len(posts_desc),
        last_post_date=last.datetime if last else None,
        is_private=runtime.IS_PRIVATE,
        **base_context(base="", nav_active="profile.html"),
    )
    write_page(config.OUTPUT_DIR / "profile.html", html)
    stats.pages_static += 1