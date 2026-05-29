(function () {
  function reset(row) {
    delete row.dataset.confirming;
    const btn = row.querySelector('.del');
    if (btn) btn.textContent = '×';
  }

  function arm(row) {
    row.dataset.confirming = 'true';
    const btn = row.querySelector('.del');
    if (btn) btn.textContent = '× CONFIRM';
  }

  // Drop the deleted app's per-app localStorage so a re-created app of the
  // same name doesn't silently inherit stale pin / visit / order state.
  function purgeStorage(name) {
    try {
      localStorage.removeItem('lp:visited:' + name);
      localStorage.removeItem('lp:visits:' + name);
      ['lp:pinned', 'lp:order'].forEach((key) => {
        const raw = localStorage.getItem(key);
        if (!raw) return;
        let arr;
        try { arr = JSON.parse(raw); } catch { return; }
        if (!Array.isArray(arr)) return;
        const next = arr.filter((n) => n !== name);
        if (next.length !== arr.length) localStorage.setItem(key, JSON.stringify(next));
      });
    } catch { /* localStorage unavailable — nothing to prune */ }
  }

  async function doDelete(row) {
    const name = row.dataset.name;
    try {
      const res = await fetch('/__apps/' + encodeURIComponent(name), { method: 'DELETE' });
      if (res.ok) {
        purgeStorage(name);
        row.remove();
      } else {
        if (window.lpReport) {
          window.lpReport('delete failed for ' + name + ': ' + res.status + ' ' + res.statusText);
        }
        alert('Delete failed: ' + res.status + ' ' + res.statusText);
        reset(row);
      }
    } catch (err) {
      if (window.lpReport) {
        window.lpReport('delete request error for ' + name + ': ' + err, err);
      }
      alert('Delete failed: ' + err);
      reset(row);
    }
  }

  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.del');
    if (btn) {
      e.preventDefault();
      e.stopPropagation();
      const row = btn.closest('.row');
      if (!row) return;
      // Cancel any other rows that were armed.
      document.querySelectorAll('.row[data-confirming]').forEach((r) => {
        if (r !== row) reset(r);
      });
      if (row.dataset.confirming) {
        doDelete(row);
      } else {
        arm(row);
      }
      return;
    }
    // Click on a row that's currently in confirming state (anywhere but
    // the × button): cancel that row's confirm and DO NOT navigate.
    const confirmingRow = e.target.closest('.row[data-confirming]');
    if (confirmingRow) {
      e.preventDefault();
      e.stopImmediatePropagation();
      reset(confirmingRow);
      return;
    }
    // Click anywhere else cancels all armed rows.
    document.querySelectorAll('.row[data-confirming]').forEach(reset);
  });

  // Esc cancels any armed delete-confirm; highest priority so it wins over
  // focus-clearing and other dismissers when a row is armed.
  window.LP.onEscape(100, () => {
    const armed = document.querySelectorAll('.row[data-confirming]');
    if (!armed.length) return false;
    armed.forEach(reset);
    return true;
  });
})();
