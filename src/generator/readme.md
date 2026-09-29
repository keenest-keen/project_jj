# project jj

Генератор статического блога. Читает JSON-посты (экспорт из ЖЖ-подобного
дневника) и складывает готовые HTML-страницы в `/blog/`, откуда их можно
заливать по FTP в папку `/blog/` на сайте.

## Быстрый старт

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install jinja2

# через дефолты из config.py, только public-посты
python3 main.py

# тест на другой коллекции, в другую папку
python3 main.py --json-dir ~/projects/blog/cache_test --output-dir ~/projects/blog/blog_test -v

# рабочий прогон
python3 main.py --json-dir ../../cache_prod --output-dir ../../blog

# всё, включая private/friends
python3 main.py --json-dir ../../cache_prod --output-dir ../../blog --private -v
```
Результат — в output/blog/. Папка при каждом запуске пересоздаётся с нуля.

В конце генерации в stdout печатается статистика: сколько постов, сколько
файлов каких типов, топ тегов, полный список используемых mood_icon
(удобно проверять, все ли gif'ы на месте).

# Что генерируется

output/blog/
├── index.html                # последние 20 постов
├── index-20.html             # предыдущие 20
├── index-40.html             # ...
├── <post_stem>.html          # страница каждого поста (напр. 77645.html)
├── tags.html                 # облако тегов
├── tag/
│   ├── index.html            # дубль облака тегов
│   ├── <тег>.html            # посты с тегом
│   └── <тег>-20.html         # пагинация по тегу
├── profile.html              # профиль + динамика
├── css/style.css
├── img/
│   ├── background.gif
│   ├── mood/*.gif            # иконки настроений
│   └── posts/YYYY/MM/<stem>/ # папки под картинки постов (создаются пустыми)
└── mood/  (устаревшее, не используется)


# Структура проекта

src/generator/
├── main.py              # точка входа
├── config.py            # ВСЕ настройки: пути, форматы, состав профиля
│
├── core/                # логика
│   ├── models.py        # dataclass'ы Post, Cut, Page, TagInfo
│   ├── loader.py        # чтение JSON-файлов
│   ├── cuts.py          # <cut/> → <details>
│   ├── tags.py          # агрегация тегов, slugify
│   ├── paginator.py     # универсальная пагинация
│   ├── renderer.py      # Jinja2 + фильтры + base_context
│   ├── files.py         # копирование static/, создание папок под картинки
│   ├── stats.py         # сбор статистики
│   └── runtime.py       # флаг IS_PRIVATE
│
├── pages/               # один файл = один тип страницы
│   ├── index.py         # главная + пагинация
│   ├── post.py          # страницы постов
│   ├── tags.py          # tags.html + tag/*.html
│   └── profile.py       # profile.html
│
├── templates/           # Jinja2
│   ├── base.html        # каркас
│   ├── _nav.html        # навигация
│   ├── _meta.html       # мета-блок (location/mood/music/tags)
│   ├── _post_preview.html
│   ├── list.html        # список постов (главная и теги)
│   ├── post.html        # полный пост
│   ├── tags.html
│   └── profile.html
│
└── static/              # копируется в output/blog/
    ├── css/style.css
    └── img/
        ├── background.gif
        └── mood/*.gif

# Формат JSON-поста

Один файл = один пост, имя = числовой id (77645.json).
```json
{
  "title": "заголовок",
  "datetime": "2009-01-15T16:15:00",
  "original_url": "https://...",
  "visibility": "public",
  "tags": ["юмор", "работа"],
  "meta_fields": {
    "location": "на работе",
    "mood": "sleepy",
    "mood_icon": "tired",
    "music": "Marilyn Manson - Sweet Dreams"
  },
  "article": {
    "visible_html": "...текст до ката... <cut id=\"cutid1\"/>",
    "cuts": [
      {"id": "cutid1", "html": "...под катом...", "expand_text": "читать дальше"}
    ]
  }
}
```

*    visibility: public / private / friends. По умолчанию генерируются только public.

*    mood_icon — имя файла без расширения, ищется в img/mood/<icon>.gif.

*    expand_text опционален, иначе используется DEFAULT_EXPAND_TEXT из конфига.

*    Сортировка постов — по числовому значению имени файла (не по datetime).

# Картинки постов

Под каждый пост создаётся папка output/blog/img/posts/YYYY/MM/<stem>/.
В JSON ссылки пишутся относительно корня блога, например:

```html
<img src="img/posts/2009/01/77645/photo.jpg">
```

Картинки генератор не копирует — их надо положить в эту папку вручную
(или отдельным скриптом при миграции с LJ).

# Что и где править

**Дизайн** → templates/*.html и static/css/style.css. Логика не трогается.

**Бизнес-настройки** → config.py:

    пути (JSON_DIR, OUTPUT_DIR),

    POSTS_PER_PAGE, форматы имён файлов,

    DATE_FORMAT, LOCALE,

    состав NAV и PROFILE_FIELDS,

    флаги SHOW_LOCATION / SHOW_MOOD / SHOW_MUSIC,

    TAG_FONT_MIN / TAG_FONT_MAX для облака тегов.

**Логика конкретного типа страницы** → pages/<тип>.py.

**Общая логика → core/*.py** (грузим, режем ката, пагинируем).