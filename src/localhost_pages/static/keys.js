// Keyboard navigation:
//   j / ArrowDown — focus next visible row
//   k / ArrowUp   — focus previous visible row
//   Enter         — open the focused row
//   x             — arm/confirm delete on the focused row
//   p             — toggle pin on the focused row
//   e             — toggle edit mode
//   /             — focus the search input (already handled in search.js)
//   Esc           — clear search / leave edit mode (handled per-feature)
// All bindings are no-ops when the user is typing in an input.
(function () {
  const list = document.querySelector('.apps');
  if (!list) return;

  function visibleRows() {
    return Array.from(list.querySelectorAll('.row')).filter((r) => r.style.display !== 'none');
  }

  function focusedRow() {
    return document.activeElement?.closest?.('.row') || document.querySelector('.row.kbd-focus');
  }

  function setFocus(row) {
    list.querySelectorAll('.row.kbd-focus').forEach((r) => r.classList.remove('kbd-focus'));
    if (!row) return;
    row.classList.add('kbd-focus');
    row.scrollIntoView({ block: 'nearest' });
  }

  function move(delta) {
    const rows = visibleRows();
    if (!rows.length) return;
    const current = focusedRow();
    let i = rows.indexOf(current);
    if (i === -1) i = delta > 0 ? -1 : rows.length;
    const next = rows[Math.max(0, Math.min(rows.length - 1, i + delta))];
    setFocus(next);
  }

  // Lowest-priority Esc handler: only clears the focus highlight, and only
  // if no higher-priority dismisser (preview, help, edit, etc.) consumed it.
  window.LP.onEscape(10, () => {
    const focused = document.querySelector('.row.kbd-focus');
    if (!focused) return false;
    setFocus(null);
    return true;
  });

  document.addEventListener('keydown', (e) => {
    if (window.LP.isTypingTarget(e)) return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;

    // While a preview or help overlay owns the screen, the index's action
    // keys must be inert. Those overlays trap their own keys (Esc, ?, f)
    // but let every other key fall through to here.
    if (document.querySelector('.peek-backdrop.open, .help-backdrop.open')) return;

    switch (e.key) {
      case 'j':
      case 'ArrowDown':
        e.preventDefault();
        move(1);
        return;
      case 'k':
      case 'ArrowUp':
        e.preventDefault();
        move(-1);
        return;
      case 'Enter': {
        const row = focusedRow();
        if (!row) return;
        e.preventDefault();
        // Plain row click is intercepted by peek.js to open the preview.
        row.click();
        return;
      }
      case 'x': {
        // Edit mode hides the × button to prevent fat-finger deletes;
        // the keyboard delete path must respect the same guard.
        if (document.body.classList.contains('editing')) return;
        const row = focusedRow();
        if (!row) return;
        e.preventDefault();
        row.querySelector('.del')?.click();
        return;
      }
      case 'p': {
        const row = focusedRow();
        if (!row) return;
        e.preventDefault();
        row.querySelector('.pin')?.click();
        return;
      }
      case 'e':
        e.preventDefault();
        document.querySelector('.edit-toggle')?.click();
        return;
    }
  });
})();
