"""Скан/поиск постов, next_id, теги."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
import html as _html
import re

_TAG_RE = re.compile(r'<[^>]+>')


def _plain_text(s: str) -> str:
    """Грубо, но быстро вытаскивает текст из HTML-фрагмента поста.

    Регулярка не идеальна для «плохого» HTML (незакрытые теги, `>` внутри
    комментариев), но для поиска по содержимому постов — 99% случаев.
    """
    if not s:
        return ""
    return _html.unescape(_TAG_RE.sub(' ', s))


def iter_json_files(root: Path):
    for p in root.rglob("*.json"):
        if p.name.endswith(".bak"):
            continue
        if p.is_file():
            yield p


def extract_post(p: Path, root: Path) -> dict[str, Any] | None:
    """Прочитать один JSON-пост и вернуть «лёгкое» представление для сайдбара."""
    try:
        with p.open(encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        return None

    pid = d.get("id")
    if not isinstance(pid, int) or pid <= 0:
        try:
            pid = int(p.stem)
        except ValueError:
            return None

    meta = d.get("meta_fields") or {}
    title = str(d.get("title") or "")
    datetime_str = str(d.get("datetime") or "")
    tags = [str(t) for t in (d.get("tags") or [])]
    music = str(meta.get("music") or "")

    article = d.get("article") or {}
    visible = str(article.get("visible_html") or "")
    cut_parts = [str(c.get("html") or "") for c in (article.get("cuts") or [])]
    body_text = _plain_text(visible + "\n" + "\n".join(cut_parts))

    # Единый lowercased-индекс: заголовок + музыка + теги + дата + id
    # + plain text видимого тела и тела под катом.
    search_blob = " ".join(
        [title, music, " ".join(tags), datetime_str, str(pid), body_text]
    ).lower()

    return {
        "id": pid,
        "title": title,
        "datetime": datetime_str,
        "tags": tags,
        "visibility": str(d.get("visibility") or ""),
        "music": music,
        "relpath": str(p.relative_to(root)),
        "search_blob": search_blob,
    }


def find_post_path(root: Path, post_id: int) -> Path | None:
    fname = f"{post_id}.json"
    for p in root.rglob(fname):
        if p.is_file():
            return p
    return None


def scan_posts(root: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in iter_json_files(root):
        post = extract_post(p, root)
        if post is not None:
            out.append(post)
    out.sort(key=lambda x: x["datetime"], reverse=True)
    return out


def collect_tags(root: Path) -> list[str]:
    tags: set[str] = set()
    for p in iter_json_files(root):
        try:
            with p.open(encoding="utf-8") as f:
                d = json.load(f)
            tags.update(str(t) for t in (d.get("tags") or []))
        except Exception:
            continue
    return sorted(tags)


def next_id(root: Path) -> int:
    max_id = 0
    for p in iter_json_files(root):
        try:
            with p.open(encoding="utf-8") as f:
                v = json.load(f).get("id")
            if isinstance(v, int) and v > 0:
                max_id = max(max_id, v)
                continue
        except Exception:
            pass
        try:
            max_id = max(max_id, int(p.stem))
        except ValueError:
            pass
    return max_id + 1