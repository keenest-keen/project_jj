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

  function setMode(which, mode) {              // mode: 'rich' | 'raw'
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

  async function refreshSidebar() {
    state.posts = await window.pywebview.api.list_posts();
    renderSidebar($('#search').value);
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
    const view = await window.pywebview.api.new_post();
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
    const parts = [`✓ сохранено: ${res.path}`];
    if (res.backup) parts.push(`бэкап: ${res.backup}`);
    setStatus(parts.join(' · '), 'ok');
    await refreshSidebar();
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

  // -------------------- init --------------------

  async function init() {
    await waitForPywebview();
    const Quill = await loadQuill();
    if (!Quill) { setStatus('Не удалось загрузить Quill', 'err'); return; }
    initEditors(Quill);

    state.tags = await window.pywebview.api.list_tags();
    state.moodIcons = await window.pywebview.api.list_mood_icons();
    state.expandDefault = await window.pywebview.api.default_expand_text();

    $('#tags-list').innerHTML = state.tags.map((t) => `<option value="${esc(t)}"></option>`).join('');
    const moodSel = $('#f-mood-icon');
    for (const icon of state.moodIcons) {
      const opt = document.createElement('option');
      opt.value = icon.name;
      opt.textContent = icon.name;
      moodSel.appendChild(opt);
    }
    moodSel.addEventListener('change', updateMoodPreview);

    await refreshSidebar();

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
    });
  });
})();