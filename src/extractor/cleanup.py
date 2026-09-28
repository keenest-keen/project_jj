from __future__ import annotations
import re


# href="http://<host>/http://…" или href="http://<host>/https://…"
# — лишний внешний префикс от ЖЖ-обёртки. Убираем его, оставляя
# внутренний URL со собственной схемой.
_BROKEN_HREF_RE = re.compile(
    r'(href=["\'])(https?://[^/"\'\s]+/)(?=https?://)',
    re.I,
)

# .../sad.gif  ->  sad
_ICON_NAME_RE = re.compile(r"/([^/]+)\.\w+$")


def normalize_hrefs(html: str) -> str:
    """Чинит битые href, порождённые ЖЖ-обёрткой ссылок."""
    return _BROKEN_HREF_RE.sub(r"\1", html)


def short_icon_name(url: str) -> str:
    """Из '…/classic/sad.gif' делает 'sad'. Если не распозналось — отдаёт как есть."""
    m = _ICON_NAME_RE.search(url)
    return m.group(1) if m else url