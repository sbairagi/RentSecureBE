"""A dependency free PDF writer.

WeasyPrint renders the agreement beautifully on the servers that have the
native libraries, but the native libraries are missing on the macOS
development machines and the test suite must not depend on them either.

This writer keeps the agreement workflow working everywhere: it lays the
agreement out as plain text pages in a valid, readable PDF file. It only
supports what the agreement needs — one column of text, three text styles
and automatic page breaks.
"""

from __future__ import annotations

from typing import Literal

TextStyle = Literal["title", "heading", "body", "muted", "gap"]

PAGE_WIDTH = 595
PAGE_HEIGHT = 842
MARGIN_LEFT = 56
MARGIN_TOP = 56
LINE_HEIGHT = 15

_STYLE_SIZES: dict[str, int] = {
    "title": 16,
    "heading": 11,
    "body": 9.5,
    "muted": 8.5,
    "gap": 9.5,
}

#: Characters that fit on one line at 9.5pt in Helvetica.
_LINE_CHARS = 92


def _escape(text: str) -> str:
    """Escape the characters that are special inside a PDF string."""
    return (
        text.replace("\\", r"\\")
        .replace("(", r"\(")
        .replace(")", r"\)")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def _wrap(text: str, size: float) -> list[str]:
    """Wrap a line so it fits the width of the page."""
    limit = max(int(_LINE_CHARS * 9.5 / size), 20)
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        if len(current) + 1 + len(word) <= limit:
            current = f"{current} {word}"
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _page_content(lines: list[tuple[str, TextStyle]]) -> bytes:
    """Return the content stream of one page."""
    parts: list[str] = ["BT"]
    y = PAGE_HEIGHT - MARGIN_TOP
    for text, style in lines:
        size = _STYLE_SIZES.get(style, 9.5)
        font = "F2" if style in ("title", "heading") else "F1"
        leading = LINE_HEIGHT if style not in ("title", "heading", "gap") else size + 6
        if style == "gap":
            y -= leading
            continue
        for line in _wrap(text, size):
            parts.append(f"/{font} {size} Tf")
            parts.append(f"1 0 0 1 {MARGIN_LEFT} {y:.1f} Tm")
            parts.append(f"({_escape(line)}) Tj")
            y -= leading
        if style in ("title", "heading"):
            y -= 3
    parts.append("ET")
    return "\n".join(parts).encode("latin-1", "replace")


def _paginate(lines: list[tuple[str, TextStyle]]) -> list[list[tuple[str, TextStyle]]]:
    """Split the lines into pages that fit the height of the page."""
    pages: list[list[tuple[str, TextStyle]]] = []
    current: list[tuple[str, TextStyle]] = []
    used = 0
    for text, style in lines:
        size = _STYLE_SIZES.get(style, 9.5)
        leading = LINE_HEIGHT if style not in ("title", "heading", "gap") else size + 6
        wrapped = _wrap(text, size)
        if used + leading * len(wrapped) > PAGE_HEIGHT - 2 * MARGIN_TOP:
            pages.append(current)
            current = []
            used = 0
        current.append((text, style))
        used += leading * len(wrapped)
    if current:
        pages.append(current)
    return pages or [[("", "body")]]


def build_text_pdf(lines: list[tuple[str, TextStyle]]) -> bytes:
    """Return a valid PDF file that renders ``lines``.

    Every item is a ``(text, style)`` pair where the style is one of
    ``title``, ``heading``, ``body``, ``muted`` or ``gap``.
    """
    pages = _paginate(lines)

    # Object 1 is the catalogue, object 2 the page tree, 3 and 4 the fonts.
    objects: list[bytes] = [
        b"",  # 1: catalogue
        b"",  # 2: page tree
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",  # 3
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",  # 4
    ]

    page_ids: list[int] = []
    for page in pages:
        content = _page_content(page)
        content_id = len(objects) + 1
        objects.append(
            f"<< /Length {len(content)} >>\nstream\n".encode("latin-1")
            + content
            + b"\nendstream"
        )
        page_id = len(objects) + 1
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R "
                f"/MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
                f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> "
                f"/Contents {content_id} 0 R >>"
            ).encode("latin-1")
        )
        page_ids.append(page_id)

    objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode(
        "latin-1"
    )

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets: list[int] = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode("latin-1")
        out += body
        out += b"\nendobj\n"

    xref_offset = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode("latin-1")
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode("latin-1")
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode("latin-1")
    return bytes(out)
