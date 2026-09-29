"""Точка входа.

Использование:
    python main.py                              # только public
    python main.py --private                    # все посты (public + private + friends)
    python main.py --json-dir PATH              # откуда читать JSON
    python main.py --output-dir PATH            # куда писать результат
    python main.py --json-dir a --output-dir b -v
"""
from __future__ import annotations
import argparse
import logging
import shutil
import sys
from pathlib import Path
import time

import config
from core import files, runtime
from core.loader import load_all
from core.renderer import make_env
from core.stats import Stats
from core.tags import collect_tags

from pages import index as page_index
from pages import post  as page_post
from pages import tags  as page_tags
from pages import profile as page_profile


def parse_args():
    ap = argparse.ArgumentParser(description="Генератор блога")
    ap.add_argument("--private", action="store_true",
                    help="включить private/friends посты")
    ap.add_argument("--json-dir", type=Path, default=None,
                    help="папка с JSON-постами (по умолчанию из config.py)")
    ap.add_argument("--output-dir", type=Path, default=None,
                    help="папка для сгенерированного сайта (по умолчанию из config.py)")
    ap.add_argument("-v", "--verbose", action="store_true")
    return ap.parse_args()


def setup_logging(verbose: bool):
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )


def apply_overrides(args) -> None:
    """Переопределяет пути в config значениями из командной строки."""
    if args.json_dir is not None:
        config.JSON_DIR = args.json_dir.expanduser().resolve()
    if args.output_dir is not None:
        config.OUTPUT_DIR = args.output_dir.expanduser().resolve()


def clean_output():
    if config.OUTPUT_DIR.exists():
        shutil.rmtree(config.OUTPUT_DIR)
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def collect_stats(posts, stats: Stats):
    stats.posts_total = len(posts)
    for p in posts:
        if p.visibility == "public":
            stats.posts_public += 1
        elif p.visibility == "private":
            stats.posts_private += 1
        elif p.visibility == "friends":
            stats.posts_friends += 1
        else:
            stats.posts_custom += 1
        for t in p.tags:
            stats.tags[t] += 1
        m = p.meta_fields.get("mood")
        if m:
            stats.moods[m] += 1
        mi = p.meta_fields.get("mood_icon")
        if mi:
            stats.mood_icons[mi] += 1
        mu = p.meta_fields.get("music")
        if mu:
            stats.music[mu] += 1
        loc = p.meta_fields.get("location")
        if loc:
            stats.locations[loc] += 1
        if p.datetime:
            stats.years[p.datetime.year] += 1


def main():
    args = parse_args()
    setup_logging(args.verbose)
    runtime.IS_PRIVATE = args.private
    apply_overrides(args)

    allowed = {"public", "private", "friends"} if args.private else config.PUBLIC_VISIBILITIES

    log = logging.getLogger("main")
    log.info("режим: %s", "PRIVATE (все посты)" if args.private else "PUBLIC")
    log.info("JSON_DIR:   %s", config.JSON_DIR)
    log.info("OUTPUT_DIR: %s", config.OUTPUT_DIR)

    if not config.JSON_DIR.exists():
        log.error("нет папки с JSON: %s", config.JSON_DIR)
        sys.exit(1)

    start_time = time.perf_counter()
    log.info("читаю посты")
    posts = load_all(config.JSON_DIR, allowed)

    for p in posts:
        p.filename = config.POST_FILENAME_TPL.format(stem=p.stem)

    # «свежие первыми»
    posts_desc = list(reversed(posts))

    stats = Stats()
    collect_stats(posts, stats)

    env = make_env()

    log.info("чищу output")
    clean_output()

    log.info("копирую static/")
    files.copy_static()

    # log.info("создаю папки под картинки постов")
    # files.ensure_post_img_dirs(posts)

    log.info("генерирую главную")
    page_index.generate(env, posts_desc, stats)

    log.info("генерирую страницы постов")
    page_post.generate(env, posts_desc, stats)

    log.info("генерирую теги")
    tags_list = collect_tags(posts)
    page_tags.generate(env, posts_desc, tags_list, stats)

    log.info("генерирую профиль")
    page_profile.generate(env, posts_desc, stats)

    end_time = time.perf_counter()
    execution_time = end_time - start_time
    log.info(f"время выполнения функции: {execution_time:.1f} секунд")

    print(stats.report())


if __name__ == "__main__":
    main()