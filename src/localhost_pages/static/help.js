// Help overlay: keyboard shortcut + interaction reference.
// Toggled by the ? button in the header or by pressing ? anywhere outside
// an input. Closes via × button, backdrop click, or Esc.
(function () {
  const HTML = `
    <div class="help-panel" role="dialog" aria-label="Keyboard shortcuts">
      <button class="help-close" type="button" aria-label="Close help">×</button>
      <h2>Navigation</h2>
      <dl>
        <dt><kbd>j</kbd> / <kbd>↓</kbd></dt><dd>focus next row</dd>
        <dt><kbd>k</kbd> / <kbd>↑</kbd></dt><dd>focus previous row</dd>
        <dt><kbd>/</kbd></dt><dd>focus search</dd>
        <dt><kbd>Esc</kbd></dt><dd>clear focus · clear search · close preview · leave edit mode</dd>
      </dl>
      <h2>On the focused row</h2>
      <dl>
        <dt><kbd>Enter</kbd></dt><dd>open preview</dd>
        <dt><kbd>p</kbd></dt><dd>pin / unpin to top</dd>
        <dt><kbd>x</kbd></dt><dd>delete (press again to confirm)</dd>
      </dl>
      <h2>In the preview</h2>
      <dl>
        <dt><kbd>f</kbd></dt><dd>open the full page</dd>
        <dt><kbd>Esc</kbd></dt><dd>close preview</dd>
      </dl>
      <h2>Modes</h2>
      <dl>
        <dt><kbd>e</kbd></dt><dd>toggle edit mode (drag rows to reorder)</dd>
        <dt><kbd>?</kbd></dt><dd>show / hide this help</dd>
      </dl>
      <h2>Mouse</h2>
      <dl>
        <dt>click row</dt><dd>open preview modal</dd>
        <dt>⌘ / ctrl / shift / middle-click</dt><dd>open in new tab</dd>
        <dt>hover row</dt><dd>reveal pin and × buttons</dd>
        <dt>click ↗ in preview</dt><dd>open full page</dd>
        <dt>click backdrop / ×</dt><dd>close preview</dd>
      </dl>
      <h2>Troubleshooting</h2>
      <dl>
        <dt><a class="diag-link" href="/__diagnostics" download="localhost-pages-diagnostics.txt">Download logs</a></dt>
        <dd>save a diagnostics bundle — logs plus environment — to attach to a bug report</dd>
      </dl>
    </div>
  `;

  let backdrop = null;
  const toggleBtn = document.querySelector('.help-toggle');

  function build() {
    if (backdrop) return;
    backdrop = document.createElement('div');
    backdrop.className = 'help-backdrop';
    backdrop.innerHTML = HTML;
    document.body.appendChild(backdrop);
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) close();
    });
    backdrop.querySelector('.help-close').addEventListener('click', close);
  }

  function isOpen() {
    return backdrop?.classList.contains('open');
  }

  function open() {
    build();
    backdrop.classList.add('open');
    document.body.classList.add('help-open');
    toggleBtn?.setAttribute('aria-pressed', 'true');
  }

  function close() {
    backdrop?.classList.remove('open');
    document.body.classList.remove('help-open');
    toggleBtn?.setAttribute('aria-pressed', 'false');
  }

  function toggle() {
    if (isOpen()) close(); else open();
  }

  toggleBtn?.addEventListener('click', toggle);

  window.LP.onEscape(80, () => {
    if (!isOpen()) return false;
    close();
    return true;
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === '?') {
      if (window.LP.isTypingTarget(e)) return;
      e.preventDefault();
      toggle();
    }
  });
})();
