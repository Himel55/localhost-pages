from __future__ import annotations

from html import escape

MARKER = "data-localhost-pages-reload"
STATIC_PREFIX = "/__static"
# Idempotency is keyed on our actual injected <script> tag, not the bare
# marker — an app whose HTML merely *mentions* the marker string (in text
# or a comment) must still receive live-reload.
_SCRIPT_PREFIX = f"<script {MARKER}"


def reload_script_tag(app_name: str) -> str:
    return (f'<script {MARKER} src="{STATIC_PREFIX}/reload.js" '
            f'data-app="{escape(app_name, quote=True)}"></script>')


def inject_reload_script(html: str, app_name: str) -> str:
    # Served app pages are the user's own HTML; we inject only the live-reload
    # client (the core feature). Browser error capture (lp-log.js) is *not*
    # injected here — it would log the user's own app errors as noise. That
    # script is loaded only on the localhost-pages dashboard (index.html),
    # where it captures our own frontend's bugs.
    if _SCRIPT_PREFIX in html:
        return html
    tag = reload_script_tag(app_name)
    # Match </body> case-insensitively (e.g. </BODY>) so the script lands
    # before the closing tag rather than after </html>.
    idx = html.lower().rfind("</body>")
    if idx == -1:
        return html + tag
    return html[:idx] + tag + html[idx:]
