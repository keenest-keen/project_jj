/* Poster UI. Всё общение с Python — через window.pywebview.api.* */

(() => {
  'use strict';

  const $ = (s) => document.querySelector(s);
  const $$ = (s) => Array.from(document.querySelectorAll(s));

  const state = {
    posts: [],
    tags: [],
    moodIcons: [],
    quill: { visible: null, cut: null },
    rawMode: { visible: false, cut: false },
    currentId: null,
    dirty: false,
    expandDefault: 'читать далее...',
    nextId: 0,
  };

  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[c]);

  function setStatus(msg, kind = '') {
    const el = $('#status');
    el.textContent = msg || '';
    el.className = 'status ' + kind;
    clearTimeout(setStatus._t);
    if (msg) setStatus._t = setTimeout(() => { el.textContent = ''; el.className = 'status'; }, 6000);
  }

  // -------------------- loading overlay --------------------

  function showLoading(text = 'Загрузка…') {
    $('#loading-overlay').hidden = false;
    $('#loading-text').textContent = text;
    $('#loading-bar-wrap').hidden = true;
    $('#loading-bar').style.width = '0%';
  }
  function updateLoadingProgress(current, total) {
    if (!total) return;
    $('#loading-bar-wrap').hidden = false;
    const pct = Math.min(100, Math.round(current / total * 100));
    $('#loading-bar').style.width = pct + '%';
    $('#loading-text').textContent = `Загрузка постов: ${current} / ${total} (${pct}%)`;
  }
  function hideLoading() {
    $('#loading-overlay').hidden = true;
  }

  // -------------------- asset loaders --------------------

  function loadScript(src) {
    return new Promise((res, rej) => {
      const s = document.createElement('script');
      s.src = src;
      s.onload = () => res();
      s.onerror = () => rej(new Error('script: ' + src));
      document.head.appendChild(s);
    });
  }
  function loadCSS(href) {
    return new Promise((res, rej) => {
      const l = document.createElement('link');
      l.rel = 'stylesheet'; l.href = href;
      l.onload = () => res();
      l.onerror = () => rej(new Error('css: ' + href));
      document.head.appendChild(l);
    });
  }

  async function loadQuill() {
    try {
      await Promise.all([
        loadScript('vendor/quill/quill.js'),
        loadCSS('vendor/quill/quill.snow.css'),
      ]);
      return window.Quill;
    } catch (e) {
      console.warn('local Quill не загрузился, пробуем CDN', e);
      await Promise.all([
        loadScript('https://cdn.jsdelivr.net/npm/quill@2.0.3/dist/quill.js'),
        loadCSS('https://cdn.jsdelivr.net/npm/quill@2.0.3/dist/quill.snow.css'),
      ]);
      return window.Quill;
    }
  }

  function waitForPywebview() {
    return new Promise((res) => {
      if (window.pywebview && window.pywebview.api) return res();
      window.addEventListener('pywebviewready', () => res(), { once: true });
    });
  }

  // -------------------- editors (Quill + raw) --------------------

  const TOOLBAR = [
    [{ header: [1, 2, 3, false] }],
    ['bold', 'italic', 'underline', 'strike'],
    [{ color: [] }, { background: [] }],
    [{ list: 'ordered' }, { list: 'bullet' }],
    ['blockquote', 'code-block'],
    ['link', 'image'],
    ['clean'],
  ];

  function initEditors(Quill) {
    state.quill.visible = new Quill('#editor-visible', { theme: 'snow', modules: { toolbar: TOOLBAR } });
    state.quill.cut = new Quill('#editor-cut', { theme: 'snow', modules: { toolbar: TOOLBAR } });
    state.quill.visible.on('text-change', () => { state.dirty = true; });
    state.quill.cut.on('text-change', () => { state.dirty = true; });

    $$('.mode-toggle').forEach((toggle) => {
      const which = toggle.dataset.target;
      toggle.querySelectorAll('.mode-btn').forEach((btn) => {
        btn.addEventListener('click', () => setMode(which, btn.dataset.mode));
      });
    });
  }

  function getEditorHTML(which) {
    if (state.rawMode[which]) return $(`#editor-${which}-raw`).value;
    return state.quill[which].root.innerHTML;
  }

  function setEditorHTML(which, html) {
    const v = html || '';
    if (state.rawMode[which]) $(`#editor-${which}-raw`).value = v;
    else state.quill[which].clipboard.dangerouslyPasteHTML(v);
  }

  function setMode(which, mode) {
    const isRaw = mode === 'raw';
    if (state.rawMode[which] === isRaw) return;
    const html = getEditorHTML(which);
    state.rawMode[which] = isRaw;
    const quillHost = $(`#editor-${which}`);
    const rawArea = $(`#editor-${which}-raw`);
    if (isRaw) {
      rawArea.value = html;
      rawArea.hidden = false;
      quillHost.hidden = true;
    } else {
      rawArea.hidden = true;
      quillHost.hidden = false;
      state.quill[which].clipboard.dangerouslyPasteHTML(html);
    }
    $$(`.mode-toggle[data-target="${which}"] .mode-btn`).forEach((b) => {
      b.classList.toggle('active', b.dataset.mode === mode);
    });
    state.dirty = true;
  }

  // -------------------- sidebar --------------------

  function renderSidebar(filter = '') {
    const list = $('#post-list');
    const q = filter.trim().toLowerCase();
    const items = state.posts.filter((p) => {
      if (!q) return true;
      return (p.title || '').toLowerCase().includes(q)
          || (p.datetime || '').toLowerCase().includes(q)
          || (p.music || '').toLowerCase().includes(q)
          || (p.tags || []).some((t) => t.toLowerCase().includes(q))
          || String(p.id).includes(q);
    });
    list.innerHTML = items.map((p) => `
      <div class="post-item${p.id === state.currentId ? ' active' : ''}" data-id="${p.id}" title="${esc(p.relpath)}">
        <div class="title">${esc(p.title || '(без заголовка)')}</div>
        <div class="sub">${esc(p.id)} · ${esc((p.datetime || '').replace('T', ' ').slice(0, 16))}${p.tags?.length ? ' · ' + esc(p.tags.join(', ')) : ''}</div>
      </div>
    `).join('');
    $('#sidebar-status').textContent = `постов: ${items.length} из ${state.posts.length}`;
    list.querySelectorAll('.post-item').forEach((el) => {
      el.addEventListener('click', () => {
        const id = Number(el.dataset.id);
        if (id === state.currentId) return;
        if (!guardUnsaved()) return;
        loadPost(id);
      });
    });
  }

  // -------------------- form --------------------

  function collectFormData() {
    const tags = $('#f-tags').value.split(',').map((s) => s.trim()).filter(Boolean);
    return {
      id: Number($('#f-id').value),
      title: $('#f-title').value,
      datetime: $('#f-datetime').value,
      visibility: $('#f-visibility').value,
      original_url: '',
      tags,
      mood: $('#f-mood').value,
      mood_icon: $('#f-mood-icon').value,
      music: $('#f-music').value,
      location: $('#f-location').value,
      visible_html: getEditorHTML('visible'),
      has_cut: $('#f-has-cut').checked,
      cut_html: getEditorHTML('cut'),
      expand_text: $('#f-expand-text').value || state.expandDefault,
    };
  }

  function fillForm(view) {
    $('#f-id').value = view.id ?? '';
    $('#f-datetime').value = view.datetime || '';
    $('#f-visibility').value = view.visibility || 'public';
    $('#f-title').value = view.title || '';
    $('#f-tags').value = (view.tags || []).join(', ');
    $('#f-mood').value = view.mood || '';
    $('#f-mood-icon').value = view.mood_icon || '';
    $('#f-music').value = view.music || '';
    $('#f-location').value = view.location || '';
    $('#f-has-cut').checked = !!view.has_cut;
    $('#f-expand-text').value = view.expand_text || state.expandDefault;
    setEditorHTML('visible', view.visible_html || '');
    setEditorHTML('cut', view.cut_html || '');
    toggleCutFields();
    updateMoodPreview();

    const warn = $('#cut-warning');
    if ((view.cuts_count || 0) > 1) {
      warn.hidden = false;
      warn.textContent = `⚠️ у поста было ${view.cuts_count} ката — они склеены в один через <hr/>. При сохранении останется один кат.`;
    } else {
      warn.hidden = true;
      warn.textContent = '';
    }

    state.currentId = view.id ?? null;
    state.dirty = false;
    renderSidebar($('#search').value);
  }

  function toggleCutFields() {
    $('#cut-fields').hidden = !$('#f-has-cut').checked;
  }

  function updateMoodPreview() {
    const name = $('#f-mood-icon').value;
    const img = $('#f-mood-icon-preview');
    const found = state.moodIcons.find((m) => m.name === name);
    if (found) { img.src = found.url; img.hidden = false; }
    else { img.removeAttribute('src'); img.hidden = true; }
  }

  function guardUnsaved() {
    if (!state.dirty) return true;
    return window.confirm('Есть несохранённые изменения. Продолжить без сохранения?');
  }

  // -------------------- actions --------------------

  async function newPost() {
    if (!guardUnsaved()) return;
    const view = await window.pywebview.api.new_post(state.nextId || 0);
    fillForm(view);
    setStatus(`Новый пост, id=${view.id}`, '');
  }

  async function loadPost(id) {
    const res = await window.pywebview.api.load_post(id);
    if (!res.ok) { setStatus('Ошибка: ' + res.error, 'err'); return; }
    fillForm(res.post);
    setStatus(`Загружен ${res.relpath}`, '');
  }

  async function saveCurrent(ev) {
    ev?.preventDefault?.();
    const payload = collectFormData();
    const res = await window.pywebview.api.save_post(payload);
    if (!res.ok) { setStatus('Ошибка: ' + res.error, 'err'); return; }
    state.dirty = false;
    state.currentId = payload.id;

    // обновляем локальный список без повторного скана всех файлов
    const idx = state.posts.findIndex((p) => p.id === payload.id);
    const entry = {
      id: payload.id,
      title: payload.title,
      datetime: payload.datetime,
      tags: payload.tags,
      visibility: payload.visibility,
      music: payload.music,
      relpath: res.path,
    };
    if (idx >= 0) state.posts[idx] = entry;
    else state.posts.push(entry);
    state.posts.sort((a, b) => (b.datetime || '').localeCompare(a.datetime || ''));
    if (payload.id >= state.nextId) state.nextId = payload.id + 1;

    // обновляем datalist тегов
    const newTags = new Set(state.tags);
    for (const t of payload.tags) newTags.add(t);
    state.tags = [...newTags].sort();
    $('#tags-list').innerHTML = state.tags.map((t) => `<option value="${esc(t)}"></option>`).join('');

    renderSidebar($('#search').value);

    const parts = [`✓ сохранено: ${res.path}`];
    if (res.backup) parts.push(`бэкап: ${res.backup}`);
    setStatus(parts.join(' · '), 'ok');
  }

  async function showPreview() {
    const data = collectFormData();
    setStatus('Рендерю превью…', '');
    const res = await window.pywebview.api.render_preview(data);
    if (!res.ok) {
      setStatus('Превью: ' + res.error, 'err');
      if (res.trace) console.error(res.trace);
      return;
    }
    $('#preview-frame').srcdoc = res.html;
    $('#preview-modal').hidden = false;
    setStatus('', '');
  }

  // -------------------- bootstrap --------------------

  async function bootstrap() {
    showLoading('Сканирую посты…');
    await new Promise((r) => setTimeout(r, 0));  // дать браузеру отрисовать оверлей

    const total = await window.pywebview.api.bootstrap_count();
    if (!total) {
      state.posts = [];
      state.tags = [];
      state.nextId = 1;
      hideLoading();
      return;
    }

    updateLoadingProgress(0, total);
    const allPosts = [];
    let offset = 0;
    const LIMIT = 100;
    while (offset < total) {
      const batch = await window.pywebview.api.bootstrap_batch(offset, LIMIT);
      allPosts.push(...batch.posts);
      offset += batch.batch_size;
      updateLoadingProgress(offset, total);
      if (batch.done) break;
      await new Promise((r) => setTimeout(r, 0));  // дать UI перерисоваться
    }

    allPosts.sort((a, b) => (b.datetime || '').localeCompare(a.datetime || ''));
    state.posts = allPosts;
    state.tags = [...new Set(allPosts.flatMap((p) => p.tags))].sort();
    state.nextId = allPosts.reduce((m, p) => Math.max(m, p.id), 0) + 1;

    hideLoading();
  }

  // -------------------- init --------------------

  async function init() {
    await waitForPywebview();

    // параллельно грузим Quill (CDN или локально) — пока bootstrap ещё не начался
    const [Quill, moodIcons, expandDefault] = await Promise.all([
      loadQuill(),
      window.pywebview.api.list_mood_icons(),
      window.pywebview.api.default_expand_text(),
    ]);
    if (!Quill) { setStatus('Не удалось загрузить Quill', 'err'); hideLoading(); return; }

    state.moodIcons = moodIcons;
    state.expandDefault = expandDefault;

    initEditors(Quill);
    $('#tags-list').innerHTML = '';
    const moodSel = $('#f-mood-icon');
    for (const icon of state.moodIcons) {
      const opt = document.createElement('option');
      opt.value = icon.name;
      opt.textContent = icon.name;
      moodSel.appendChild(opt);
    }
    moodSel.addEventListener('change', updateMoodPreview);

    // основной долгий шаг — с прогрессом
    await bootstrap();

    $('#tags-list').innerHTML = state.tags
      .map((t) => `<option value="${esc(t)}"></option>`)
      .join('');

    // события
    $('#btn-new').addEventListener('click', newPost);
    $('#search').addEventListener('input', (e) => renderSidebar(e.target.value));
    $('#f-has-cut').addEventListener('change', toggleCutFields);
    $('#form').addEventListener('submit', saveCurrent);
    $('#btn-preview').addEventListener('click', showPreview);
    $('#btn-preview-close').addEventListener('click', () => { $('#preview-modal').hidden = true; });
    $('#preview-modal').addEventListener('click', (e) => {
      if (e.target.id === 'preview-modal') $('#preview-modal').hidden = true;
    });

    ['f-id','f-title','f-datetime','f-visibility','f-tags','f-mood','f-mood-icon','f-music','f-location','f-expand-text']
      .forEach((id) => $('#' + id).addEventListener('input', () => { state.dirty = true; }));

    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
        e.preventDefault();
        saveCurrent();
      }
    });

    await newPost();
    state.dirty = false;
  }

  window.addEventListener('DOMContentLoaded', () => {
    init().catch((e) => {
      console.error(e);
      setStatus('Ошибка инициализации: ' + e.message, 'err');
      hideLoading();
    });
  });
})();