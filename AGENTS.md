# Registering an AI app with localhost-pages

`localhost-pages` is a tiny always-on local web server at `http://localhost/`. Each registered app gets:

- A card on the index page at `/`
- Its own URL at `/<app-name>/`
- Auto-reload in the browser whenever any file in its directory changes

## Where the symlinks live

By default, the server watches the `symlinks/` directory **inside the localhost-pages repo** (e.g. `/path/to/localhost-pages/symlinks/`). If the operator started the server with `LOCALHOST_PAGES_SYMLINKS=/some/other/dir`, register your app there instead.

Throughout this doc, `<symlinks-dir>` refers to whichever directory is in use. To check at runtime, either:

- read the operator's setup, or
- visit `http://localhost/` and inspect any existing card's URL.

## How to register

1. **Make sure your app writes its output to a single directory.** At minimum, an `index.html`. Example output dirs:
   - macOS / Linux: `/Users/you/code/my-app/output/` or `/home/you/my-app/output/`
   - Windows: `C:\Users\you\code\my-app\output\`

2. **Create a symlink** in `<symlinks-dir>` pointing to that directory. The symlink's filename becomes the URL segment — use kebab-case, avoid spaces.

   ### macOS / Linux

   ```bash
   ln -s /absolute/path/to/your-app/output <symlinks-dir>/your-app
   ```

   Concrete example, assuming the repo is at `~/Projects/localhost-pages`:

   ```bash
   ln -s ~/code/my-scraper/output ~/Projects/localhost-pages/symlinks/my-scraper
   ```

   ### Windows

   `mklink /D` requires either an **admin shell** or **Developer Mode** enabled in Windows Settings → Privacy & Security → For Developers.

   ```cmd
   mklink /D <symlinks-dir>\your-app C:\absolute\path\to\your-app\output
   ```

   Concrete example, assuming the repo is at `%USERPROFILE%\Projects\localhost-pages`:

   ```cmd
   mklink /D %USERPROFILE%\Projects\localhost-pages\symlinks\my-scraper C:\code\my-scraper\output
   ```

3. **Visit** `http://localhost/your-app/` (or `http://localhost:8080/your-app/` if the operator hasn't set up port 80).

That's it. No config to edit, no server to restart — the watcher picks up the new symlink within a second.

## `meta.json` (optional)

Drop a `meta.json` next to your `index.html` to control how the row looks on the index page:

```json
{
  "title": "My Scraper Dashboard",
  "description": "Hourly scrape of X, rendered as a table.",
  "icon": "chart-bar",
  "accent": "sage"
}
```

All fields are optional.

| Field         | Type   | Default        | Notes                                                                                                                                                                                |
| ------------- | ------ | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `title`       | string | symlink name   | Display name shown in the row.                                                                                                                                                       |
| `description` | string | `""`           | Subtitle text under the name.                                                                                                                                                        |
| `icon`        | string | `"box"`        | One of: a [Lucide icon name](https://lucide.dev/icons/) (`"chart-bar"`, `"palette"`, `"lightbulb"`…), an emoji (`"📊"`), or a raw SVG string (`"<svg>...</svg>"`).                       |
| `accent`      | string | hash-of-name   | One of the 32 muted-pastel accent names (see below). When omitted (or unrecognized), an accent is auto-picked from the palette by hashing the app name (deterministic, so the same app always gets the same color across reloads). |

The 32 accent names, organized by hue family and shade:

| Hue family | Base       | Lighter   | Darker  | Palest    |
| ---------- | ---------- | --------- | ------- | --------- |
| Green      | `sage`     | `fern`    | `moss`  | `mint`    |
| Pink       | `mauve`    | `blossom` | `orchid`| `petal`   |
| Red        | `rose`     | `coral`   | `clay`  | `blush`   |
| Blue       | `powder`   | `sky`     | `denim` | `ice`     |
| Tan        | `sand`     | `wheat`   | `taupe` | `linen`   |
| Teal       | `mist`     | `seafoam` | `slate` | `frost`   |
| Yellow     | `peach`    | `honey`   | `ochre` | `cream`   |
| Purple     | `lavender` | `lilac`   | `iris`  | `thistle` |

If `meta.json` is malformed, defaults are used and a warning is logged — the row still renders.

## Auto-reload

Open tabs viewing `/<app>/` automatically reload when **any file** in the symlinked directory changes (recursive). For most AI apps, simply overwriting `index.html` is enough. The server injects a tiny SSE-driven script into served HTML — you don't need to add anything.

## Errors

- **Broken symlink** or **missing `index.html`**: the card appears greyed-out on the index with the error message.
- **Path traversal** attempts (`/<app>/../../etc/passwd`) return 404.

## File layout your app should produce

```
/absolute/path/to/your-app/output/
├── index.html       ← required
├── meta.json        ← optional (controls card appearance)
├── style.css        ← any extra assets you reference are served too
└── data.json
```

## Naming reserved

Symlink names starting with `__` (double underscore) are reserved for internal routes (`/__events`, `/__static/`). Any other kebab-case name is fine.
