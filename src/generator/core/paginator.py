"""Универсальная пагинация."""
from __future__ import annotations
from typing import Callable

from core.models import Post, Page
import config


def paginate(
    posts: list[Post],
    per_page: int = config.POSTS_PER_PAGE,
    url_for: Callable[[int], str] | None = None,
) -> list[Page]:
    """
    posts — уже отсортированы «свежие первыми».
    url_for(offset) -> относительный URL страницы (или путь файла) для offset.
    """
    if url_for is None:
        url_for = config.pagination_url

    total = len(posts)
    pages: list[Page] = []
    offsets = list(range(0, total, per_page)) or [0]

    for i, off in enumerate(offsets):
        chunk = posts[off:off + per_page]
        prev_url = url_for(offsets[i - 1]) if i > 0 else None
        next_url = url_for(offsets[i + 1]) if i + 1 < len(offsets) else None
        pages.append(Page(
            posts=chunk,
            offset=off,
            prev_url=prev_url,   # более новые
            next_url=next_url,   # более старые
            url=url_for(off),
        ))
    return pages