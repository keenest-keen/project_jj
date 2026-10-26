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

# --- доступ к модулям generator (он написан в терминах top-level `config`, `core.*`) ---
_HERE = Path(__file__).resolve()
_SRC = _HERE.parent.parent
_GEN = _SRC / "generator"
for _p in (str(_SRC), str(_GEN)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from .config import MOOD_DIR, DEFAULT_EXPAND_TEXT
from .model import PostDraft
from .storage import (
    collect_tags,
    extract_post,
    find_post_path,
    iter_json_files,
    next_id,
    scan_posts,
)
from .writer import save_post

try:
    import config as gen_config
    from core.models import Post as GenPost, Cut as GenCut
    from core.renderer import make_env, base_context
    from core.cuts import render_full
    _GEN_OK = True
    _GEN_ERR = ""
except Exception as _e:  # noqa: BLE001
    _GEN_OK = False
    _GEN_ERR = f"{type(_e).__name__}: {_e}"


class PosterBridge:
    def __init__(self, json_dir: Path):
        self.json_dir = json_dir
        self._bootstrap_files: list[Path] | None = None

    # ---------- bootstrap с прогрессом ----------

    def bootstrap_count(self) -> int:
        """Список файлов кэшируется — последующие bootstrap_batch его переиспользуют."""
        self._bootstrap_files = list(iter_json_files(self.json_dir))
        return len(self._bootstrap_files)

    def bootstrap_batch(self, offset: int, limit: int = 100) -> dict[str, Any]:
        if self._bootstrap_files is None:
            self._bootstrap_files = list(iter_json_files(self.json_dir))
        total = len(self._bootstrap_files)
        chunk = self._bootstrap_files[offset:offset + int(limit)]
        posts: list[dict[str, Any]] = []
        for p in chunk:
            post = extract_post(p, self.json_dir)
            if post is not None:
                posts.append(post)
        done = offset + len(chunk) >= total
        return {
            "posts": posts,
            "offset": offset,
            "batch_size": len(chunk),
            "done": done,
            "total": total,
        }

    # ---------- справочники ----------

    def list_posts(self) -> list[dict[str, Any]]:
        return scan_posts(self.json_dir)

    def list_tags(self) -> list[str]:
        return collect_tags(self.json_dir)

    def list_mood_icons(self) -> list[dict[str, str]]:
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

    def new_post(self, next_id_hint: int = 0) -> dict[str, Any]:
        try:
            nid = int(next_id_hint) if next_id_hint else 0
        except (TypeError, ValueError):
            nid = 0
        if nid <= 0:
            nid = next_id(self.json_dir)
        return {
            "id": nid,
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
        draft = PostDraft.from_json(raw, fallback_id=int(post_id))
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
            return {"ok": False, "error": f"generator недоступен для превью: {_GEN_ERR}"}
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

            css_path = Path(gen_config.STATIC_DIR) / "css" / "style.css"
            css = css_path.read_text(encoding="utf-8") if css_path.is_file() else ""
            html = re.sub(
                r'<link\s+[^>]*rel="stylesheet"[^>]*>',
                lambda _m: f"<style>\n{css}\n</style>",
                html,
                count=1,
            )

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

            return {"ok": True, "html": html}
        except Exception as e:  # noqa: BLE001
            return {
                "ok": False,
                "error": f"{type(e).__name__}: {e}",
                "trace": traceback.format_exc(),
            }