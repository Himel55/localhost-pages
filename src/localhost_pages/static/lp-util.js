// Shared helpers for the index UI scripts. Loaded before every other
// static script so `window.LP` is available to them.
window.LP = (function () {
  const KEYS = {
    sort: 'lp:sort',
    order: 'lp:order',
    pinned: 'lp:pinned',
    visitedPrefix: 'lp:visited:',
    visitsPrefix: 'lp:visits:',
  };

  function loadArray(key) {
    try {
      const raw = localStorage.getItem(key);
      const v = raw ? JSON.parse(raw) : [];
      return Array.isArray(v) ? v : [];
    } catch {
      return [];
    }
  }

  function saveArray(key, arr) {
    localStorage.setItem(key, JSON.stringify(arr));
  }

  function isTypingTarget(e) {
    const tag = (e.target && e.target.tagName) || '';
    return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT';
  }

  // Single Escape dispatcher. Features register a handler with a priority;
  // higher priority runs first. A handler returns true if it consumed the
  // Escape (stopping lower-priority handlers), false to pass it through.
  // Replaces the per-script stopImmediatePropagation dance and load-order
  // dependence.
  const escapeHandlers = [];
  function onEscape(priority, fn) {
    escapeHandlers.push({ priority, fn });
    escapeHandlers.sort((a, b) => b.priority - a.priority);
  }

  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    for (const h of escapeHandlers) {
      if (h.fn(e)) {
        e.preventDefault();
        return;
      }
    }
  });

  return { KEYS, loadArray, saveArray, isTypingTarget, onEscape };
})();
