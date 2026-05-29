from localhost_pages.accents import PALETTE, NAMED_ACCENTS, resolve_accent


def test_palette_has_32_colors():
    assert len(PALETTE) == 32
    for hex_ in PALETTE:
        assert hex_.startswith("#")
        assert len(hex_) == 7  # #rrggbb


def test_named_color_resolves_to_known_hex():
    assert resolve_accent("sage", "any-name") == NAMED_ACCENTS["sage"]


def test_hex_value_is_not_accepted():
    # Only named accents are honored; raw hex falls back to the hash-assigned palette color.
    result = resolve_accent("#7fffaf", "scraper")
    assert result in PALETTE


def test_unknown_name_falls_back_to_hash():
    result = resolve_accent("not-a-color", "scraper")
    assert result in PALETTE


def test_missing_value_uses_hash():
    a = resolve_accent(None, "scraper")
    b = resolve_accent(None, "scraper")
    assert a == b  # deterministic
    assert a in PALETTE


def test_different_names_can_get_different_colors():
    names = [f"app-{i}" for i in range(50)]
    seen = {resolve_accent(None, n) for n in names}
    assert len(seen) > 1
