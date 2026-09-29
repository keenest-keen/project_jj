"""Чтение JSON-дерева и превращение его в список Post."""
from __future__ import annotations
import json
import logging
from datetime import datetime
from pathlib import Path

from core.models import Cut, Post

log = logging.getLogger(__name__)


def iter_json_files(root: Path):
    """Все *.json рекурсивно, отсортированные по числовому stem."""
    files = list(root.rglob("*.json"))
    def key(p: Path):
        try:
            return int(p.stem)
        except ValueError:
            return 0
    files.sort(key=key)
    return files


def _parse_dt(s: str | None):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        log.warning("не удалось разобрать datetime: %r", s)
        return None


def load_post(path: Path) -> Post | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        log.error("не читается %s: %s", path, e)
        return None

    article = data.get("article") or {}
    visible_html = article.get("visible_html") or ""

    cuts = []
    for c in article.get("cuts") or []:
        cuts.append(Cut(
            id=c.get("id") or "",
            html=c.get("html") or "",
            expand_text=c.get("expand_text") or "",
        ))

    stem = path.stem
    try:
        sort_key = int(stem)
    except ValueError:
        sort_key = 0

    return Post(
        stem=stem,
        path=path,
        title=data.get("title"),
        datetime=_parse_dt(data.get("datetime")),
        original_url=data.get("original_url"),
        visibility=data.get("visibility") or "public",
        tags=list(data.get("tags") or []),
        meta_fields=dict(data.get("meta_fields") or {}),
        visible_html=visible_html,
        cuts=cuts,
        sort_key=sort_key,
        pin=data.get("pin"),
    )


def load_all(root: Path, allowed_visibilities: set[str]) -> list[Post]:
    posts: list[Post] = []
    skipped = 0
    for f in iter_json_files(root):
        p = load_post(f)
        if p is None:
            continue
        if p.visibility not in allowed_visibilities:
            skipped += 1
            continue
        posts.append(p)
    # по возрастанию stem; для отображения будем разворачивать
    posts.sort(key=lambda p: p.sort_key)
    log.info("загружено %d постов (пропущено %d по видимости)", len(posts), skipped)
    return posts