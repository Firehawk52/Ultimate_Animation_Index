(async () => {
  'use strict';
  const catalogResponse = await fetch('catalog.json');
  if (!catalogResponse.ok) throw new Error(`Could not load catalog (${catalogResponse.status})`);
  const CAT = await catalogResponse.json();
  const PAGE_SIZE = 60;
  const STORE = {
    progress: 'uai:progress:v3',
    opinions: 'uai:my-opinions:v1',
    custom: 'uai:custom-titles:v1',
    sources: 'uai:imported-sources:v1',
    meta: 'uai:metadata:v6',
    compact: 'uai:compact:v1',
    favorites: 'uai:favorites:v1',
    ui: 'uai:ui-state:v1',
  };
  const $ = (s, r = document) => r.querySelector(s),
    $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const esc = (v = '') =>
    String(v).replace(
      /[&<>'"]/g,
      (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#039;', '"': '&quot;' })[c],
    );
  const load = (k, d) => {
    try {
      const v = JSON.parse(localStorage.getItem(k));
      return v ?? d;
    } catch {
      return d;
    }
  };
  const save = (k, v) => localStorage.setItem(k, JSON.stringify(v));
  const savedUI = load(STORE.ui, {});
  const adultModes = ['all', 'ecchi', 'erotic', 'hentai', 'gore', 'violence', 'disturbing'];
  const state = {
    visible: PAGE_SIZE,
    compact: load(STORE.compact, false),
    tab: 'master',
    adult: adultModes.includes(savedUI.adult) ? savedUI.adult : 'all',
    server: false,
    keyId: '',
    serverCovers: 0,
    serverCoverTotal: 0,
    serverCoverRunning: false,
  };
  let progress = load(STORE.progress, {}),
    myOpinions = load(STORE.opinions, {}),
    customTitles = load(STORE.custom, []),
    sources = load(STORE.sources, {}),
    meta = load(STORE.meta, {}),
    favorites = load(STORE.favorites, {});
  const META_TTL = 1000 * 60 * 60 * 24 * 30;
  const NO_META = new URLSearchParams(location.search).has('nometa');
  const META_BATCH_SIZE = 12,
    META_BATCH_DELAY = 2200;
  const metaQueue = [],
    metaQueued = new Set();
  let metaPumping = false,
    metaSaveTimer = null;
  const masterItems = CAT.items || [];
  const masterById = new Map(masterItems.map((x) => [x.id, x]));
  const aliasMap = new Map();

  // Catalog identity and local state helpers
  function norm(s = '') {
    return String(s)
      .normalize('NFKD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .replace(/&/g, ' and ')
      .replace(/\b(the|a|an)\b/g, ' ')
      .replace(/[^a-z0-9]+/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }
  masterItems.forEach((x) => {
    aliasMap.set(norm(x.title), x.id);
    (x.aliases || []).forEach((a) => aliasMap.set(norm(a), x.id));
  });
  function canonicalItems() {
    const out = [...masterItems];
    const seen = new Set(masterItems.map((x) => x.id));
    for (const c of customTitles) {
      if (!seen.has(c.id)) {
        out.push(c);
        seen.add(c.id);
      }
    }
    return out;
  }
  function itemById(id) {
    return masterById.get(id) || customTitles.find((x) => x.id === id) || null;
  }
  function pFor(id) {
    return progress[id] || { status: 'Not started', rating: 0, note: '' };
  }
  function ownVerdict(id) {
    return myOpinions[id] || '';
  }
  function isFavorite(id) {
    return favorites[id] === true;
  }
  function toggleFavorite(id) {
    if (!itemById(id)) return;
    if (isFavorite(id)) delete favorites[id];
    else favorites[id] = true;
    save(STORE.favorites, favorites);
    renderMaster({ noMeta: true });
    renderFavorites();
    updateStats();
    toast(isFavorite(id) ? 'Added to favorites' : 'Removed from favorites');
  }
  function sourceOpinions(id) {
    const out = [];
    for (const [sid, s] of Object.entries(sources)) {
      const v = s.opinions?.[id];
      if (v) out.push({ sid, label: s.label, verdict: v });
    }
    return out;
  }
  function sourceBadgesHTML(id) {
    const ops = sourceOpinions(id);
    if (!ops.length) return '';
    return `<div class="source-badges">${ops
      .slice(0, 5)
      .map(
        (o) =>
          `<span class="source-badge ${o.verdict === 'recommend' ? 'rec' : 'no'}">${o.verdict === 'recommend' ? 'RECOMMENDED BY' : 'NOT RECOMMENDED BY'} ${esc(o.label)}</span>`,
      )
      .join('')}${ops.length > 5 ? `<span class="source-badge">+${ops.length - 5}</span>` : ''}</div>`;
  }
  function initials(t) {
    return t
      .replace(/\([^)]*\)/g, '')
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 3)
      .map((x) => x[0])
      .join('')
      .toUpperCase();
  }
  function displayType(x) {
    return x.type || meta[x.id]?.data?.format || 'Animation';
  }
  function liveYear(x) {
    return meta[x.id]?.data?.year || x.year || '—';
  }
  function liveGenres(x) {
    const g = meta[x.id]?.data?.genres;
    return Array.isArray(g) && g.length
      ? g
      : (x.genres || '')
          .split(',')
          .map((v) => v.trim())
          .filter(Boolean);
  }

  // Master-list filtering and sorting
  function populateFilters() {
    const items = canonicalItems();
    fill(
      $('#tierFilter'),
      [...new Set(items.map((x) => x.tier).filter(Boolean))].sort(
        (a, b) =>
          ['S+', 'S', 'A+', 'A', 'B+', 'B', 'CUSTOM'].indexOf(a) -
          ['S+', 'S', 'A+', 'A', 'B+', 'B', 'CUSTOM'].indexOf(b),
      ),
    );
    fill($('#typeFilter'), [...new Set(items.map(displayType).filter(Boolean))].sort());
    fill(
      $('#genreFilter'),
      [
        ...new Set(items.flatMap((x) => (x.genres || '').split(',').map((g) => g.trim())).filter(Boolean)),
      ].sort(),
    );
  }
  function fill(sel, vals) {
    const first = sel.options[0];
    sel.innerHTML = '';
    sel.append(first);
    for (const v of vals) {
      const o = document.createElement('option');
      o.value = v;
      o.textContent = v.toUpperCase();
      sel.append(o);
    }
  }

  const UI_VALUE_FIELDS = [
    'searchInput',
    'tierFilter',
    'typeFilter',
    'genreFilter',
    'statusFilter',
    'sortSelect',
    'collectionSearch',
    'franchiseSearch',
    'favoriteSearch',
  ];
  const UI_CHECKBOX_FIELDS = ['hideCompleted', 'customOnly'];

  function restoreUIState() {
    for (const id of UI_VALUE_FIELDS) {
      const control = $('#' + id);
      const value = savedUI[id];
      if (typeof value !== 'string') continue;
      if (
        control instanceof HTMLSelectElement &&
        ![...control.options].some((option) => option.value === value)
      )
        continue;
      control.value = value;
    }
    for (const id of UI_CHECKBOX_FIELDS) {
      if (typeof savedUI[id] === 'boolean') $('#' + id).checked = savedUI[id];
    }
    $$('.adult-chip').forEach((button) =>
      button.classList.toggle('active', button.dataset.adult === state.adult),
    );
  }

  function saveUIState() {
    const next = { adult: state.adult };
    for (const id of UI_VALUE_FIELDS) next[id] = $('#' + id).value;
    for (const id of UI_CHECKBOX_FIELDS) next[id] = $('#' + id).checked;
    save(STORE.ui, next);
  }

  function filteredMaster() {
    const all = canonicalItems(),
      q = $('#searchInput').value.trim().toLowerCase(),
      tier = $('#tierFilter').value,
      type = $('#typeFilter').value,
      genre = $('#genreFilter').value,
      status = $('#statusFilter').value;
    let out = all.filter((x) => {
      const p = pFor(x.id),
        m = meta[x.id]?.data || {};
      const hay =
        `${x.title} ${(x.aliases || []).join(' ')} ${x.genres || ''} ${x.editorial_note || x.why || ''} ${m.studio || ''}`.toLowerCase();
      if (q && !hay.includes(q)) return false;
      if (tier && x.tier !== tier) return false;
      if (type && displayType(x) !== type) return false;
      if (
        genre &&
        !(x.genres || '')
          .split(',')
          .map((v) => v.trim())
          .includes(genre)
      )
        return false;
      if (status && p.status !== status) return false;
      if ($('#hideCompleted').checked && p.status === 'Completed') return false;
      if ($('#customOnly').checked && !x.custom) return false;
      return true;
    });
    const sort = $('#sortSelect').value;
    const score = (x, k) => x.scores?.[k] ?? x[k] ?? 0;
    if (sort === 'rank')
      out.sort((a, b) => (a.rank ?? 999999) - (b.rank ?? 999999) || a.title.localeCompare(b.title));
    else if (['overall', 'production', 'story', 'emotional'].includes(sort))
      out.sort((a, b) => score(b, sort) - score(a, sort) || (a.rank ?? 999999) - (b.rank ?? 999999));
    else if (sort === 'year')
      out.sort(
        (a, b) =>
          (Number(liveYear(b)) || 0) - (Number(liveYear(a)) || 0) || (a.rank ?? 999999) - (b.rank ?? 999999),
      );
    else if (sort === 'title') out.sort((a, b) => a.title.localeCompare(b.title));
    else if (sort === 'myrating')
      out.sort(
        (a, b) =>
          (pFor(b.id).rating || 0) - (pFor(a.id).rating || 0) || (a.rank ?? 999999) - (b.rank ?? 999999),
      );
    return out;
  }

  function cardHTML(x, { adult = false } = {}) {
    const m = meta[x.id]?.data || {},
      p = pFor(x.id),
      verdict = ownVerdict(x.id),
      cover = m.cover || m.image || '';
    const rank = x.rank ? `#${String(x.rank).padStart(3, '0')}` : 'ADD';
    const tags = liveGenres(x).slice(0, 3);
    const sc = x.scores || {
      overall: x.fit_score || 0,
      production: x.production || 0,
      story: x.story || 0,
      emotional: 7,
    };
    const verdictBadge = verdict
      ? `<span class="own-verdict ${verdict}">${verdict === 'recommend' ? '★ REC' : '× NO'}</span>`
      : '';
    const fav = isFavorite(x.id);
    const content = adult ? contentGuide(x, true) : '';
    return `<article class="title-card" data-id="${esc(x.id)}" tabindex="0">
      <div class="cover">${cover ? `<img loading="lazy" src="${esc(cover)}" alt="${esc(x.title)} cover">` : `<div class="cover-placeholder">${esc(initials(x.title))}</div>`}<span class="rank">${rank}</span><span class="tier">${esc(x.tier || 'CUSTOM')}</span><button class="favorite-toggle ${fav ? 'active' : ''}" data-fav-id="${esc(x.id)}" type="button" aria-label="${fav ? 'Remove from favorites' : 'Add to favorites'}" title="${fav ? 'Remove from favorites' : 'Add to favorites'}">${fav ? '♥' : '♡'}</button>${verdictBadge}</div>
      <div class="card-body"><div class="card-meta">${esc(displayType(x).toUpperCase())} // ${esc(liveYear(x))} // ${esc((m.studio || x.origin || '').toUpperCase())}</div><h3>${esc(x.title)}</h3>
      <div class="tag-row">${tags.map((g) => `<span class="tag">${esc(g)}</span>`).join('')}</div>${sourceBadgesHTML(x.id)}${content}
      <div class="score-line"><div class="score-bit"><b>${sc.overall || '—'}</b><span>OVERALL</span></div><div class="score-bit"><b>${sc.production || '—'}</b><span>PROD</span></div><div class="score-bit"><b>${sc.story || '—'}</b><span>STORY</span></div><div class="score-bit"><b>${sc.emotional || '—'}</b><span>EMOTION</span></div></div></div></article>`;
  }
  function contentGuide(x, compact = false) {
    const c = x.content || {};
    const defs = [
      ['Sexual content', c.sex || 0],
      ['Nudity', c.nudity || 0],
      ['Violence', c.violence || 0],
      ['Gore', c.gore || 0],
      ['Disturbing content', c.disturbing || 0],
    ];
    const words = ['None', 'Mild', 'Moderate', 'Strong', 'Very strong', 'Extreme'];
    return `<div class="content-guide ${compact ? 'compact' : ''}">${defs
      .map(([label, raw]) => {
        const v = Math.max(0, Math.min(5, Number(raw) || 0));
        return `<div class="content-row severity-${v}"><span class="content-label">${esc(label)}</span><span class="content-meter" aria-hidden="true"><i></i></span><b>${esc(words[v])}</b><em>${v}/5</em></div>`;
      })
      .join('')}</div>`;
  }

  // Master-list cards and summary statistics
  function bindCards(root) {
    bindCoverErrors(root);
    $$('[data-fav-id]', root).forEach((b) =>
      b.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleFavorite(b.dataset.favId);
      }),
    );
    $$('.title-card', root).forEach((c) => {
      const fn = () => openDetail(c.dataset.id);
      c.addEventListener('click', (e) => {
        if (!e.target.closest('button')) fn();
      });
      c.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.target === c) fn();
      });
    });
  }
  function renderMaster({ noMeta = false } = {}) {
    const all = filteredMaster();
    $('#resultCount').textContent = all.length;
    const shown = all.slice(0, state.visible);
    const root = $('#cards');
    root.classList.toggle('compact', state.compact);
    root.innerHTML = shown.length
      ? shown.map((x) => cardHTML(x)).join('')
      : '<div class="empty-state">Nothing matches those filters.</div>';
    $('#loadMoreBtn').parentElement.classList.toggle('hidden', state.visible >= all.length);
    bindCards(root);
    updateStats();
    if (!noMeta) queueMetadata(shown, { priority: true });
  }
  function updateStats() {
    const items = canonicalItems(),
      completed = items.filter((x) => pFor(x.id).status === 'Completed').length,
      watching = items.filter((x) => pFor(x.id).status === 'Watching').length,
      films = items.filter((x) => /film/i.test(x.type || '')).length,
      favCount = items.filter((x) => isFavorite(x.id)).length;
    const browserCovers = items.filter((x) => {
      const m = meta[x.id]?.data || {};
      return !!(m.cover || m.image);
    }).length;
    const covers = Math.max(browserCovers, Number(state.serverCovers) || 0),
      coverTotal = Math.max(items.length, Number(state.serverCoverTotal) || 0);
    $('#statStrip').innerHTML =
      `<div class="stat"><b>${items.length}</b><span>TITLES</span></div><div class="stat"><b>${films}</b><span>FILMS / FILM SERIES</span></div><div class="stat"><b>${CAT.collections.length}</b><span>COLLECTIONS</span></div><div class="stat"><b>${CAT.franchises.length}</b><span>FRANCHISE GUIDES</span></div><div class="stat"><b>${covers}/${coverTotal}</b><span>${state.serverCoverRunning ? 'ARTWORK CACHING' : 'ARTWORK CACHED'}</span></div><div class="stat"><b>${favCount}</b><span>FAVORITES</span></div><div class="stat"><b>${completed}${watching ? ` + ${watching}` : ''}</b><span>${watching ? 'COMPLETED + WATCHING' : 'COMPLETED'}</span></div>`;
    renderUserSummary();
  }

  // Favorites and adult-content views
  function renderFavorites() {
    const input = $('#favoriteSearch');
    if (!input) return;
    const q = input.value.trim().toLowerCase();
    const arr = canonicalItems()
      .filter((x) => isFavorite(x.id))
      .filter((x) => {
        if (!q) return true;
        const m = meta[x.id]?.data || {};
        return `${x.title} ${(x.aliases || []).join(' ')} ${x.genres || ''} ${m.studio || ''}`
          .toLowerCase()
          .includes(q);
      })
      .sort((a, b) => (a.rank ?? 999999) - (b.rank ?? 999999) || a.title.localeCompare(b.title));
    $('#favoriteCount').textContent = `${arr.length} FAVORITE${arr.length === 1 ? '' : 'S'}`;
    const root = $('#favoriteCards');
    root.innerHTML = arr.length
      ? arr.map((x) => cardHTML(x)).join('')
      : '<div class="empty-state">No favorites yet. Use the heart on any title to add it here.</div>';
    bindCards(root);
    queueMetadata(arr, { priority: true });
  }

  function matchesAdult(x, mode = 'all') {
    const c = x.content || {},
      tags = (c.tags || []).map((t) => t.toLowerCase()),
      g = (x.genres || '').toLowerCase(),
      typ = (x.type || '').toLowerCase();
    if (mode === 'hentai') return tags.includes('hentai') || typ.includes('hentai');
    if (mode === 'ecchi') return tags.includes('ecchi') || g.includes('ecchi');
    if (mode === 'erotic') return tags.includes('erotic') || g.includes('erotic') || g.includes('sex comedy');
    if (mode === 'gore') return (c.gore || 0) >= 4 || tags.includes('gore');
    if (mode === 'violence') return (c.violence || 0) >= 5 || tags.includes('extreme violence');
    if (mode === 'disturbing') return (c.disturbing || 0) >= 5 || tags.includes('disturbing');
    return (
      tags.length > 0 ||
      Math.max(c.sex || 0, c.nudity || 0, c.violence || 0, c.gore || 0, c.disturbing || 0) >= 4
    );
  }
  function adultFilterItems(mode = state.adult) {
    return canonicalItems()
      .filter((x) => matchesAdult(x, mode))
      .sort((a, b) => (a.rank ?? 999999) - (b.rank ?? 999999));
  }
  function updateAdultChipCounts() {
    const labels = {
      all: 'ALL ADULT',
      ecchi: 'ECCHI',
      erotic: 'EROTIC',
      hentai: 'HENTAI',
      gore: 'GORE',
      violence: 'EXTREME VIOLENCE',
      disturbing: 'DISTURBING',
    };
    $$('.adult-chip').forEach((b) => {
      const mode = b.dataset.adult;
      b.textContent = `${labels[mode]} · ${adultFilterItems(mode).length}`;
    });
  }
  function renderAdult() {
    updateAdultChipCounts();
    const arr = adultFilterItems();
    const root = $('#adultCards');
    root.innerHTML = arr.length
      ? arr.map((x) => cardHTML(x, { adult: true })).join('')
      : `<div class="empty-state">No current master titles carry this tag.</div>`;
    bindCards(root);
    queueMetadata(arr, { priority: true });
  }

  // Curated collections and franchise watch orders
  function renderCollections() {
    const q = $('#collectionSearch').value.trim().toLowerCase();
    const all = CAT.collections.filter((c) => {
      const titles = c.items.map((id) => itemById(id)?.title || '').join(' ');
      return !q || `${c.name} ${c.kind} ${c.description} ${titles}`.toLowerCase().includes(q);
    });
    $('#collectionCount').textContent = `${all.length} COLLECTIONS`;
    $('#collectionGrid').innerHTML = all
      .map(
        (c) =>
          `<article class="collection-card" data-cid="${esc(c.id)}" tabindex="0"><span class="collection-kind">${esc(c.kind.toUpperCase())}</span><h3>${esc(c.name)}</h3><p>${esc(c.description)}</p><span class="collection-mode">${esc(c.mode.toUpperCase())}</span><span class="collection-count">${c.items.length}</span></article>`,
      )
      .join('');
    $$('.collection-card', $('#collectionGrid')).forEach((el) => {
      const fn = () => openCollection(el.dataset.cid);
      el.addEventListener('click', fn);
      el.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') fn();
      });
    });
  }
  function openCollection(id) {
    const c = CAT.collections.find((x) => x.id === id);
    if (!c) return;
    let arr = c.items.map(itemById).filter(Boolean);
    if (c.id === 'studio-ghibli') arr.sort((a, b) => (a.year || 9999) - (b.year || 9999));
    else arr.sort((a, b) => (a.rank ?? 999999) - (b.rank ?? 999999));
    $('#collectionBody').innerHTML =
      `<div class="collection-detail"><div class="meta">${esc(c.kind.toUpperCase())} // ${esc(c.mode.toUpperCase())} // ${arr.length} TITLES</div><h2>${esc(c.name)}</h2><p>${esc(c.description)}</p><div class="collection-title-list">${arr.map((x) => `<button class="collection-title" data-id="${esc(x.id)}"><b>${x.rank ? `#${String(x.rank).padStart(3, '0')}` : 'ADD'}</b><span>${esc(x.title)}${x.year ? ` <small>(${x.year})</small>` : ''}</span><em>${esc(x.tier || '')}</em></button>`).join('')}</div></div>`;
    $('#collectionDialog').showModal();
    $$('.collection-title', $('#collectionBody')).forEach((b) =>
      b.addEventListener('click', () => {
        $('#collectionDialog').close();
        openDetail(b.dataset.id);
      }),
    );
  }

  function renderFranchises() {
    const q = $('#franchiseSearch').value.trim().toLowerCase();
    const arr = CAT.franchises.filter(
      (f) => !q || `${f.name} ${f.summary} ${JSON.stringify(f.orders)}`.toLowerCase().includes(q),
    );
    $('#franchiseCount').textContent = `${arr.length} GUIDES`;
    $('#franchiseStack').innerHTML = arr
      .map(
        (f, i) =>
          `<details class="franchise"><summary><span class="franchise-no">${String(i + 1).padStart(2, '0')}</span><h3>${esc(f.name)}</h3><span class="franchise-chevron">+</span></summary><div class="franchise-body"><p class="franchise-summary">${esc(f.summary)}</p>${f.orders.map((o) => `<section class="order-block"><h4>${esc(o.label)}</h4>${o.note ? `<p class="order-note">${esc(o.note)}</p>` : ''}<div class="steps">${o.steps.map((s) => `<div class="step"><span class="step-n">${esc(s.n)}</span><span class="step-title">${esc(s.title)}${s.note ? `<small class="step-note">${esc(s.note)}</small>` : ''}</span><span class="flag ${esc(s.flag)}">${esc(s.flag)}</span></div>`).join('')}</div></section>`).join('')}</div></details>`,
      )
      .join('');
  }

  // Server availability and UserList sharing
  async function checkServer() {
    try {
      const r = await fetch('/api/health', { cache: 'no-store' });
      if (!r.ok) throw 0;
      const j = await r.json();
      state.server = !!j.ok;
      state.keyId = j.keyId || '';
      state.serverCovers = Number(j.covers?.cached) || 0;
      state.serverCoverTotal = Number(j.covers?.total) || masterItems.length;
      state.serverCoverRunning = !!j.covers?.running;
      $('#securityState').classList.add('ok');
      $('#securityState').innerHTML =
        `<b>SECURE USERLIST // UWL1</b><span>Ed25519 signing is ready · key ${esc(state.keyId)}</span>`;
      updateStats();
      queueMetadata(filteredMaster().slice(0, state.visible), { priority: true });
      pumpMetadata();
      hydrateMissingCustomMetadata();
    } catch {
      state.server = false;
      $('#securityState').classList.add('bad');
      $('#securityState').innerHTML =
        '<b>USERLIST SIGNING OFFLINE</b><span>Start the included server to create or verify signed UserList codes.</span>';
    }
  }
  function renderUserSummary() {
    const rec = Object.values(myOpinions).filter((v) => v === 'recommend').length,
      no = Object.values(myOpinions).filter((v) => v === 'avoid').length,
      adds = customTitles.filter((x) => x.addedByMe).length;
    $('#userListSummary').innerHTML =
      `<div><b>${rec}</b><span>RECOMMENDED</span></div><div><b>${no}</b><span>NOT RECOMMENDED</span></div><div><b>${adds}</b><span>ADDED TITLES</span></div>`;
    renderSources();
  }
  function renderSources() {
    const arr = Object.entries(sources).sort((a, b) =>
      (b[1].importedAt || '').localeCompare(a[1].importedAt || ''),
    );
    $('#sourceList').innerHTML = arr.length
      ? arr
          .map(([sid, s]) => {
            const rec = Object.values(s.opinions || {}).filter((v) => v === 'recommend').length,
              no = Object.values(s.opinions || {}).filter((v) => v === 'avoid').length;
            return `<div class="source-item"><div><b>${esc(s.label)}</b><span>${rec} rec · ${no} no · ${(s.titleIds || []).length} custom titles</span></div><span>${esc((s.importedAt || '').slice(0, 10))}</span><button data-remove-source="${esc(sid)}">REMOVE</button></div>`;
          })
          .join('')
      : '<div class="empty-state" style="padding:24px">No imported UserLists yet.</div>';
    $$('[data-remove-source]', $('#sourceList')).forEach((b) =>
      b.addEventListener('click', () => removeSource(b.dataset.removeSource)),
    );
  }
  function removeSource(sid) {
    if (!sources[sid]) return;
    delete sources[sid];
    save(STORE.sources, sources);
    // Remove imported-only custom titles that no remaining source uses and that you did not add yourself / opine on.
    const used = new Set(
      Object.values(sources).flatMap((s) => [...Object.keys(s.opinions || {}), ...(s.titleIds || [])]),
    );
    customTitles = customTitles.filter(
      (x) => x.addedByMe || myOpinions[x.id] || favorites[x.id] || used.has(x.id),
    );
    save(STORE.custom, customTitles);
    populateFilters();
    renderAll();
    toast('Imported source removed');
  }

  async function generateUserList() {
    if (!state.server) {
      toast('Secure signer is offline');
      return;
    }
    const opinionEntries = Object.entries(myOpinions)
      .filter(([id, v]) => itemById(id) && ['recommend', 'avoid'].includes(v))
      .map(([id, verdict]) => ({ id, verdict }));
    const needed = new Set([
      ...customTitles.filter((x) => x.addedByMe).map((x) => x.id),
      ...opinionEntries.map((o) => o.id).filter((id) => !masterById.has(id)),
    ]);
    const titleEntries = customTitles
      .filter((x) => needed.has(x.id))
      .map((x) => ({
        id: x.id,
        title: x.title,
        year: Number(x.year) || 0,
        type: x.type || 'Series',
        origin: x.origin || 'Unknown',
        api: x.api || 'none',
        lookupTitle: x.lookupTitle || x.title,
        externalId: String(x.externalId || ''),
        genres: x.genres || '',
        content: normalizedContent(x.content),
      }));
    $('#generateCodeBtn').disabled = true;
    $('#generateCodeBtn').textContent = 'SIGNING…';
    try {
      const r = await fetch('/api/userlist/sign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          v: 1,
          created: new Date().toISOString(),
          opinions: opinionEntries,
          titles: titleEntries,
        }),
      });
      const j = await r.json();
      if (!r.ok || !j.ok) throw new Error(j.error || 'sign-failed');
      $('#exportCode').value = j.code;
      toast('Signed UserList generated');
    } catch (e) {
      toast(`Could not sign: ${e.message}`);
    } finally {
      $('#generateCodeBtn').disabled = false;
      $('#generateCodeBtn').textContent = 'GENERATE SIGNED CODE';
    }
  }
  async function importUserList() {
    const label = $('#importSourceName').value.trim(),
      code = $('#importCode').value.trim(),
      out = $('#importResult');
    out.className = 'import-result';
    out.textContent = '';
    if (!label) {
      out.classList.add('bad');
      out.textContent = 'Choose the local source name first.';
      return;
    }
    if (label.length > 40 || /[<>\u0000-\u001F]/.test(label)) {
      out.classList.add('bad');
      out.textContent = 'Source name is invalid.';
      return;
    }
    if (!code) {
      out.classList.add('bad');
      out.textContent = 'Paste a UserList code.';
      return;
    }
    if (!state.server) {
      out.classList.add('bad');
      out.textContent = 'Signature service is offline.';
      return;
    }
    $('#importCodeBtn').disabled = true;
    $('#importCodeBtn').textContent = 'VERIFYING…';
    try {
      const r = await fetch('/api/userlist/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      });
      const j = await r.json();
      if (!r.ok || !j.ok) throw new Error(j.error || 'verification-failed');
      const payload = j.payload;
      // Work on clones. Commit only after every item is merged successfully.
      const nextCustom = JSON.parse(JSON.stringify(customTitles)),
        nextSources = JSON.parse(JSON.stringify(sources));
      const all = [...masterItems, ...nextCustom];
      const idMap = new Map(all.map((x) => [x.id, x]));
      const incomingMap = new Map();
      let newCount = 0,
        mergedCount = 0;
      for (const t of payload.titles) {
        let existing = idMap.get(t.id) || findEquivalent(t, all);
        if (existing) {
          if (existing.custom && !existing.addedByMe) applySharedCustomMetadata(existing, t);
          incomingMap.set(t.id, existing.id);
          mergedCount++;
          continue;
        }
        const x = customFromPayload(t, false);
        nextCustom.push(x);
        all.push(x);
        idMap.set(x.id, x);
        incomingMap.set(t.id, x.id);
        newCount++;
      }
      const existingSid = Object.keys(nextSources).find(
        (s) => nextSources[s].label.toLowerCase() === label.toLowerCase(),
      );
      const sid = existingSid || `src:${crypto.randomUUID()}`;
      const record = { label, importedAt: new Date().toISOString(), opinions: {}, titleIds: [] };
      for (const o of payload.opinions) {
        const mapped = incomingMap.get(o.id) || idMap.get(o.id)?.id || o.id;
        if (!idMap.has(mapped) && !masterById.has(mapped)) throw new Error('unknown-title-reference');
        record.opinions[mapped] = o.verdict;
      }
      record.titleIds = payload.titles
        .map((t) => incomingMap.get(t.id) || t.id)
        .filter((id) => !masterById.has(id));
      nextSources[sid] = record;
      customTitles = nextCustom;
      sources = nextSources;
      save(STORE.custom, customTitles);
      save(STORE.sources, sources);
      populateFilters();
      renderAll();
      hydrateMissingCustomMetadata();
      out.classList.add('good');
      out.textContent = `Verified. ${newCount} new title${newCount === 1 ? '' : 's'}, ${mergedCount} merged without duplicates, ${payload.opinions.length} opinions attached to “${label}”.`;
      toast(`UserList imported: ${label}`);
    } catch (e) {
      out.classList.add('bad');
      out.textContent = `Rejected. Nothing was imported. ${humanImportError(e.message)}`;
    } finally {
      $('#importCodeBtn').disabled = false;
      $('#importCodeBtn').textContent = 'VERIFY + IMPORT';
    }
  }
  function humanImportError(e) {
    const m = {
      'foreign-userlist-key': 'This code was not generated by this installation.',
      'signature-failed': 'The code was modified or the signature is invalid.',
      'not-userlist-code': 'This is not a UWL1 code.',
      'invalid-schema': 'The payload does not match the UserList schema.',
      'invalid-code': 'The code is malformed.',
    };
    return m[e] || e;
  }
  function findEquivalent(t, all) {
    const n = norm(t.title);
    const aliasId = aliasMap.get(n);
    if (aliasId) {
      const m = masterById.get(aliasId);
      if (!t.year || !m?.year || Math.abs(Number(t.year) - Number(m.year)) <= 1) return m;
    }
    return (
      all.find((x) => {
        const same = norm(x.title) === n || (x.aliases || []).some((a) => norm(a) === n);
        if (!same) return false;
        const y1 = Number(x.year) || 0,
          y2 = Number(t.year) || 0;
        if (y1 && y2 && Math.abs(y1 - y2) > 1) return false;
        return roughlySameType(x.type, t.type);
      }) || null
    );
  }
  function roughlySameType(a = '', b = '') {
    const A = a.toLowerCase(),
      B = b.toLowerCase();
    if (A.includes('film') !== B.includes('film')) return false;
    if (
      A.includes('series') !== B.includes('series') &&
      A.includes('film') === false &&
      B.includes('film') === false
    )
      return true;
    return true;
  }
  function customFromPayload(t, addedByMe) {
    const adult = (t.type || '').toLowerCase().includes('hentai');
    const fallbackContent = adult
      ? { sex: 5, nudity: 5, violence: 0, gore: 0, disturbing: 1, tags: ['Hentai', 'Adult Only'] }
      : { sex: 0, nudity: 0, violence: 0, gore: 0, disturbing: 0, tags: [] };
    return {
      id: t.id,
      title: t.title,
      year: Number(t.year) || 0,
      type: t.type,
      origin: t.origin || 'Unknown',
      genres: t.genres || (adult ? 'Adult, Hentai' : 'Custom addition'),
      tier: 'CUSTOM',
      rank: null,
      quality_band: 'CUSTOM',
      api: t.api || 'none',
      lookupTitle: t.lookupTitle || t.title,
      externalId: t.externalId || '',
      custom: true,
      addedByMe,
      content: t.content ? normalizedContent(t.content) : fallbackContent,
      scores: { overall: 0, production: 0, story: 0, emotional: 0 },
    };
  }

  function normalizedContent(content = {}) {
    const level = (key) => Math.max(0, Math.min(5, Math.round(Number(content[key]) || 0)));
    const tags = Array.isArray(content.tags)
      ? [
          ...new Map(
            content.tags.map((tag) => [String(tag).trim().toLowerCase(), String(tag).trim()]),
          ).values(),
        ]
          .filter(Boolean)
          .slice(0, 20)
      : [];
    return {
      sex: level('sex'),
      nudity: level('nudity'),
      violence: level('violence'),
      gore: level('gore'),
      disturbing: level('disturbing'),
      tags,
    };
  }

  function applySharedCustomMetadata(target, incoming) {
    target.title = incoming.title;
    target.year = Number(incoming.year) || 0;
    target.type = incoming.type;
    target.origin = incoming.origin || 'Unknown';
    target.genres = incoming.genres || target.genres || 'Custom addition';
    target.api = incoming.api || target.api || 'none';
    target.lookupTitle = incoming.lookupTitle || incoming.title;
    target.externalId = incoming.externalId || '';
    if (incoming.content) target.content = normalizedContent(incoming.content);
  }

  function customMetadataKinds(type = '', origin = '') {
    const format = type.toLowerCase();
    const place = origin.toLowerCase();
    const asian = /japan|japanese|china|chinese|korea|korean/.test(place);
    if (format.includes('western series')) return ['tvmaze', 'wiki', 'anilist'];
    if (format.includes('western film')) return ['wiki', 'tvmaze', 'anilist'];
    if (/ova|ona|donghua|hentai/.test(format) || asian) return ['anilist', 'wiki', 'tvmaze'];
    if (format.includes('series')) return ['tvmaze', 'anilist', 'wiki'];
    return ['wiki', 'anilist', 'tvmaze'];
  }

  function metadataMatchesTitle(title, data, year = 0) {
    const target = norm(title);
    const candidates = [data?.canonicalTitle, data?.altTitle].filter(Boolean).map(norm);
    if (!target || !candidates.length) return false;
    if (year && data?.year && Math.abs(Number(year) - Number(data.year)) > 1) return false;
    const targetTokens = new Set(target.split(' ').filter(Boolean));
    return candidates.some((candidate) => {
      if (candidate === target) return true;
      if (
        Math.min(candidate.length, target.length) >= 5 &&
        (candidate.includes(target) || target.includes(candidate))
      )
        return true;
      const candidateTokens = new Set(candidate.split(' ').filter(Boolean));
      const shared = [...targetTokens].filter((token) => candidateTokens.has(token)).length;
      const union = new Set([...targetTokens, ...candidateTokens]).size;
      return union > 0 && shared / union >= 0.6;
    });
  }

  function contentIsEmpty(content) {
    const value = normalizedContent(content);
    return (
      !value.tags.length && !['sex', 'nudity', 'violence', 'gore', 'disturbing'].some((key) => value[key])
    );
  }

  async function findCustomMetadata(title, type, origin, year = 0) {
    if (!state.server || NO_META) return null;
    for (const kind of customMetadataKinds(type, origin)) {
      try {
        const response = await fetch(
          `/api/resolve?kind=${encodeURIComponent(kind)}&title=${encodeURIComponent(title)}`,
        );
        const result = await response.json();
        if (response.ok && result.ok && metadataMatchesTitle(title, result.data, year))
          return { kind, data: result.data };
      } catch {}
    }
    return null;
  }

  function applyResolvedCustomMetadata(x, match) {
    if (!match?.data) return;
    const data = match.data;
    x.api = match.kind;
    x.lookupTitle = x.title;
    x.externalId = data.externalId || '';
    if (!x.year && data.year) x.year = Number(data.year) || 0;
    if ((!x.genres || x.genres === 'Custom addition') && Array.isArray(data.genres) && data.genres.length)
      x.genres = data.genres.join(', ');
    if (contentIsEmpty(x.content) && data.content) {
      x.content = normalizedContent(data.content);
      x.contentEstimated = true;
    }
    meta[x.id] = { ts: Date.now(), data };
    save(STORE.custom, customTitles);
    save(STORE.meta, meta);
  }

  async function refreshCustomMetadata(x, { force = false, silent = false } = {}) {
    if (!x?.custom) return false;
    if (!force && metaFresh(x.id) && meta[x.id]?.data?.content) return true;
    const match = await findCustomMetadata(x.lookupTitle || x.title, x.type, x.origin, x.year);
    if (!match) {
      if (!silent) toast('No reliable metadata match found');
      return false;
    }
    applyResolvedCustomMetadata(x, match);
    refreshArtwork();
    if (!silent) toast('Metadata and estimated content ratings updated');
    return true;
  }

  async function hydrateMissingCustomMetadata() {
    for (const x of customTitles) {
      if (!state.server) return;
      if (!metaFresh(x.id) || (contentIsEmpty(x.content) && !meta[x.id]?.data?.content))
        await refreshCustomMetadata(x, { silent: true });
    }
  }

  // Manual title resolution and deduplication
  async function addTitle(ev) {
    ev.preventDefault();
    const out = $('#addResult'),
      raw = $('#addTitleName').value.trim(),
      year = Number($('#addTitleYear').value) || 0,
      type = $('#addTitleType').value,
      origin = $('#addTitleOrigin').value.trim() || 'Unknown';
    out.className = 'import-result';
    if (!raw) {
      return;
    }
    const pre = findEquivalent({ title: raw, year, type }, canonicalItems());
    if (pre) {
      out.classList.add('bad');
      out.innerHTML = `Already exists: <button class="inline-open" data-open-id="${esc(pre.id)}">${esc(pre.title)}</button>`;
      out.querySelector('button').onclick = () => openDetail(pre.id);
      return;
    }
    let match = null;
    out.textContent = 'Resolving title and checking canonical metadata…';
    if (state.server) match = await findCustomMetadata(raw, type, origin, year);
    const resolved = match?.data || null,
      kind = match?.kind || customMetadataKinds(type, origin)[0],
      title = raw,
      finalYear = year || resolved?.year || 0;
    const second = findEquivalent(
      { title: resolved?.canonicalTitle || title, year: finalYear, type },
      canonicalItems(),
    );
    if (second) {
      out.classList.add('bad');
      out.innerHTML = `Resolved to an existing title: <button class="inline-open" data-open-id="${esc(second.id)}">${esc(second.title)}</button>`;
      out.querySelector('button').onclick = () => openDetail(second.id);
      return;
    }
    let id;
    if (resolved?.externalId) {
      id = `${kind === 'anilist' ? 'a' : kind === 'tvmaze' ? 't' : 'w'}:${resolved.externalId}`;
    } else {
      id = await fallbackId(title, finalYear, type);
    }
    if (itemById(id)) {
      out.classList.add('bad');
      out.textContent = 'That canonical title already exists.';
      return;
    }
    const t = {
      id,
      title,
      year: finalYear,
      type,
      origin,
      api: kind,
      lookupTitle: title,
      externalId: resolved?.externalId || '',
      genres: Array.isArray(resolved?.genres) ? resolved.genres.join(', ') : '',
      content: resolved?.content,
    };
    const x = customFromPayload(t, true);
    if (resolved?.content && !contentIsEmpty(resolved.content)) x.contentEstimated = true;
    customTitles.push(x);
    save(STORE.custom, customTitles);
    if (resolved) meta[id] = { ts: Date.now(), data: resolved };
    save(STORE.meta, meta);
    populateFilters();
    renderAll();
    out.classList.add('good');
    out.innerHTML = `Added “${esc(title)}” without changing the editorial master ranking. <button class="inline-open" type="button">EDIT DETAILS</button>`;
    out.querySelector('button').onclick = () => openDetail(id);
    $('#addTitleForm').reset();
    toast('Custom title added');
  }
  async function fallbackId(title, year, type) {
    const input = `${norm(title)}|${year || 0}|${norm(type)}`;
    const hash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(input));
    const hex = [...new Uint8Array(hash)]
      .slice(0, 6)
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('');
    return `c:${norm(title).replace(/ /g, '-').slice(0, 70) || 'title'}:${hex}`;
  }

  function customEditorHTML(x) {
    const content = normalizedContent(x.content);
    const formats = [
      'Series',
      'Film',
      'OVA',
      'ONA',
      'Special',
      'Donghua series',
      'Western series',
      'Western film',
      'Adult / Hentai',
    ];
    if (x.type && !formats.includes(x.type)) formats.unshift(x.type);
    const levels = [
      ['Sexual content', 'sex'],
      ['Nudity', 'nudity'],
      ['Violence', 'violence'],
      ['Gore', 'gore'],
      ['Disturbing', 'disturbing'],
    ];
    return `<section class="custom-editor"><h4>Edit custom metadata</h4><p>These fields are included when this title is exported in a signed UserList. Provider-based content ratings are estimates and should be reviewed.</p><button id="refreshCustomMetadata" class="slash-button small" type="button">${x.contentEstimated ? 'REFRESH ESTIMATED METADATA' : 'FIND MISSING METADATA'}</button><div class="custom-editor-grid"><label class="field-label">TITLE<input id="customTitle" maxlength="180" value="${esc(x.title)}"></label><div class="field-row"><label class="field-label">YEAR<input id="customYear" type="number" min="0" max="2200" value="${Number(x.year) || ''}" placeholder="Unknown"></label><label class="field-label">FORMAT<select id="customType">${formats.map((type) => `<option ${x.type === type ? 'selected' : ''}>${esc(type)}</option>`).join('')}</select></label></div><label class="field-label">ORIGIN<input id="customOrigin" maxlength="80" value="${esc(x.origin || '')}" placeholder="Japan / US / China / …"></label><label class="field-label">GENRES / TAGS<textarea id="customGenres" maxlength="500" placeholder="Fantasy, Adventure, Drama">${esc(x.genres || '')}</textarea></label><label class="field-label">CONTENT LABELS<input id="customContentTags" maxlength="500" value="${esc(content.tags.join(', '))}" placeholder="Ecchi, Gore, Adult Only, …"></label><div class="custom-content-fields">${levels.map(([label, key]) => `<label>${esc(label)}<input id="customContent-${key}" type="number" min="0" max="5" step="1" value="${content[key]}"><span>/5</span></label>`).join('')}</div></div></section>`;
  }

  function parseCustomTags(raw) {
    const tags = [];
    const seen = new Set();
    for (const part of String(raw).split(',')) {
      const tag = part.trim();
      if (!tag) continue;
      if (tag.length > 40 || /[<> -]/.test(tag))
        throw new Error('Each content label must be 40 safe characters or fewer.');
      const key = tag.toLowerCase();
      if (!seen.has(key)) {
        seen.add(key);
        tags.push(tag);
      }
    }
    if (tags.length > 20) throw new Error('Use no more than 20 content labels.');
    return tags;
  }

  function saveCustomMetadata(x) {
    const title = $('#customTitle').value.trim();
    const year = Number($('#customYear').value) || 0;
    const type = $('#customType').value;
    const origin = $('#customOrigin').value.trim() || 'Unknown';
    const genres = $('#customGenres').value.trim();
    const lookupChanged =
      norm(title) !== norm(x.lookupTitle || x.title) || type !== x.type || norm(origin) !== norm(x.origin);
    if (!title || title.length > 180 || /[<> -]/.test(title)) throw new Error('Enter a valid title.');
    if (!Number.isInteger(year) || year < 0 || year > 2200) throw new Error('Enter a valid year.');
    if (origin.length > 80 || /[<> -]/.test(origin)) throw new Error('Enter a valid origin.');
    if (genres.length > 500 || /[<> -]/.test(genres))
      throw new Error('Genres and tags must be 500 safe characters or fewer.');
    const duplicate = findEquivalent(
      { title, year, type },
      canonicalItems().filter((item) => item.id !== x.id),
    );
    if (duplicate) throw new Error(`This matches the existing title “${duplicate.title}”.`);
    const level = (key) => {
      const value = Number($(`#customContent-${key}`).value);
      if (!Number.isInteger(value) || value < 0 || value > 5)
        throw new Error('Content ratings must be whole numbers from 0 to 5.');
      return value;
    };
    x.title = title;
    x.year = year;
    x.type = type;
    x.origin = origin;
    x.genres = genres;
    x.lookupTitle = title;
    if (lookupChanged) {
      x.api = customMetadataKinds(type, origin)[0];
      x.externalId = '';
      delete meta[x.id];
      save(STORE.meta, meta);
    }
    x.content = {
      sex: level('sex'),
      nudity: level('nudity'),
      violence: level('violence'),
      gore: level('gore'),
      disturbing: level('disturbing'),
      tags: parseCustomTags($('#customContentTags').value),
    };
    x.contentEstimated = false;
    save(STORE.custom, customTitles);
    return lookupChanged;
  }

  // Detail dialog and personal progress
  function openDetail(id) {
    const x = itemById(id);
    if (!x) return;
    const m = meta[id]?.data || {},
      p = pFor(id),
      verdict = ownVerdict(id),
      ops = sourceOpinions(id),
      bg = m.banner || m.cover || m.image || '';
    const sc = x.scores || {};
    const facts = [
      x.rank ? `#${x.rank}` : 'CUSTOM',
      x.tier,
      displayType(x),
      liveYear(x),
      x.origin,
      m.studio,
      sc.overall ? `Overall ${sc.overall}` : '',
    ].filter(Boolean);
    $('#dialogBody').innerHTML =
      `<div class="detail-hero">${bg ? `<img class="detail-bg" src="${esc(bg)}" alt="">` : ''}<div class="detail-heading"><div class="kicker">${x.rank ? `MASTER RANK #${String(x.rank).padStart(3, '0')}` : 'CUSTOM ADDITION'} // ${esc(x.tier || '')}</div><h2>${esc(x.title)}</h2></div></div><div class="detail-content"><div class="detail-facts">${facts.map((f) => `<span class="fact">${esc(f)}</span>`).join('')}</div><div class="detail-grid"><div>${m.description ? `<h4>Synopsis</h4><p>${esc(m.description)}</p>` : '<p class="metadata-wait">Synopsis will appear when metadata is available.</p>'}${x.watch_note ? `<div class="callout"><h4>Watch note</h4><p>${esc(x.watch_note)}</p></div>` : ''}${x.caveat ? `<div class="callout"><h4>Worth knowing</h4><p>${esc(x.caveat)}</p></div>` : ''}${m.siteUrl ? `<a class="external-link" href="${esc(m.siteUrl)}" target="_blank" rel="noopener">OPEN SOURCE ↗</a>` : ''}<h4>Content</h4>${contentGuide(x, false)}${x.custom ? customEditorHTML(x) : ''}${ops.length ? `<h4>Imported opinions</h4><div class="source-opinion-list">${ops.map((o) => `<div class="source-opinion"><b>${esc(o.label)}</b><span class="${o.verdict === 'recommend' ? 'yes' : 'no'}">${o.verdict === 'recommend' ? 'RECOMMENDED' : 'NOT RECOMMENDED'}</span></div>`).join('')}</div>` : ''}</div><aside><div class="user-edit"><button id="modalFavorite" class="favorite-detail ${isFavorite(id) ? 'active' : ''}" type="button">${isFavorite(id) ? '♥ FAVORITE' : '♡ ADD TO FAVORITES'}</button><label>MY RECOMMENDATION</label><div class="verdict-row"><button class="verdict-btn rec ${verdict === 'recommend' ? 'active' : ''}" data-v="recommend">RECOMMEND</button><button class="verdict-btn no ${verdict === 'avoid' ? 'active' : ''}" data-v="avoid">DON'T RECOMMEND</button><button class="verdict-btn neutral ${!verdict ? 'active' : ''}" data-v="">NEUTRAL</button></div><label>WATCH STATUS</label><select id="modalStatus">${['Not started', 'Watching', 'Completed', 'On hold', 'Dropped'].map((s) => `<option ${p.status === s ? 'selected' : ''}>${s}</option>`).join('')}</select><label>MY RATING /10</label><input id="modalRating" type="number" min="0" max="10" step="0.5" value="${p.rating || ''}" placeholder="Unrated"><label>PRIVATE NOTE</label><textarea id="modalNote" maxlength="2000">${esc(p.note || '')}</textarea><button class="slash-button hot wide" id="saveDetail">${x.custom ? 'SAVE TITLE + LOCAL DATA' : 'SAVE LOCAL DATA'}</button></div></aside></div></div>`;
    $('#modalFavorite').onclick = () => {
      toggleFavorite(id);
      const b = $('#modalFavorite');
      b.classList.toggle('active', isFavorite(id));
      b.textContent = isFavorite(id) ? '♥ FAVORITE' : '♡ ADD TO FAVORITES';
    };
    let selectedVerdict = verdict;
    $$('.verdict-btn', $('#dialogBody')).forEach((b) =>
      b.addEventListener('click', () => {
        selectedVerdict = b.dataset.v;
        $$('.verdict-btn', $('#dialogBody')).forEach((x) => x.classList.remove('active'));
        b.classList.add('active');
      }),
    );
    if (x.custom) {
      $('#refreshCustomMetadata').onclick = async () => {
        const button = $('#refreshCustomMetadata');
        button.disabled = true;
        button.textContent = 'SEARCHING…';
        const found = await refreshCustomMetadata(x, { force: true });
        if (found) {
          $('#detailDialog').close();
          openDetail(id);
        } else {
          button.disabled = false;
          button.textContent = 'FIND MISSING METADATA';
        }
      };
    }
    $('#saveDetail').onclick = () => {
      let metadataChanged = false;
      if (x.custom) {
        try {
          metadataChanged = saveCustomMetadata(x);
        } catch (error) {
          toast(error.message);
          return;
        }
      }
      progress[id] = {
        status: $('#modalStatus').value,
        rating: Number($('#modalRating').value) || 0,
        note: $('#modalNote').value.trim(),
      };
      if (selectedVerdict) myOpinions[id] = selectedVerdict;
      else delete myOpinions[id];
      save(STORE.progress, progress);
      save(STORE.opinions, myOpinions);
      $('#detailDialog').close();
      renderAll();
      toast('Saved locally');
      if (metadataChanged) refreshCustomMetadata(x, { force: true, silent: true });
    };
    $('#detailDialog').showModal();
    if (x.custom) refreshCustomMetadata(x, { silent: true });
    else queueMetadata([x], { priority: true });
  }

  function metaFresh(id) {
    const cur = meta[id];
    return !!(cur && Date.now() - cur.ts < META_TTL && cur.data);
  }

  // Batched metadata loading keeps provider traffic bounded.
  function queueMetadata(items, { priority = false } = {}) {
    if (NO_META) return;
    const add = [];
    for (const x of items || []) {
      if (x?.custom) continue;
      if (!x?.id || !x.api || x.api === 'none' || metaFresh(x.id) || metaQueued.has(x.id)) continue;
      metaQueued.add(x.id);
      add.push(x);
    }
    if (priority) metaQueue.unshift(...add.reverse());
    else metaQueue.push(...add);
    if (state.server) pumpMetadata();
  }
  function scheduleMetaSave() {
    clearTimeout(metaSaveTimer);
    metaSaveTimer = setTimeout(() => save(STORE.meta, meta), 350);
  }
  function sleep(ms) {
    return new Promise((r) => setTimeout(r, ms));
  }
  function replaceBrokenCover(img, x) {
    const slot = img.closest('.cover');
    if (!slot) return;
    const ph = document.createElement('div');
    ph.className = 'cover-placeholder';
    ph.textContent = initials(x.title);
    img.replaceWith(ph);
  }
  function bindCoverErrors(root = document) {
    $$('.title-card img', root).forEach((img) => {
      if (img.dataset.errBound) return;
      img.dataset.errBound = '1';
      img.addEventListener(
        'error',
        () => {
          const x = itemById(img.closest('.title-card')?.dataset.id);
          if (x) replaceBrokenCover(img, x);
        },
        { once: true },
      );
    });
  }
  function refreshArtwork() {
    $$('.title-card').forEach((card) => {
      const x = itemById(card.dataset.id),
        m = meta[card.dataset.id]?.data || {},
        url = m.cover || m.image || '';
      if (!x || !url) return;
      const slot = card.querySelector('.cover'),
        img = slot?.querySelector('img'),
        ph = slot?.querySelector('.cover-placeholder');
      if (!slot) return;
      if (img) {
        if (img.src !== url) img.src = url;
      } else {
        const n = document.createElement('img');
        n.loading = 'lazy';
        n.alt = `${x.title} cover`;
        n.src = url;
        if (ph) ph.replaceWith(n);
        else slot.prepend(n);
      }
    });
    bindCoverErrors();
    updateHero();
    updateStats();
  }
  async function pumpMetadata() {
    if (metaPumping || !state.server || NO_META) return;
    metaPumping = true;
    try {
      while (metaQueue.length && state.server) {
        const chunk = [];
        while (metaQueue.length && chunk.length < META_BATCH_SIZE) {
          const x = metaQueue.shift();
          metaQueued.delete(x.id);
          if (!metaFresh(x.id) && x.api && x.api !== 'none') chunk.push(x);
        }
        if (!chunk.length) continue;
        try {
          const r = await fetch('/api/meta/batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              items: chunk.map((x) => ({ key: x.id, kind: x.api, title: x.lookupTitle || x.title })),
            }),
          });
          const j = await r.json();
          if (r.ok && j.ok) {
            for (const row of j.results || []) {
              if (row?.data && itemById(row.key)) {
                meta[row.key] = { ts: Date.now(), data: row.data };
              }
            }
            scheduleMetaSave();
            refreshArtwork();
          }
        } catch {}
        if (metaQueue.length) await sleep(META_BATCH_DELAY);
      }
    } finally {
      metaPumping = false;
      if (metaQueue.length && state.server) setTimeout(pumpMetadata, META_BATCH_DELAY);
    }
  }
  function updateHero() {
    const x = masterItems[0];
    if (!x) return;
    const m = meta[x.id]?.data || {};
    const h = $('#heroFeature');
    h.innerHTML = `${m.banner || m.cover ? `<img class="hero-bg" src="${esc(m.banner || m.cover)}" alt="">` : ''}<div class="feature-rank">#001</div><div class="feature-lines"><span></span><span></span><span></span></div><div class="feature-title">${esc(x.title)}</div><div class="feature-sub">NO. 1 IN THE CURRENT RANKING.</div>`;
    if (m.banner || m.cover) h.classList.add('with-image');
  }

  // Navigation, global rendering and event wiring
  function switchTab(name) {
    state.tab = name;
    $$('.rail-tab').forEach((b) => b.classList.toggle('active', b.dataset.tab === name));
    $$('.panel').forEach((p) => p.classList.toggle('active', p.id === `${name}Tab`));
    if (name === 'adult') renderAdult();
    if (name === 'collections') renderCollections();
    if (name === 'franchises') renderFranchises();
    if (name === 'favorites') renderFavorites();
    if (name === 'userlist') renderUserSummary();
    history.replaceState(null, '', `#${name}`);
    window.scrollTo({ top: 0, behavior: 'instant' });
  }
  function renderAll() {
    renderMaster({ noMeta: true });
    renderCollections();
    renderFranchises();
    if (state.tab === 'adult') renderAdult();
    if (state.tab === 'favorites') renderFavorites();
    renderUserSummary();
  }
  function toast(msg) {
    const t = $('#toast');
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(toast.t);
    toast.t = setTimeout(() => t.classList.remove('show'), 2100);
  }
  function randomPick() {
    const a = filteredMaster();
    if (!a.length) return toast('No titles match');
    openDetail(a[Math.floor(Math.random() * a.length)].id);
  }
  function topUnseen() {
    const x = masterItems.find((x) => pFor(x.id).status !== 'Completed');
    if (x) openDetail(x.id);
    else toast('You have completed every title in the list.');
  }

  // UI events
  $$('.rail-tab').forEach((b) => b.addEventListener('click', () => switchTab(b.dataset.tab)));
  ['searchInput'].forEach((id) =>
    $('#' + id).addEventListener('input', () => {
      state.visible = PAGE_SIZE;
      saveUIState();
      renderMaster();
    }),
  );
  [
    'tierFilter',
    'typeFilter',
    'genreFilter',
    'statusFilter',
    'sortSelect',
    'hideCompleted',
    'customOnly',
  ].forEach((id) =>
    $('#' + id).addEventListener('change', () => {
      state.visible = PAGE_SIZE;
      saveUIState();
      renderMaster();
    }),
  );
  $('#loadMoreBtn').addEventListener('click', () => {
    state.visible += PAGE_SIZE;
    renderMaster();
  });
  $('#viewToggle').addEventListener('click', () => {
    state.compact = !state.compact;
    save(STORE.compact, state.compact);
    $('#viewToggle').textContent = state.compact ? '▤' : '▥';
    renderMaster();
  });
  $('#surpriseBtn').addEventListener('click', randomPick);
  $('#topUnseenBtn').addEventListener('click', topUnseen);
  $('#quickAddBtn').addEventListener('click', () => {
    switchTab('userlist');
    setTimeout(() => $('#addTitleName').focus(), 50);
  });
  $('#collectionSearch').addEventListener('input', () => {
    saveUIState();
    renderCollections();
  });
  $('#franchiseSearch').addEventListener('input', () => {
    saveUIState();
    renderFranchises();
  });
  $('#favoriteSearch').addEventListener('input', () => {
    saveUIState();
    renderFavorites();
  });
  $$('.adult-chip').forEach((b) =>
    b.addEventListener('click', () => {
      $$('.adult-chip').forEach((x) => x.classList.remove('active'));
      b.classList.add('active');
      state.adult = b.dataset.adult;
      saveUIState();
      renderAdult();
    }),
  );
  $('#generateCodeBtn').addEventListener('click', generateUserList);
  $('#copyCodeBtn').addEventListener('click', async () => {
    const v = $('#exportCode').value;
    if (!v) return toast('Generate a code first');
    try {
      await navigator.clipboard.writeText(v);
      toast('UserList code copied');
    } catch {
      $('#exportCode').select();
      document.execCommand('copy');
      toast('UserList code copied');
    }
  });
  $('#importCodeBtn').addEventListener('click', importUserList);
  $('#addTitleForm').addEventListener('submit', addTitle);
  $('#dialogClose').addEventListener('click', () => $('#detailDialog').close());
  $('#collectionClose').addEventListener('click', () => $('#collectionDialog').close());
  $('#detailDialog').addEventListener('click', (e) => {
    if (e.target === $('#detailDialog')) $('#detailDialog').close();
  });
  $('#collectionDialog').addEventListener('click', (e) => {
    if (e.target === $('#collectionDialog')) $('#collectionDialog').close();
  });

  // boot
  populateFilters();
  restoreUIState();
  $('#viewToggle').textContent = state.compact ? '▤' : '▥';
  renderMaster({ noMeta: NO_META });
  renderCollections();
  renderFranchises();
  renderFavorites();
  renderUserSummary();
  updateHero();
  checkServer();
  const hash = location.hash.replace('#', '');
  if (['master', 'collections', 'franchises', 'adult', 'favorites', 'userlist'].includes(hash))
    switchTab(hash);
})().catch((error) => {
  console.error('Catalog startup failed:', error);
  const main = document.querySelector('.main-shell');
  if (main) {
    main.innerHTML =
      '<section class="panel active"><div class="empty-state">The catalog could not be loaded. Start the included server and reload the page.</div></section>';
  }
});
