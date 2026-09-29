"""Датаклассы предметной области."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class Cut:
    id: str
    html: str
    expand_text: str = ""     # если пусто — берётся DEFAULT_EXPAND_TEXT
    collapse_text: str = ""   # если пусто — берётся DEFAULT_COLLAPSE_TEXT


@dataclass
class Post:
    stem: str                 # "77645"
    path: Path                # путь к исходному json
    title: Optional[str]
    datetime: Optional[datetime]
    original_url: Optional[str]
    visibility: str           # "public" | "private" | "friends"
    tags: list[str]
    meta_fields: dict[str, str]
    visible_html: str         # с <cut id="..."/> маркерами
    cuts: list[Cut]
    pin: Optional[bool] = False

    # рассчитывается позже
    filename: str = ""        # "77645.html"
    sort_key: int = 0         # числовое значение stem для сортировки

    @property
    def display_title(self) -> str:
        return self.title or "без заголовка"

    @property
    def year(self) -> int:
        return self.datetime.year if self.datetime else 0

    @property
    def month(self) -> int:
        return self.datetime.month if self.datetime else 0


@dataclass
class TagInfo:
    name: str                 # "юмор" — оригинальное написание
    slug: str                 # "юмор" с "_" вместо пробелов
    count: int = 0
    posts: list[Post] = field(default_factory=list)

    @property
    def url(self) -> str:
        from config import tag_url
        return tag_url(self.slug)


@dataclass
class Page:
    """Одна страница пагинации."""
    posts: list[Post]
    offset: int                       # 0, 20, 40...
    prev_url: Optional[str] = None    # на более новые посты
    next_url: Optional[str] = None    # на более старые
    url: str = ""                     # куда сохранять (относительно output)