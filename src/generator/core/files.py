"""Копирование статики в output."""
from __future__ import annotations
import shutil
from pathlib import Path

import config


def copy_static() -> None:
    """Копирует static/* в output/blog/ с сохранением структуры."""
    src = config.STATIC_DIR
    dst = config.OUTPUT_DIR
    if not src.exists():
        return
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def ensure_post_img_dirs(posts) -> None:
    """Создаёт пустые папки под картинки каждого поста."""
    for p in posts:
        if not p.datetime:
            continue
        d = (config.OUTPUT_DIR / config.POST_IMG_DIR
             / f"{p.year:04d}" / f"{p.month:02d}" / p.stem)
        d.mkdir(parents=True, exist_ok=True)