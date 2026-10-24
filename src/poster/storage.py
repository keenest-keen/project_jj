"""Скан/поиск постов, next_id, теги."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any


def _iter_json_files(root: Path):
    for p in root.rglob("*.json"):
        # пропускаем .json.bak и прочий мусор
        if p.name.endswith(".bak"):
            continue
        if p.is_file():
            yield p


def find_post_path(root: Path, post_id: int) -> Path | None:
    """Ищем <id>.json рекурсивно (посты могут лежать в подпапках)."""
    fname = f"{post_id}.json"
    for p in root.rglob(fname):
        if p.is_file():
            return p
    return None


def scan_posts(root: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in _iter_json_files(root):
        try:
            with p.open(encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            continue
        try:
            pid = int(d.get("id") or p.stem)
        except (TypeError, ValueError):
            continue
        out.append({
            "id": pid,
            "title": str(d.get("title") or ""),
            "datetime": str(d.get("datetime") or ""),
            "tags": [str(t) for t in (d.get("tags") or [])],
            "visibility": str(d.get("visibility") or ""),
            "relpath": str(p.relative_to(root)),
        })
    out.sort(key=lambda x: x["datetime"], reverse=True)
    return out


def collect_tags(root: Path) -> list[str]:
    tags: set[str] = set()
    for p in _iter_json_files(root):
        try:
            with p.open(encoding="utf-8") as f:
                d = json.load(f)
            tags.update(str(t) for t in (d.get("tags") or []))
        except Exception:
            continue
    return sorted(tags)


def next_id(root: Path) -> int:
    max_id = 0
    for p in _iter_json_files(root):
        try:
            max_id = max(max_id, int(p.stem))
        except ValueError:
            pass
        try:
            with p.open(encoding="utf-8") as f:
                v = json.load(f).get("id")
            if isinstance(v, int):
                max_id = max(max_id, v)
        except Exception:
            pass
    return max_id + 1