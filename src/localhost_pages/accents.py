from __future__ import annotations

import hashlib

# 32 muted pastels — desaturated, dusty, all readable on #1a1822.
# Organized as 8 hue families × 4 shades. Each colour has a unique name so
# apps can opt into any specific accent via meta.json.
NAMED_ACCENTS: dict[str, str] = {
    # Base shades — one of each hue family
    "sage":     "#a8c8a3",
    "mauve":    "#c8a3c4",
    "rose":     "#d6a3a3",
    "powder":   "#a3b8d6",
    "sand":     "#c4b8a3",
    "mist":     "#a3c4c4",
    "peach":    "#d6c4a3",
    "lavender": "#b8a3d6",
    # Lighter shades
    "fern":     "#bdd0b8",
    "blossom":  "#d4b8d0",
    "coral":    "#e0b5b5",
    "sky":      "#b5c8e0",
    "wheat":    "#d0c8b5",
    "seafoam":  "#b5d0d0",
    "honey":    "#e0d0b5",
    "lilac":    "#c8b5e0",
    # Darker shades
    "moss":     "#9eb89e",
    "orchid":   "#b89eb4",
    "clay":     "#c89e9e",
    "denim":    "#9eaecc",
    "taupe":    "#b8a896",
    "slate":    "#96b4b4",
    "ochre":    "#c8b496",
    "iris":     "#a896c8",
    # Palest shades
    "mint":     "#c0d4ba",
    "petal":    "#d4bac8",
    "blush":    "#dcbcbc",
    "ice":      "#bcc4dc",
    "linen":    "#d4c8bc",
    "frost":    "#bcd4d4",
    "cream":    "#dcd0bc",
    "thistle":  "#c8bcdc",
}

PALETTE: tuple[str, ...] = tuple(NAMED_ACCENTS.values())


def _hash_index(name: str) -> int:
    digest = hashlib.sha1(name.encode("utf-8")).hexdigest()
    return int(digest, 16) % len(PALETTE)


def resolve_accent(value: str | None, name: str) -> str:
    """Return a hex color (#rrggbb) for this app row.

    Resolution order:
      1. None / empty                  → hash(name) → PALETTE
      2. exact match in NAMED_ACCENTS  → mapped hex
      3. anything else                 → hash fallback
    """
    if not value:
        return PALETTE[_hash_index(name)]
    if value in NAMED_ACCENTS:
        return NAMED_ACCENTS[value]
    return PALETTE[_hash_index(name)]
