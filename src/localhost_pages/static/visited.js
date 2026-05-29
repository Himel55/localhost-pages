// On load, mark each row with .has-update if its mtime is newer than the
// last time the user clicked into it. On click/preview, stamp the visit so
// the indicator clears and the visit-based sorts update.
(function () {
  const { KEYS } = window.LP;

  function lastVisitedAt(name) {
    const v = localStorage.getItem(KEYS.visitedPrefix + name);
    return v ? Date.parse(v) : 0;
  }

  function markRows() {
    document.querySelectorAll('.row').forEach((row) => {
      const name = row.dataset.name;
      const mtimeIso = row.dataset.mtime;
      if (!name || !mtimeIso) return;
      const mtime = Date.parse(mtimeIso);
      if (Number.isNaN(mtime)) return;
      row.classList.toggle('has-update', mtime > lastVisitedAt(name));
    });
  }

  function recordVisit(row) {
    if (!row || !row.dataset.name) return;
    const name = row.dataset.name;
    // Stamp with "now" so recently-visited sorts by actual click time. The
    // has-update badge still works because now > any past mtime, and if the
    // file is touched later (mtime > now) the badge reappears next render.
    localStorage.setItem(KEYS.visitedPrefix + name, new Date().toISOString());
    const countKey = KEYS.visitsPrefix + name;
    const current = parseInt(localStorage.getItem(countKey) || '0', 10) || 0;
    localStorage.setItem(countKey, String(current + 1));
    row.classList.remove('has-update');
    const mode = localStorage.getItem(KEYS.sort);
    if (mode === 'recently-visited' || mode === 'most-visited') {
      window.LP.sort?.reapply();
    }
  }

  // Record a visit for clicks that open the app in a NEW TAB: modifier +
  // left-click, or a non-primary button. Middle-clicks dispatch `auxclick`
  // (not `click`) in modern browsers, so we bind both. Plain left-clicks
  // open the in-page preview instead — peek.js records that visit — so we
  // skip them here to avoid double-counting.
  function onActivate(e) {
    const opensNewTab = e.metaKey || e.ctrlKey || e.shiftKey || e.altKey
      || (e.button !== undefined && e.button !== 0);
    if (!opensNewTab) return;
    const link = e.target.closest('a.body');
    if (link) recordVisit(link.closest('.row'));
  }
  document.addEventListener('click', onActivate);
  document.addEventListener('auxclick', onActivate);

  // Exposed so peek.js can record a visit when the preview opens.
  window.LP.recordVisit = recordVisit;

  window.addEventListener('pageshow', markRows);
})();
