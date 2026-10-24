"""python -m poster [--json-dir PATH]"""
from __future__ import annotations
import argparse
from pathlib import Path

from .config import JSON_DIR


def main() -> None:
    p = argparse.ArgumentParser(prog="python -m poster")
    p.add_argument(
        "--json-dir",
        type=Path,
        default=None,
        help=f"папка с JSON-постами (по умолчанию: {JSON_DIR})",
    )
    args = p.parse_args()

    json_dir = (args.json_dir or JSON_DIR).expanduser().resolve()
    if not json_dir.exists() or not json_dir.is_dir():
        raise SystemExit(f"error: {json_dir} не существует или не является папкой")

    from .app import run  # импортируем здесь, чтобы --help работал без webview
    run(json_dir)


if __name__ == "__main__":
    main()