from __future__ import annotations
from pathlib import Path
from typing import Any
from bs4 import BeautifulSoup

from .selectors import NEW_ARTICLE_CLASS_RE
from .dates import extract_datetime
from .cuts import split_cuts
from .cleanup import normalize_hrefs
from .meta import extract_meta_fields
from .fields import (
    extract_title, extract_tags, extract_original_url, extract_visibility,
    extract_id, extract_comments,
)


def parse_file(path: Path) -> dict[str, Any]:
    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="replace"), "lxml")
    article = soup.find("article", class_=NEW_ARTICLE_CLASS_RE)
    if not article:
        return {"_error": "не найден article.b-singlepost-body"}

    inner = normalize_hrefs(article.decode_contents().strip())
    visible_html, cuts = split_cuts(inner)

    return {
        "id":           extract_id(path, soup),
        "title":        extract_title(soup),
        "datetime":     extract_datetime(soup),
        "original_url": extract_original_url(soup),
        "visibility":   extract_visibility(soup),
        "tags":         extract_tags(soup),
        "comments":     extract_comments(soup),
        "meta_fields":  extract_meta_fields(soup),
        "article": {
            "visible_html": visible_html,
            "cuts":         cuts,
        },
    }