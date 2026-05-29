from localhost_pages.inject import inject_reload_script

SNIPPET_MARKER = "data-localhost-pages-reload"


def test_injects_before_body_close():
    html = "<html><body>hi</body></html>"
    out = inject_reload_script(html, "myapp")
    assert SNIPPET_MARKER in out
    assert out.index(SNIPPET_MARKER) < out.index("</body>")
    assert 'data-app="myapp"' in out


def test_appends_when_no_body_close():
    html = "<html><body>hi"
    out = inject_reload_script(html, "myapp")
    assert SNIPPET_MARKER in out
    assert out.endswith("</script>")


def test_idempotent():
    html = "<html><body>hi</body></html>"
    once = inject_reload_script(html, "myapp")
    twice = inject_reload_script(once, "myapp")
    assert once == twice
    assert twice.count(SNIPPET_MARKER) == 1


def test_escapes_app_name():
    html = "<html><body></body></html>"
    out = inject_reload_script(html, 'evil"name')
    assert 'data-app="evil&quot;name"' in out


def test_injects_before_uppercase_body_close():
    html = "<HTML><BODY>hi</BODY></HTML>"
    out = inject_reload_script(html, "myapp")
    assert SNIPPET_MARKER in out
    assert out.index(SNIPPET_MARKER) < out.lower().index("</body>")


def test_marker_text_in_app_html_does_not_block_injection():
    # The app's HTML merely mentions the marker string in visible text;
    # it must still receive the live-reload <script>.
    html = "<html><body><p>data-localhost-pages-reload</p></body></html>"
    out = inject_reload_script(html, "myapp")
    assert "<script data-localhost-pages-reload" in out
