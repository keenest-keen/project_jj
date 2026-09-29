"""Настройка Jinja2 + вспомогательные фильтры."""
from __future__ import annotations
import locale
import logging
from datetime import datetime
from pathlib import Path
from core.cuts import render_visible
from core.tags import slugify_tag

from jinja2 import Environment, FileSystemLoader, select_autoescape

import config

log = logging.getLogger(__name__)


_MONTHS_RU = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая",    6: "июня",    7: "июля",   8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
}


def fmt_date(dt: datetime | None) -> str:
    if not dt:
        return ""
    return f"{dt.day} {_MONTHS_RU[dt.month]} {dt.year}"


def fmt_time(dt: datetime | None) -> str:
    if not dt:
        return ""
    return dt.strftime("%H:%M")


def fmt_date_short(dt: datetime | None) -> str:
    """Для profile: '31 августа 2026'."""
    return fmt_date(dt)


def make_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(config.TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["fmt_date"]        = fmt_date
    env.filters["fmt_time"]        = fmt_time
    env.filters["fmt_date_short"]  = fmt_date_short
    env.filters["render_visible"]  = render_visible
    env.filters["tag_slug"]        = slugify_tag
    return env


def base_context(base: str = "", nav_active: str = "") -> dict:
    """Стандартный набор переменных для base.html и партиалов.

    base — префикс пути от текущей страницы к корню блога:
           '' для страниц в blog/, '../' для страниц в blog/tag/.
    """
    return {
        "base":          base,
        "blog_title":    config.BLOG_TITLE,
        "nav_items":     config.NAV,
        "nav_home_site": config.NAV_HOME_SITE,
        "nav_active":    nav_active,
        "mood_dir":      config.MOOD_ICONS_DIR,
        "generated_at":  config.GENERATED_AT,
        "show_location": config.SHOW_LOCATION,
        "show_mood":     config.SHOW_MOOD,
        "show_music":    config.SHOW_MUSIC,
    }

def write_page(out_path: Path, html: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding=config.ENCODING)