// Browser-side error capture for the dashboard only — loaded by
// templates/index.html, deliberately NOT injected into served user apps
// (their runtime errors aren't localhost-pages bugs). Forwards to POST /__log.
// Must never throw or interfere with the page it's watching.
(function () {
  var ENDPOINT = "/__log";
  var sent = 0;
  var MAX = 25; // cap per page load so an error loop can't flood the log

  function send(payload) {
    if (sent >= MAX) return;
    sent++;
    try {
      var body = JSON.stringify(payload);
      if (navigator.sendBeacon) {
        navigator.sendBeacon(ENDPOINT, new Blob([body], { type: "application/json" }));
      } else {
        fetch(ENDPOINT, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: body,
          keepalive: true,
        });
      }
    } catch (_) {
      // Logging must be invisible — swallow everything.
    }
  }

  // Manual reporter for errors that are caught locally (try/catch around a
  // fetch, etc.) and therefore never reach the global 'error' handler below.
  // Exposed as a bare global because lp-log.js loads before lp-util.js, so
  // window.LP isn't defined yet. Callers guard with `window.lpReport &&`.
  window.lpReport = function (message, extra) {
    var payload = {
      message: String(message),
      page: location.pathname,
      userAgent: navigator.userAgent,
    };
    if (extra && extra.stack) payload.stack = String(extra.stack);
    send(payload);
  };

  window.addEventListener("error", function (e) {
    send({
      message: String((e && e.message) || (e && e.type) || "error"),
      source: (e && e.filename) || "",
      line: (e && e.lineno) || "",
      column: (e && e.colno) || "",
      stack: e && e.error && e.error.stack ? String(e.error.stack) : "",
      page: location.pathname,
      userAgent: navigator.userAgent,
    });
  });

  window.addEventListener("unhandledrejection", function (e) {
    var r = e && e.reason;
    send({
      message: "unhandledrejection: " + (r && r.message ? r.message : String(r)),
      stack: r && r.stack ? String(r.stack) : "",
      page: location.pathname,
      userAgent: navigator.userAgent,
    });
  });
})();
