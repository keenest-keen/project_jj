# poster — редактор JSON-постов для generator

Десктопное приложение (pywebview + Quill) для создания и редактирования
JSON-файлов постов, которые читает `generator`. Убирает ручное редактирование
`visible_html` и ручное экранирование — за это отвечает `json.dump(...,
ensure_ascii=False, indent=2)`.

## Что умеет

- создать новый пост → `<id>.json`
- отредактировать существующий (с бэкапом `<id>.json.bak`)
- WYSIWYG-редактор (Quill 2) + переключение в raw HTML
- автодополнение тегов, селект `mood_icon` из `generator/static/img/mood/*.gif`
- превью с боевым `generator/static/css/style.css`
- сайдбар со списком постов + поиск по id / заголовку / тегу / дате
- поддержка вложенных подпапок (`cache_test/2021/9/8787.json`)
- переключатель «видимый / HTML» у каждой панели (Quill ↔ raw-HTML)
- картинка-превью выбранной `mood_icon` рядом с выпадающим списком
- превью поста рендерится **через настоящие шаблоны generator** (`post.html`
  + `base.html` + `_meta.html` + inline CSS из `generator/static/css/style.css`) —
  то есть 1:1 как в блоге после `python -m generator`


## Структура `src/poster/`

init.py
main.py python -m poster [--json-dir PATH]
app.py webview.create_window + webview.start
bridge.py JS-мост: list_posts / load_post / save_post / …
config.py пути (импорт из generator.config) + дефолты
model.py PostDraft: from_form / from_json / to_json / to_form_view
storage.py скан постов, поиск по id, next_id, теги
writer.py атомарная запись + .bak при перезаписи
vendor.py python -m poster.vendor — скачать Quill локально
ui/
index.html каркас (сайдбар + форма + модалка превью)
poster.css стили
poster.js вся логика UI (Quill, форма, fetch → pywebview.api)
vendor/quill/ quill.js + quill.snow.css (оффлайн)

## Запуск

### Первый раз

```bash
cd src

# опционально, но рекомендуется (нужен интернет — иначе poster.js подтянет Quill с CDN при первом запуске)
python -m poster.vendor

# ставим pywebview с Qt-бэкендом (pywebview входит в extras)
pip install "pywebview[qt]"
```

pywebview[qt] включает сам pywebview — отдельно ставить не нужно.
Если хочется GTK вместо Qt — см. раздел «Траблшутинг».

Каждый следующий запуск
```bash
cd src
python -m poster                          # JSON_DIR из generator.config
python -m poster --json-dir ../cache_test # явная папка
python -m poster --json-dir ../cache_prod
```

## Рабочий цикл

-    python -m poster --json-dir ../cache_test
-    правим/создаём пост → «Сохранить» → cache_test/<id>.json
-    python -m generator ... — генерим HTML
-    python -m http.server 8080 из корня, открываем http://localhost:8080/blog

## Поведенческие детали

- Куда пишется файл. Новый пост — в корень --json-dir. Существующий — туда, откуда был прочитан (включая вложенные cache/2021/9/…).
- Кат. Один. <cut id="cutid1" /> дописывается в конец visible_html автоматически, тело — в cuts[0].html. Старый пост с двумя катами при загрузке склеивается через <hr/> (в UI показывается предупреждение).
- <p> вместо <br/> после правки в Quill — нормально: шаблоны рендерят visible_html через |safe.
- Теги — через запятую, автодополнение из всех постов в --json-dir.
- Ctrl+S = сохранить.
- Бэкап — при перезаписи пишется <id>.json.bak рядом с файлом.
- **Превью.** Рендерится реальным `post.html` из generator; CSS инлайнится,
  mood-иконка инлайнится как `data:gif;base64,…`. Постовые картинки с
  абсолютными путями (`src="/media/...")` в превью **не отображаются** —
  в реальной странице они загрузятся (их отдаёт ваш web-сервер), а внутри
  preview-iframe без базового URL — нет.
- **Режим rich / HTML.** В каждом редакторе есть переключатель:
  «видимый» — Quill (WYSIWYG), «HTML» — plain textarea с сырым HTML.
  При переключении содержимое переносится как есть.

## Траблшутинг

Симптом	Лечение
**GTK cannot be loaded + QT cannot be loaded**	нет GUI-бэкенда → pip install "pywebview[qt]"
**Qt: ошибки xcb на Ubuntu**	sudo apt install libxcb-cursor0
**Qt: Fontconfig error: Cannot load default config**	sudo apt install fontconfig (обычно некритично)
**Пустое/белое окно**	открыть UI-URL во внешнем браузере (адрес пишется в консоль), смотреть ошибки. Обычно — нет ui/vendor/quill/quill.js и нет интернета
**Хочется GTK**	sudo apt install python3-gi gir1.2-webkit2-4.1, пересоздать venv с --system-site-packages, pip install pywebview
