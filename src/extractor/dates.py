from __future__ import annotations
import re
from bs4 import BeautifulSoup
from .selectors import (
    ISO_RE, TIME_IN_TEXT_RE,
    YMD_PATH_RE, YM_PATH_RE, Y_PATH_RE,
)


def iso_from_text(txt: str) -> str | None:
    m = ISO_RE.search(txt)
    if not m:
        return None
    y, mo, d, hh, mm, ss = m.groups()
    if hh is None:
        return f"{y}-{mo}-{d}"
    return f"{y}-{mo}-{d}T{int(hh):02d}:{mm}:{ss or '00'}"


def _date_from_hrefs(time_el) -> tuple[str | None, str | None, str | None]:
    y = mo = d = None
    for a in time_el.find_all("a"):
        href = a.get("href") or ""
        if (m := YMD_PATH_RE.search(href)):
            y, mo, d = m.groups(); continue
        if (m := YM_PATH_RE.search(href)):
            y, mo = m.groups(); continue
        if (m := Y_PATH_RE.search(href)):
            y = m.group(1)
    return y, mo, d


def extract_datetime(soup: BeautifulSoup) -> str | None:
    # 1. <time class="…published…">
    for t in soup.find_all("time"):
        cls = " ".join(t.get("class") or [])
        if "published" not in cls:
            continue
        txt = re.sub(r"\s+", " ", t.get_text(" ", strip=True))
        if (iso := iso_from_text(txt)):
            return iso
        y, mo, d = _date_from_hrefs(t)
        if y and mo and d:
            tm = TIME_IN_TEXT_RE.search(txt)
            if tm:
                return f"{y}-{mo}-{d}T{int(tm.group(1)):02d}:{tm.group(2)}:{tm.group(3) or '00'}"
            return f"{y}-{mo}-{d}"

    # 2. метатеги
    for prop in ("article:published_time", "og:published_time"):
        m = soup.find("meta", attrs={"property": prop})
        if m and m.get("content"):
            return m["content"].strip()

    return None