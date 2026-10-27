"""Пакетный разбор папки с HTML-постами ЖЖ в формате LJSM.

Использование:
    python -m extractor.batch <source_dir> [--output DIR] [--incremental] [--quiet]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .pipeline import parse_file


@dataclass
class BatchStats:
    total: int = 0
    errors: int = 0
    error_files: list[str] = field(default_factory=list)

    by_visibility: dict[str, int] = field(default_factory=dict)

    no_datetime: int = 0
    no_title: int = 0
    no_tags: int = 0

    with_cut_content: int = 0

    total_comments: int = 0

    def update(self, rec: dict[str, Any], *, src: str = "") -> None:
        self.total += 1

        if rec.get("_error"):
            self.errors += 1
            self.error_files.append(src or "?")
            return

        vis = rec.get("visibility") or "unknown"
        self.by_visibility[vis] = self.by_visibility.get(vis, 0) + 1

        if not rec.get("datetime"): self.no_datetime += 1
        if not rec.get("title"):    self.no_title += 1
        if not rec.get("tags"):     self.no_tags += 1

        art = rec.get("article") or {}
        if art.get("cuts"):
            self.with_cut_content += 1

        self.total_comments += int(rec.get("comments") or 0)

    def report(self) -> str:
        lines: list[str] = []
        lines.append(f"Всего файлов:        {self.total}")
        lines.append(f"Ошибок разбора:      {self.errors}")
        for f in self.error_files[:20]:
            lines.append(f"  ! {f}")
        if len(self.error_files) > 20:
            lines.append(f"  … и ещё {len(self.error_files) - 20}")
        lines.append("")

        lines.append("Видимость:")
        for k, v in sorted(self.by_visibility.items()):
            lines.append(f"  {k:<10}{v}")
        lines.append("")

        lines.append(f"Без datetime:        {self.no_datetime}")
        lines.append(f"Без title:           {self.no_title}")
        lines.append(f"Без tags:            {self.no_tags}")
        lines.append("")

        lines.append(f"С содержимым cuts:   {self.with_cut_content}")
        lines.append(f"Всего комментариев:  {self.total_comments}")
        return "\n".join(lines)


def iter_html_files(root: Path) -> Iterable[Path]:
    for p in sorted(root.rglob("*.html")):
        if p.is_file():
            yield p


def _output_path(output_dir: Path, source_dir: Path, src: Path) -> Path:
    return output_dir / src.relative_to(source_dir).with_suffix(".json")


def run_batch(
    source_dir: Path,
    output_dir: Path | None = None,
    *,
    incremental: bool = False,
    quiet: bool = False,
) -> BatchStats:
    st = BatchStats()
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    start_time = time.perf_counter()
    for src in iter_html_files(source_dir):
        out = _output_path(output_dir, source_dir, src) if output_dir else None

        if incremental and out and out.exists() and out.stat().st_mtime >= src.stat().st_mtime:
            try:
                rec = json.loads(out.read_text(encoding="utf-8"))
            except Exception as e:
                if not quiet:
                    print(f"  {src}  ->  output-CORRUPT: {e}", file=sys.stderr)
                continue
            st.update(rec, src=str(src))
            if not quiet:
                print(f"  {src}  ->  (outputed)")
            continue

        try:
            rec = parse_file(src)
        except Exception as e:
            rec = {"_error": f"{type(e).__name__}: {e}"}

        st.update(rec, src=str(src))

        if out:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(
                json.dumps(rec, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        if not quiet:
            print(f"  {src}  ->  {'OK' if not rec.get('_error') else 'FAIL'}")

    end_time = time.perf_counter()
    execution_time = end_time - start_time
    print(f"Время выполнения функции: {execution_time:.1f} секунд")

    return st


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="extractor.batch",
        description="Пакетный разбор HTML-постов ЖЖ.",
    )
    ap.add_argument("source", type=Path, help="папка с .html")
    ap.add_argument("--output", type=Path, default=None,
                    help="куда писать JSON-кэш (по умолчанию не писать)")
    ap.add_argument("--incremental", action="store_true",
                    help="не пересобирать, если кэш свежее источника")
    ap.add_argument("--quiet", action="store_true",
                    help="не печатать строку по каждому файлу")
    ap.add_argument("--no-stats", action="store_true",
                    help="не печатать статистику")
    args = ap.parse_args(argv)

    if not args.source.is_dir():
        print(f"!! не папка: {args.source}", file=sys.stderr)
        return 2

    st = run_batch(
        args.source,
        args.output,
        incremental=args.incremental,
        quiet=args.quiet,
    )

    if not args.no_stats:
        print()
        print(st.report())

    return 0 if st.errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())