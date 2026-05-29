// Preview modal: clicking anywhere on a row opens a centered iframe of the
// row's app. The .open button (top-right) and modifier-clicks (cmd/ctrl,
// middle-click) bypass this and navigate to the actual page.
// Closes via the × button, clicking the backdrop, or pressing Esc.
(function () {
  let backdrop = null;
  let modal = null;
  let openRow = null;

  function build() {
    if (modal) return;
    backdrop = document.createElement('div');
    backdrop.className = 'peek-backdrop';
    modal = document.createElement('div');
    modal.className = 'peek-modal';
    modal.innerHTML =
      '<a class="peek-open" href="#" aria-label="Open full page" title="Open full page">' +
        '<svg viewBox="0 0 24 24" aria-hidden="true">' +
          '<path d="M15 3h6v6"/>' +
          '<path d="M10 14 21 3"/>' +
          '<path d="M21 14v5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5"/>' +
        '</svg>' +
      '</a>' +
      '<button class="peek-close" type="button" aria-label="Close preview">×</button>' +
      '<iframe sandbox="allow-same-origin allow-scripts" referrerpolicy="no-referrer"></iframe>';
    backdrop.appendChild(modal);
    document.body.appendChild(backdrop);

    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) close();
    });
    modal.querySelector('.peek-close').addEventListener('click', close);
    // Maximize: replace the peek-state history entry instead of pushing a
    // new one, so back from the full page returns to the bare index — not
    // a bfcache-restored open preview.
    modal.querySelector('.peek-open').addEventListener('click', (e) => {
      const a = e.currentTarget;
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      if (e.button !== undefined && e.button !== 0) return;
      e.preventDefault();
      window.location.replace(a.href);
    });
  }

  function open(row) {
    if (!row || !row.dataset.name) return;
    if (row.classList.contains('broken')) return;
    if (document.body.classList.contains('editing')) return;
    build();
    openRow = row;
    const url = '/' + encodeURIComponent(row.dataset.name) + '/';
    // Use location.replace so the iframe load does NOT add an entry to the
    // top-level back stack. If we used iframe.src instead, the back button
    // would have to pop the iframe nav first before reaching our pushState.
    const iframe = modal.querySelector('iframe');
    try {
      iframe.contentWindow.location.replace(url);
    } catch {
      iframe.src = url;
    }
    modal.querySelector('.peek-open').href = url;
    backdrop.classList.add('open');
    history.pushState({ peek: row.dataset.name }, '');
    // Opening the preview counts as a visit (drives recently-visited /
    // most-visited sorts and clears the has-update indicator).
    window.LP.recordVisit?.(row);
  }

  function close(fromPopstate = false) {
    if (!backdrop) return;
    if (!backdrop.classList.contains('open')) return;
    backdrop.classList.remove('open');
    const iframe = modal.querySelector('iframe');
    try {
      iframe.contentWindow.location.replace('about:blank');
    } catch {
      iframe.src = 'about:blank';
    }
    openRow = null;
    if (!fromPopstate && history.state?.peek) history.back();
  }

  window.addEventListener('popstate', () => {
    if (backdrop?.classList.contains('open')) close(true);
  });

  document.addEventListener('click', (e) => {
    // Modifier-clicks should keep their native "open in new tab/window"
    // behavior on the underlying <a class="body"> link.
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    if (e.button !== undefined && e.button !== 0) return;
    // Let the explicit .open / .pin / .del buttons do their own thing.
    if (e.target.closest('.open, .pin, .del')) return;
    const row = e.target.closest('.row');
    if (!row) return;
    if (row.classList.contains('broken')) return;
    if (document.body.classList.contains('editing')) return;
    if (row.hasAttribute('data-confirming')) return;  // delete.js handles this
    e.preventDefault();
    open(row);
  });

  window.LP.onEscape(90, () => {
    if (!backdrop?.classList.contains('open')) return false;
    close();
    return true;
  });

  document.addEventListener('keydown', (e) => {
    if (!backdrop?.classList.contains('open')) return;
    if (e.key === 'f' || e.key === 'F') {
      if (window.LP.isTypingTarget(e)) return;
      e.preventDefault();
      const link = modal.querySelector('.peek-open');
      if (link?.href) window.location.replace(link.href);
    }
  });
})();
