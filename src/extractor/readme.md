# Extractor — разбор сохранённых HTML-постов ЖЖ

Модуль читает локальные HTML-страницы блога (один файл = один пост)
и превращает их в нормализованный словарь Python / JSON: метаданные,
тело поста, содержимое катов. Дальше этот словарь пойдёт в рендерер.

Поддерживается единственный формат вёрстки ЖЖ — современный (2026, но
не менялся лет 15):
(`<article class="…b-singlepost-body…">`).

Зависимости: `beautifulsoup4`, `lxml`.

```bash
pip install beautifulsoup4 lxml
```

## Структура

```
src/extractor/
  __init__.py     публичное API: parse_file
  __main__.py     `python3 -m extractor …`
  batch.py        `python3 -m extractor.batch …`
  cleanup.py      нормализация href и имён иконок
  cli.py          argparse и pretty_print
  pipeline.py     parse_file
  selectors.py    все классы и регэкспы ЖЖ (править здесь)
  dates.py        разбор <time> и метатегов
  cuts.py         split_cuts
  meta.py         Music / Mood / Location из <li class="b-singlepost-meta-*">
  fields.py       title, tags, original_url, visibility
```

**Где что искать при правке:**

| Хочу поменять…                                     | Файл                |
|----------------------------------------------------|---------------------|
| Селекторы классов ЖЖ, регулярки                    | `selectors.py`      |
| Логику даты/времени                                | `dates.py`          |
| Как распознаётся кат, виджет ката, якоря `cutidN`  | `cuts.py`           |
| Извлечение Music / Mood / Location                 | `meta.py`           |
| title / tags / visibility / canonical              | `fields.py`         |
| Порядок сборки записи                              | `pipeline.py`       |
| Пакетный проход и статистика                       | `batch.py`          |

## Что извлекается

```
title          str | None
datetime       ISO-8601
original_url   из <link rel="canonical"> или og:url
visibility     "public" | "private" | "friends"      (по умолчанию public)
tags           список, объединение всех источников
meta_fields    dict: music, mood, mood_icon, location, …
               *_icon — короткое имя без URL: "sad", "tired", "confused"
article:
  visible_html HTML поста; на месте каждого ката — маркер <cut id="cutidN" />
  cuts         [ {id: "cutidN", html: "..."} ]  — содержимое под катом
```

`full_html` эквивалентен склейке `visible_html` + `cuts`.

## Нормализация данных

При извлечении применяются две правки (модуль `cleanup.py`):

- **Битые ссылки.** ЖЖ-обёртка иногда сохраняет ссылки вида
  `href="http://username.livejournal.com/http://vk.com/…"`.
  Внешний префикс `http://<host>/` удаляется; корректные ссылки
  остаются без изменений. Применяется к телу поста целиком —
  значит, и к `visible_html`, и к `cuts[].html`.
- **Имена иконок.** `mood_icon` / … хранятся как
  короткое имя файла без URL и расширения: `"sad"`, `"tired"`, `"confused"`.

### Терминология

- **Содержимое ката** — то, что видно после раскрытия. Лежит в `cuts`.
  В текущем корпусе (1530 постов) сохранено у всех 540 постов с катом.
- **Текст ката** — подпись ссылки-раскрывашки. Лежит только в свёрнутом
  виде, который в текущем корпусе не встречается. Все посты сохранены
  развёрнутыми — значит, текст ката потерян везде.
- **Место ката** — маркер `<cut id="cutidN" />` в `visible_html`.

## Конвенции для рендерера

- На месте маркера `<cut id="…" />` рендерер вставляет литерал
  `more...` (или `<!--more-->`), поскольку текст ката потерян
  для всех постов в корпусе.
- `visibility` со значением `None` трактуется как `public`.

## Запуск

```bash
source .venv/bin/activate
cd src
python3 -m extractor.batch ../data_test --cache ../cache
```

Один или несколько файлов:

```bash
cd src
python3 -m extractor ../data/22800.html
python3 -m extractor ../data/22800.html ../data/391010.html --full
python3 -m extractor ../data/22800.html --json > /tmp/one.json
```

Пакетный проход по папке (рекурсивно):

```bash
cd src
python3 -m extractor.batch ../data                    # только статистика
python3 -m extractor.batch ../data --cache ../cache   # + JSON-кэш
python3 -m extractor.batch ../data --cache ../cache --incremental --quiet
```

Пакетный режим:

- обходит `../data` рекурсивно, ищет `*.html`;
- для каждого файла пишет JSON **по тому же** относительному пути
  в `--cache` (e.g. `../cache/2007/10/13429.json`), создавая подпапки;
- `--incremental` пропускает файлы, чей кэш не старее исходника;
- печатает сводку: распределение по `visibility`, сколько без
  `datetime` / `title` / `tags`, сколько с катами, etc.

## Кэш как регрессионный тест

JSON-кэш сериализуется детерминированно. При изменении селекторов
полезно прогнать `--cache` в отдельную папку и сделать `diff -r`
со старой — сразу видно, на каких постах поведение поменялось.

## Известные ограничения

- «Текущее настроение» / «музыка» извлекаются из пар
  `<strong class="b-singlepost-meta-title">Label:</strong>` внутри
  `<li class="b-singlepost-meta-item">`. Незнакомые метки попадают
  в `meta_fields` как есть (например, `location`, `weather`).