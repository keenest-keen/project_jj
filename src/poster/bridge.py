"""JS-мост: все методы, которые может звать UI через window.pywebview.api."""
from __future__ import annotations

import base64
import json
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

# --- даём доступ к модулям generator (он написан в терминах top-level `config`,
#     `core.*`, поэтому нужен именно src/generator в sys.path) ---
_HERE = Path(__file__).resolve()
_SRC = _HERE.parent.parent               # .../src
_GEN = _SRC / "generator"
for _p in (str(_SRC), str(_GEN)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from .config import MOOD_DIR, DEFAULT_EXPAND_TEXT
from .model import PostDraft
from .storage import collect_tags, find_post_path, next_id, scan_posts
from .writer import save_post


# --- ленивая проверка генератора: если его нет или он сломан — превью просто скажет об этом ---
try:
    import config as gen_config                              # src/generator/config.py
    from core.models import Post as GenPost, Cut as GenCut   # src/generator/core/models.py
    from core.renderer import make_env, base_context         # src/generator/core/renderer.py
    from core.cuts import render_full                        # src/generator/core/cuts.py
    _GEN_OK = True
    _GEN_ERR = ""
except Exception as _e:                                      # noqa: BLE001
    _GEN_OK = False
    _GEN_ERR = f"{type(_e).__name__}: {_e}"


class PosterBridge:
    def __init__(self, json_dir: Path):
        self.json_dir = json_dir

    # ---------- справочники ----------

    def list_posts(self) -> list[dict[str, Any]]:
        return scan_posts(self.json_dir)

    def list_tags(self) -> list[str]:
        return collect_tags(self.json_dir)

    def list_mood_icons(self) -> list[dict[str, str]]:
        """[{name, url}] — url как data:image/gif;base64,…, работает и на file://, и на http://"""
        if not MOOD_DIR.exists():
            return []
        out: list[dict[str, str]] = []
        for p in sorted(MOOD_DIR.glob("*.gif")):
            try:
                data = base64.b64encode(p.read_bytes()).decode("ascii")
            except OSError:
                continue
            out.append({"name": p.stem, "url": f"data:image/gif;base64,{data}"})
        return out

    def next_id(self) -> int:
        return next_id(self.json_dir)

    def default_expand_text(self) -> str:
        return DEFAULT_EXPAND_TEXT

    # ---------- посты ----------

    def new_post(self) -> dict[str, Any]:
        return {
            "id": next_id(self.json_dir),
            "title": "",
            "datetime": datetime.now().strftime("%Y-%m-%dT%H:%M"),
            "visibility": "public",
            "original_url": "",
            "tags": [],
            "mood": "",
            "mood_icon": "",
            "music": "",
            "location": "",
            "visible_html": "",
            "has_cut": False,
            "cut_html": "",
            "expand_text": DEFAULT_EXPAND_TEXT,
            "cuts_count": 0,
        }

    def load_post(self, post_id: int) -> dict[str, Any]:
        path = find_post_path(self.json_dir, int(post_id))
        if path is None:
            return {"ok": False, "error": f"пост {post_id} не найден в {self.json_dir}"}
        try:
            with path.open(encoding="utf-8") as f:
                raw = json.load(f)
        except Exception as e:
            return {"ok": False, "error": f"не читается {path.name}: {e}"}
        draft = PostDraft.from_json(raw)
        return {
            "ok": True,
            "post": draft.to_form_view(),
            "relpath": str(path.relative_to(self.json_dir)),
        }

    def save_post(self, form_data: dict[str, Any]) -> dict[str, Any]:
        try:
            draft = PostDraft.from_form(form_data)
        except ValueError as e:
            return {"ok": False, "error": str(e)}
        try:
            path, backup = save_post(self.json_dir, draft)
        except Exception as e:
            return {"ok": False, "error": f"{type(e).__name__}: {e}"}
        return {
            "ok": True,
            "path": str(path.relative_to(self.json_dir)),
            "backup": str(backup.relative_to(self.json_dir)) if backup else None,
        }

    # ---------- превью через настоящие шаблоны generator ----------

    def render_preview(self, form_data: dict[str, Any]) -> dict[str, Any]:
        if not _GEN_OK:
            return {
                "ok": False,
                "error": f"generator недоступен для превью: {_GEN_ERR}",
            }
        try:
            draft = PostDraft.from_form(form_data)
        except ValueError as e:
            return {"ok": False, "error": str(e)}

        try:
            dt = datetime.fromisoformat(draft.datetime)
            cuts = [
                GenCut(id=c.id, html=c.html, expand_text=c.expand_text)
                for c in draft.cuts
            ]
            post = GenPost(
                stem=str(draft.id),
                path=Path(f"{draft.id}.json"),
                title=draft.title or None,
                datetime=dt,
                original_url=draft.original_url or None,
                visibility=draft.visibility,
                tags=list(draft.tags),
                meta_fields=dict(draft.meta_fields),
                visible_html=draft.visible_html,
                cuts=cuts,
                filename=f"{draft.id}.html",
            )

            env = make_env()
            tpl = env.get_template("post.html")
            html = tpl.render(
                post=post,
                full_html=render_full(post),
                newer=None,
                older=None,
                is_private=False,
                show_original=False,
                **base_context(base="", nav_active=""),
            )

            # 1) В iframe (srcdoc) относительные пути не работают — инлайним CSS.
            css_path = Path(gen_config.STATIC_DIR) / "css" / "style.css"
            css = css_path.read_text(encoding="utf-8") if css_path.is_file() else ""
            html = re.sub(
                r'<link\s+[^>]*rel="stylesheet"[^>]*>',
                lambda _m: f"<style>\n{css}\n</style>",
                html,
                count=1,
            )

            # 2) mood-иконка в _meta.html приходит как img/mood/<name>.gif — тоже
            #    inline'им в data:URL, иначе она не загрузится в srcdoc-iframe.
            mood_dir = Path(gen_config.STATIC_DIR) / gen_config.MOOD_ICONS_DIR

            def _icon_data_url(m: re.Match) -> str:
                f = mood_dir / f"{m.group(1)}.gif"
                if not f.is_file():
                    return m.group(0)
                data = base64.b64encode(f.read_bytes()).decode("ascii")
                return f'src="data:image/gif;base64,{data}"'

            html = re.sub(
                r'src="(?:\.\./)?img/mood/([^"]+)\.gif"',
                _icon_data_url,
                html,
            )

            # 3) Абсолютные /media/... пути (постовые картинки) в srcdoc не
            #    разрешить без знания, откуда их раздаёт сервер. Оставляем как есть —
            #    в реальной странице они загрузятся, в превью — нет (это ок).
            return {"ok": True, "html": html}
        except Exception as e:  # noqa: BLE001
            return {
                "ok": False,
                "error": f"{type(e).__name__}: {e}",
                "trace": traceback.format_exc(),
            }