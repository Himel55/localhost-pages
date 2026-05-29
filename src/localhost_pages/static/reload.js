(function () {
  var script = document.currentScript;
  var app = script && script.getAttribute("data-app");
  if (!app) return;
  var url = "/__events?app=" + encodeURIComponent(app);
  var es;
  var pendingReload = false;

  function overlayOpen() {
    return !!document.querySelector(".peek-backdrop.open, .help-backdrop.open");
  }

  function onChange() {
    // On the index page a preview/help overlay may own the screen — a
    // location.reload() would destroy it mid-view. Defer the reload until
    // the overlay closes. App pages have no such overlays, so overlayOpen()
    // is false there and they reload immediately.
    if (!overlayOpen()) { location.reload(); return; }
    if (pendingReload) return;
    pendingReload = true;
    var iv = setInterval(function () {
      if (!overlayOpen()) {
        clearInterval(iv);
        location.reload();
      }
    }, 200);
  }

  function connect() {
    es = new EventSource(url);
    es.addEventListener("change", onChange);
    es.onerror = function () {
      es.close();
      setTimeout(connect, 1000);
    };
  }
  connect();
})();
