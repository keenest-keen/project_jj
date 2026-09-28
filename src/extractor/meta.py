from __future__ import annotations
from bs4 import BeautifulSoup
from .cleanup import short_icon_name


def extract_meta_fields(soup: BeautifulSoup) -> dict[str, str]:
    """Music / Mood / Location и прочие пары из <li class="b-singlepost-meta-*">."""
    mf: dict[str, str] = {}
    for li in soup.find_all("li"):
        label_el = li.find(class_="b-singlepost-meta-title")
        value_el = li.find(class_="b-singlepost-meta-data")
        if not label_el or not value_el:
            continue
        label = label_el.get_text(strip=True).rstrip(":").lower()
        if not label:
            continue
        icon = None
        if (img := value_el.find("img")) and img.get("src"):
            icon = img["src"]
            img.decompose()
        mf[label] = value_el.get_text(" ", strip=True)
        if icon:
            mf[f"{label}_icon"] = short_icon_name(icon)
    return mf