from __future__ import annotations
import re
from pathlib import Path
from bs4 import BeautifulSoup

from .selectors import (
    VISIBILITY_CLASSES, VISIBILITY_IMG_RE,
    GROUPS_META_ITEM_RE, GROUPS_ICON_SRC_RE,
)


def extract_title(soup: BeautifulSoup) -> str | None:
    m = soup.find("meta", attrs={"property": "og:title"})
    if m and m.get("content"):
        return m["content"].strip()

    for pattern in (r"entry-title", r"b-singlepost-title"):
        h = soup.find(["h1", "h2", "h3"], class_=re.compile(pattern))
        if h:
            for span in h.find_all("span", class_=re.compile(r"i-posticon")):
                span.decompose()
            return h.get_text(" ", strip=True) or None
    return None


def extract_tags(soup: BeautifulSoup) -> list[str]:
    """Объединение всех источников тегов с дедупликацией."""
    seen: set[str] = set()
    out: list[str] = []

    def add(t: str) -> None:
        t = t.strip()
        if t and t not in seen:
            seen.add(t)
            out.append(t)

    for m in soup.find_all("meta", attrs={"property": "article:tag"}):
        add(m.get("content") or "")
    for div in soup.find_all(class_="b-singlepost-tags"):
        for a in div.find_all("a"):
            add(a.get_text())
    for a in soup.find_all("a", attrs={"rel": "tag"}):
        add(a.get_text())
    return out


def extract_original_url(soup: BeautifulSoup) -> str | None:
    m = soup.find("link", rel="canonical")
    if m and m.get("href"):
        return m["href"].strip()
    m = soup.find("meta", attrs={"property": "og:url"})
    if m and m.get("content"):
        return m["content"].strip()
    return None


def extract_visibility(soup: BeautifulSoup) -> str:
    """
    public / private / friends / custom.

    Порядок проверок — от самого сильного сигнала к слабому:

    1) custom friends group:
         <li class="b-singlepost-meta-item-groups"> с «Custom friends groups: …»
         или иконка icon_groups.gif;
    2) стандартные классы i-posticon-* и иконки icon_*.gif;
    3) по умолчанию public (в ЖЖ публичные посты иконку не показывают).
    """
    if soup.find("li", class_=GROUPS_META_ITEM_RE):
        return "custom"
    for img in soup.find_all("img", src=True):
        if GROUPS_ICON_SRC_RE.search(img["src"]):
            return "custom"

    for span in soup.find_all("span", class_=True):
        for c in span.get("class") or []:
            if c in VISIBILITY_CLASSES:
                return VISIBILITY_CLASSES[c]
    for img in soup.find_all("img", src=True):
        if (m := VISIBILITY_IMG_RE.search(img["src"])):
            v = m.group(1).lower()
            return "custom" if v == "groups" else v
    return "public"


def extract_id(path: Path, soup: BeautifulSoup) -> int | None:
    """Цифровой id поста: из canonical URL, иначе из имени файла."""
    url = extract_original_url(soup)
    if url:
        m = re.search(r"/(\d+)\.html(?:$|[?#])", url)
        if m:
            return int(m.group(1))
    if path.stem.isdigit():
        return int(path.stem)
    return None