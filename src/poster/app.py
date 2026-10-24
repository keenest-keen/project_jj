"""Точка входа pywebview."""
from __future__ import annotations
from pathlib import Path

import webview

from .bridge import PosterBridge
from .config import UI_DIR


def run(json_dir: Path) -> None:
    bridge = PosterBridge(json_dir)
    url = (UI_DIR / "index.html").resolve().as_uri()
    webview.create_window(
        f"Poster — {json_dir}",
        url=url,
        js_api=bridge,
        width=1440,
        height=900,
        min_size=(1000, 640),
    )
    webview.start(gui="qt")