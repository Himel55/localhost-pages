// Live filter the index by app name / title / description.
// Pressing "/" anywhere on the page focuses the input.
(function () {
  const input = document.querySelector('.search');
  if (!input) return;

  function apply() {
    const q = input.value.trim().toLowerCase();
    document.querySelectorAll('.row').forEach((row) => {
      const name = (row.dataset.name || '').toLowerCase();
      const title = (row.querySelector('.name')?.textContent || '').toLowerCase();
      const desc = (row.querySelector('.desc')?.textContent || '').toLowerCase();
      const match = !q || name.includes(q) || title.includes(q) || desc.includes(q);
      row.style.display = match ? '' : 'none';
    });
    // Re-gap the visible row numbers now that some rows are hidden.
    window.LP.sort?.renumber?.();
  }

  input.addEventListener('input', apply);

  const clearBtn = document.querySelector('.search-clear');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      input.value = '';
      apply();
      input.focus();
    });
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === '/' && document.activeElement !== input) {
      e.preventDefault();
      input.focus();
      input.select();
    }
  });

  window.LP.onEscape(50, () => {
    if (document.activeElement !== input) return false;
    input.value = '';
    apply();
    input.blur();
    return true;
  });
})();
