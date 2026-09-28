"""Парсинг <cut id="..."/> и превращение его в <details>."""
from __future__ import annotations
import re
import logging

from core.models import Post
import config
import html

log = logging.getLogger(__name__)

CUT_RE = re.compile(r'<cut\s+id="([^"]+)"\s*/?>', re.IGNORECASE)


def render_visible(post: Post) -> str:
    """visible_html с заменёнными <cut/> на <details>.

    Каждый <cut id="X"/> -> <details><summary>expand_text</summary>html</details>.
    Если для id нет соответствующего Cut — оставляем пустой details
    (и логируем предупреждение).
    """
    cut_map = {c.id: c for c in post.cuts}

    def repl(m: re.Match) -> str:
        cid = m.group(1)
        cut = cut_map.get(cid)
        if cut is None:
            log.warning("пост %s: кат %r без содержимого", post.stem, cid)
            return ""
        label_expand = cut.expand_text or config.DEFAULT_EXPAND_TEXT
        label_collapse = cut.collapse_text or config.DEFAULT_COLLAPSE_TEXT
        # summary не должен содержать html, иначе браузер его стрипает странно
        return (
            f'<details class="cut">'
            f'<summary class="cut-summary" '
            f'  data-expand="{html.escape(label_expand, quote=True)}" '
            f'  data-collapse="{html.escape(label_collapse, quote=True)}">'
            f'</summary>'
            f'<div class="cut-content">{cut.html}</div>'
            f'</details>'
        )

    return CUT_RE.sub(repl, post.visible_html)


def render_full(post: Post) -> str:
    """Полный текст поста — visible_html + все cuts по порядку."""
    # простая стратегия: visible_html, потом все cuts подряд.
    parts = [post.visible_html]
    for c in post.cuts:
        parts.append(c.html)
    return "".join(parts)