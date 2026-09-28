"""Агрегация тегов."""
from __future__ import annotations
from collections import defaultdict

from core.models import Post, TagInfo
import config


def slugify_tag(name: str) -> str:
    return name.replace(" ", config.TAG_SPACE_REPLACEMENT)


def collect_tags(posts: list[Post]) -> list[TagInfo]:
    """Регистрозависимая агрегация. Сортировка задаётся в config."""
    by_name: dict[str, TagInfo] = {}
    for p in posts:
        for t in p.tags:
            info = by_name.get(t)
            if info is None:
                info = TagInfo(name=t, slug=slugify_tag(t))
                by_name[t] = info
            info.count += 1
            info.posts.append(p)

    items = list(by_name.values())
    if config.TAGS_SORT_BY == "count_desc":
        items.sort(key=lambda ti: (-ti.count, ti.name.lower()))
    else:
        items.sort(key=lambda ti: ti.name.lower())
    return items