from __future__ import annotations
import re
from bs4 import BeautifulSoup
from .selectors import VISIBILITY_CLASSES, VISIBILITY_IMG_RE


def extract_title(soup: BeautifulSoup) -> str | None:
    m = soup.find("meta", attrs={"property": "og:title"})
    if m and m.get("content"):
        return m["content"].strip()

    for pattern in (r"entry-title", r"b-singlepost-title"):
        h = soup.find(["h1", "h2", "h3"], class_=re.compile(pattern))
        if h:
            # <h1> иногда содержит <span class="i-posticon-*"> — его выкидываем
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
    public / private / friends.
    В ЖЖ публичные посты иконку не показывают вовсе, поэтому
    «маркер не найден» == public.
    """
    for span in soup.find_all("span", class_=True):
        for c in span.get("class") or []:
            if c in VISIBILITY_CLASSES:
                return VISIBILITY_CLASSES[c]
    for img in soup.find_all("img", src=True):
        if (m := VISIBILITY_IMG_RE.search(img["src"])):
            return m.group(1).lower()
    return "public"