"""Модель поста: dataclass, конвертация в/из формы, JSON."""
from __future__ import annotations
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any

from .config import DEFAULT_CUT_ID, DEFAULT_EXPAND_TEXT, DEFAULT_VISIBILITY

# <cut id="cutid1"/> / <cut id="cutid1" /> — как в extractor
CUT_RE = re.compile(r'\s*<cut\s+id="([^"]+)"\s*/?>\s*', re.IGNORECASE)
CUT_AT_END_RE = re.compile(r'<cut\s+id="[^"]+"\s*/?>\s*$', re.IGNORECASE)


@dataclass
class Cut:
    id: str = DEFAULT_CUT_ID
    html: str = ""
    expand_text: str = DEFAULT_EXPAND_TEXT


@dataclass
class PostDraft:
    id: int
    title: str
    datetime: str            # ISO, "YYYY-MM-DDTHH:MM:SS"
    visibility: str = DEFAULT_VISIBILITY
    original_url: str = ""
    tags: list[str] = field(default_factory=list)
    meta_fields: dict[str, str] = field(default_factory=dict)
    visible_html: str = ""
    cuts: list[Cut] = field(default_factory=list)

    # ---------- построение из данных формы ----------

    @classmethod
    def from_form(cls, f: dict[str, Any]) -> "PostDraft":
        # id
        try:
            pid = int(f.get("id") or 0)
        except (TypeError, ValueError):
            raise ValueError("id должен быть целым числом")
        if pid <= 0:
            raise ValueError("id должен быть > 0")

        title = str(f.get("title") or "").strip()
        if not title:
            raise ValueError("заголовок обязателен")

        dt_raw = str(f.get("datetime") or "").strip()
        if not dt_raw:
            raise ValueError("дата/время обязательны")
        try:
            dt = datetime.fromisoformat(dt_raw)
        except ValueError:
            raise ValueError(f"неверный формат даты: {dt_raw!r}")
        dt_iso = dt.isoformat(timespec="seconds")

        # теги: строка "a,b,c" или уже список
        tags_raw = f.get("tags") or []
        if isinstance(tags_raw, str):
            tags_raw = tags_raw.split(",")
        tags = [str(t).strip() for t in tags_raw if str(t).strip()]
        # сохраняем порядок, убираем дубли
        seen: set[str] = set()
        tags = [t for t in tags if not (t in seen or seen.add(t))]

        # meta_fields
        meta: dict[str, str] = {}
        for key in ("mood", "mood_icon", "music", "location"):
            v = str(f.get(key) or "").strip()
            if v:
                meta[key] = v

        # article
        visible = str(f.get("visible_html") or "").strip()
        has_cut = bool(f.get("has_cut"))
        cuts: list[Cut] = []
        if has_cut:
            cut_html = str(f.get("cut_html") or "").strip()
            expand = str(f.get("expand_text") or DEFAULT_EXPAND_TEXT).strip() or DEFAULT_EXPAND_TEXT
            cut_id = DEFAULT_CUT_ID
            if not CUT_AT_END_RE.search(visible):
                if visible:
                    visible += "\n"
                visible += f'<cut id="{cut_id}" />'
            cuts.append(Cut(id=cut_id, html=cut_html, expand_text=expand))

        return cls(
            id=pid,
            title=title,
            datetime=dt_iso,
            visibility=str(f.get("visibility") or DEFAULT_VISIBILITY),
            original_url=str(f.get("original_url") or "").strip(),
            tags=tags,
            meta_fields=meta,
            visible_html=visible,
            cuts=cuts,
        )

    # ---------- чтение существующего JSON ----------

    @classmethod
    def from_json(cls, raw: dict[str, Any]) -> "PostDraft":
        article = raw.get("article") or {}
        cuts = [
            Cut(
                id=str(c.get("id") or DEFAULT_CUT_ID),
                html=str(c.get("html") or ""),
                expand_text=str(c.get("expand_text") or DEFAULT_EXPAND_TEXT),
            )
            for c in (article.get("cuts") or [])
        ]
        return cls(
            id=int(raw.get("id") or 0),
            title=str(raw.get("title") or ""),
            datetime=str(raw.get("datetime") or ""),
            visibility=str(raw.get("visibility") or DEFAULT_VISIBILITY),
            original_url=str(raw.get("original_url") or ""),
            tags=[str(t) for t in (raw.get("tags") or [])],
            meta_fields={k: str(v) for k, v in (raw.get("meta_fields") or {}).items() if v},
            visible_html=str(article.get("visible_html") or ""),
            cuts=cuts,
        )

    # ---------- запись в JSON ----------

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "id": self.id,
            "title": self.title,
            "datetime": self.datetime,
        }
        if self.original_url:
            out["original_url"] = self.original_url
        out["visibility"] = self.visibility
        out["tags"] = list(self.tags)
        out["meta_fields"] = dict(self.meta_fields)
        out["article"] = {
            "visible_html": self.visible_html,
            "cuts": [asdict(c) for c in self.cuts],
        }
        return out

    # ---------- представление для формы ----------

    def to_form_view(self) -> dict[str, Any]:
        # Убираем <cut/> из visible_html — в форме он разнесён по панелям.
        visible = CUT_RE.sub("", self.visible_html).rstrip()
        has_cut = bool(self.cuts)
        cut_html = ""
        expand = DEFAULT_EXPAND_TEXT
        if has_cut:
            # Несколько катов (редкий legacy-случай) — склеиваем через <hr/>.
            cut_html = "\n<hr/>\n".join(c.html for c in self.cuts)
            expand = self.cuts[0].expand_text or DEFAULT_EXPAND_TEXT
        dt_input = ""
        try:
            dt_input = datetime.fromisoformat(self.datetime).strftime("%Y-%m-%dT%H:%M")
        except (ValueError, TypeError):
            pass
        return {
            "id": self.id,
            "title": self.title,
            "datetime": dt_input,
            "visibility": self.visibility,
            "original_url": self.original_url,
            "tags": list(self.tags),
            "mood": self.meta_fields.get("mood", ""),
            "mood_icon": self.meta_fields.get("mood_icon", ""),
            "music": self.meta_fields.get("music", ""),
            "location": self.meta_fields.get("location", ""),
            "visible_html": visible,
            "has_cut": has_cut,
            "cut_html": cut_html,
            "expand_text": expand,
            "cuts_count": len(self.cuts),
        }