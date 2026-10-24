"""Атомарная запись JSON + бэкап при перезаписи."""
from __future__ import annotations
import json
import os
import tempfile
from pathlib import Path

from .config import BACKUP_SUFFIX
from .model import PostDraft
from .storage import find_post_path


def save_post(root: Path, draft: PostDraft) -> tuple[Path, Path | None]:
    """Возвращает (путь_к_файлу, путь_к_бэкапу|None)."""
    existing = find_post_path(root, draft.id)
    if existing is not None:
        target = existing
        backup = existing.with_suffix(existing.suffix + BACKUP_SUFFIX)  # <id>.json.bak
        backup.write_bytes(existing.read_bytes())
    else:
        target = root / f"{draft.id}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        backup = None

    data = draft.to_json()
    fd, tmp_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp_name, target)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    return target, backup