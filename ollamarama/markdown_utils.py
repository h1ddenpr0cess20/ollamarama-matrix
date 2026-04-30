from __future__ import annotations

import re
from typing import Optional

import markdown


MATRIX_MARKDOWN_EXTENSIONS = [
    "extra",
    "fenced_code",
    "nl2br",
    "sane_lists",
    "tables",
]

_LIST_ITEM_RE = re.compile(r"^(\s*([-*+]|\d+[.)]))(\s|$)")
_OL_MARKER_RE = re.compile(r"^\s*\d+[.)]")


def _list_key(line: str) -> tuple[int, str] | None:
    """Return (indent, kind) for a list item line, or None if not a list item."""
    if not _LIST_ITEM_RE.match(line):
        return None
    indent = len(line) - len(line.lstrip())
    kind = "ol" if _OL_MARKER_RE.match(line) else "ul"
    return (indent, kind)


def _normalize_list_spacing(body: str) -> str:
    """Fix list spacing for Matrix rendering with nl2br.

    1. Insert a blank line before the first list item when it immediately
       follows a paragraph (nl2br would otherwise swallow the list markers).
    2. Remove blank lines between consecutive items of the same list (same
       indent + marker type), preventing loose-list <p> wrappers that cause
       some Matrix clients to render the number on a separate line.
    """
    lines = body.splitlines()

    # Pass 1: ensure blank line before list that follows paragraph text
    step1: list[str] = []
    for i, line in enumerate(lines):
        if i > 0 and _LIST_ITEM_RE.match(line):
            prev = lines[i - 1]
            if prev.strip() and not _LIST_ITEM_RE.match(prev):
                step1.append("")
        step1.append(line)

    # Pass 2: collapse blank lines between items of the same list
    n = len(step1)
    out: list[str] = []
    for i, line in enumerate(step1):
        if not line.strip():
            prev_nb = next((step1[j] for j in range(i - 1, -1, -1) if step1[j].strip()), "")
            next_nb = next((step1[j] for j in range(i + 1, n) if step1[j].strip()), "")
            if _list_key(prev_nb) and _list_key(prev_nb) == _list_key(next_nb):
                continue
        out.append(line)

    return "\n".join(out)


def _unwrap_li_paragraphs(html: str) -> str:
    """Remove <p> wrappers that are the first child of <li> elements.

    When loose Markdown lists are rendered, each <li> gets a <p> child.
    Several Matrix clients (e.g. Element) render <li><p>text</p> with the
    list marker on its own line, detached from the content. Stripping the
    leading <p> (and the trailing </p> when it directly precedes </li>)
    keeps the number/bullet on the same line as the content.
    """
    html = re.sub(r"(<li[^>]*>)\s*<p>", r"\1", html)
    html = re.sub(r"</p>(\s*</li>)", r"\1", html)
    return html


def render_markdown(body: str) -> Optional[str]:
    """Render Markdown to Matrix-safe HTML.

    Avoid ``codehilite`` here. It emits ``div``/``span``-heavy HTML that Matrix
    clients frequently sanitize in ways that break fenced code blocks.
    """
    try:
        html = markdown.markdown(_normalize_list_spacing(body), extensions=MATRIX_MARKDOWN_EXTENSIONS)  # type: ignore[arg-type]
        return _unwrap_li_paragraphs(html)
    except Exception:
        return None
