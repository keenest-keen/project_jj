from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from typing import Any

from .pipeline import parse_file


def _trunc(s: str, n: int) -> str:
    return s if len(s) <= n else s[:n] + f"  …(+{len(s)-n})"


def _indent(text: str, prefix: str = "    ") -> str:
    return "\n".join(prefix + line for line in text.splitlines())


def pretty_print(path: Path, rec: dict[str, Any], full: bool) -> None:
    n = 10**9 if full else 400
    print(f"=== {path} ===")
    print(f"  title:        {rec.get('title')!r}")
    print(f"  datetime:     {rec.get('datetime')!r}")
    print(f"  original_url: {rec.get('original_url')!r}")
    print(f"  visibility:   {rec.get('visibility')!r}")
    print(f"  tags:         {', '.join(rec.get('tags') or []) or '—'}")
    for k, v in (rec.get("meta_fields") or {}).items():
        print(f"  {k:<13}{v!r}")

    art = rec.get("article")
    if not art:
        print("  <тело не найдено>\n")
        return

    cuts = art["cuts"]
    print(f"  cut-блоков: {len(cuts)}")
    print("  --- visible_html ---")
    print(_indent(_trunc(art["visible_html"], n)))
    for i, c in enumerate(cuts, 1):
        print(f"  --- cut[{i}] id={c['id']} ---")
        print(_indent(_trunc(c["html"], n)))
    print()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="extractor")
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--full", action="store_true")
    args = ap.parse_args(argv)

    rc = 0
    for f in args.files:
        if not f.is_file():
            print(f"!! не файл: {f}", file=sys.stderr); rc = 1; continue
        rec = parse_file(f)
        if args.json:
            print(json.dumps(rec, ensure_ascii=False, indent=2))
        else:
            pretty_print(f, rec, full=args.full)
    return rc


if __name__ == "__main__":
    sys.exit(main())