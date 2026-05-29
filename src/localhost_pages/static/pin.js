// Pin / unpin apps to the top of the index. Pinned set is a JSON array of
// app names in localStorage. Adds a .pinned class to matching rows so
// sort.js keeps them above the unpinned section and CSS can highlight the
// pin button.
(function () {
  const { KEYS, loadArray, saveArray } = window.LP;

  function toggle(name) {
    const arr = loadArray(KEYS.pinned);
    const i = arr.indexOf(name);
    if (i === -1) arr.push(name); else arr.splice(i, 1);
    saveArray(KEYS.pinned, arr);
  }

  function markRows() {
    const set = new Set(loadArray(KEYS.pinned));
    document.querySelectorAll('.row').forEach((row) => {
      row.classList.toggle('pinned', set.has(row.dataset.name));
    });
  }

  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.pin');
    if (!btn) return;
    e.preventDefault();
    e.stopPropagation();
    const row = btn.closest('.row');
    if (!row || !row.dataset.name) return;
    toggle(row.dataset.name);
    markRows();
    window.LP.sort?.reapply();
  });

  markRows();
  window.addEventListener('pageshow', markRows);
})();
