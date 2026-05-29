from localhost_pages.icons import resolve_icon


def test_inline_svg_passes_through():
    raw = "<svg xmlns='http://www.w3.org/2000/svg'><path d='M0 0h10'/></svg>"
    assert resolve_icon(raw) == raw


def test_emoji_is_wrapped_in_span():
    out = resolve_icon("📊")
    assert out == '<span class="icon-emoji">📊</span>'


def test_lucide_name_returns_svg():
    out = resolve_icon("box")
    assert out.startswith("<svg")
    assert "</svg>" in out


def test_unknown_lucide_name_falls_back_to_box(caplog):
    import logging
    caplog.set_level(logging.WARNING)
    box = resolve_icon("box")
    fallback = resolve_icon("definitely-not-a-real-icon-xyz")
    assert fallback == box
    assert any("not found" in r.message for r in caplog.records)


def test_missing_value_returns_box():
    assert resolve_icon(None) == resolve_icon("box")
    assert resolve_icon("") == resolve_icon("box")


def test_short_text_treated_as_emoji():
    assert resolve_icon("🎨") == '<span class="icon-emoji">🎨</span>'
