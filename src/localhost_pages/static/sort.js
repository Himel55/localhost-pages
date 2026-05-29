// Custom sort dropdown + row reorder. Modes: alpha, recently-updated,
// recently-visited, most-visited, manual (order set by edit.js).
(function () {
  const { KEYS, loadArray, onEscape } = window.LP;

  const wrap = document.querySelector('.sort-wrap');
  const toggle = wrap?.querySelector('.sort-toggle');
  const current = wrap?.querySelector('.sort-current');
  const menu = wrap?.querySelector('.sort-menu');
  const list = document.querySelector('.apps');
  if (!wrap || !toggle || !current || !menu || !list) return;

  const items = Array.from(menu.querySelectorAll('li[data-value]'));
  // Migrate the legacy 'recent' value (pre-rename) so existing users
  // don't get reset to alpha after deploy.
  const stored = localStorage.getItem(KEYS.sort);
  let mode = stored === 'recent' ? 'recently-updated' : (stored || 'alpha');
  if (!items.some((i) => i.dataset.value === mode)) mode = 'alpha';

  const byName = (a, b) => a.dataset.name.localeCompare(b.dataset.name);

  function buildComparator(m) {
    switch (m) {
      case 'recently-updated':
        return (a, b) => (b.dataset.mtime || '').localeCompare(a.dataset.mtime || '');
      case 'recently-visited': {
        const at = (n) => localStorage.getItem(KEYS.visitedPrefix + n) || '';
        return (a, b) => at(b.dataset.name).localeCompare(at(a.dataset.name)) || byName(a, b);
      }
      case 'most-visited': {
        const count = (n) => parseInt(localStorage.getItem(KEYS.visitsPrefix + n) || '0', 10) || 0;
        return (a, b) => count(b.dataset.name) - count(a.dataset.name) || byName(a, b);
      }
      case 'manual': {
        const pos = new Map(loadArray(KEYS.order).map((name, i) => [name, i]));
        const idx = (n) => (pos.has(n) ? pos.get(n) : Number.MAX_SAFE_INTEGER);
        return (a, b) => idx(a.dataset.name) - idx(b.dataset.name) || byName(a, b);
      }
      default:
        return byName;
    }
  }

  function renumber() {
    let i = 1;
    list.querySelectorAll('.row').forEach((row) => {
      // Skip search-hidden rows so the visible numbering stays gapless.
      if (row.style.display === 'none') return;
      const num = row.querySelector('.num');
      if (num) num.textContent = String(i++).padStart(2, '0');
    });
  }

  function apply() {
    const cmp = buildComparator(mode);
    const rows = Array.from(list.querySelectorAll('.row'));
    const pinned = rows.filter((r) => r.classList.contains('pinned')).sort(cmp);
    const rest = rows.filter((r) => !r.classList.contains('pinned')).sort(cmp);
    [...pinned, ...rest].forEach((r) => list.appendChild(r));
    renumber();
  }

  function setMode(value, persist = true) {
    mode = value;
    if (persist) localStorage.setItem(KEYS.sort, value);
    const item = items.find((i) => i.dataset.value === value);
    current.textContent = item ? item.textContent : value;
    items.forEach((i) => i.setAttribute('aria-selected', String(i.dataset.value === value)));
    apply();
  }

  function openMenu() {
    menu.hidden = false;
    toggle.setAttribute('aria-expanded', 'true');
  }
  function closeMenu() {
    menu.hidden = true;
    toggle.setAttribute('aria-expanded', 'false');
  }

  toggle.addEventListener('click', (e) => {
    e.stopPropagation();
    if (menu.hidden) openMenu(); else closeMenu();
  });

  menu.addEventListener('click', (e) => {
    const li = e.target.closest('li[data-value]');
    if (!li) return;
    e.stopPropagation();
    setMode(li.dataset.value);
    closeMenu();
  });

  document.addEventListener('click', (e) => {
    if (!menu.hidden && !wrap.contains(e.target)) closeMenu();
  });

  onEscape(70, () => {
    if (menu.hidden) return false;
    closeMenu();
    toggle.focus();
    return true;
  });

  // Public hooks for other scripts: set() changes mode (edit.js), reapply()
  // re-sorts in the current mode (pin.js, visited.js), renumber() re-gaps
  // the visible row numbers after search filtering (search.js).
  window.LP.sort = { set: setMode, reapply: apply, renumber };

  setMode(mode, /*persist*/ false);

  // Re-apply after SSE-driven reloads / bfcache restores so freshness sort
  // stays correct without a manual refresh.
  window.addEventListener('pageshow', apply);
})();
