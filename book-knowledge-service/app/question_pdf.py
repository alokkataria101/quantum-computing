"""app/question_pdf.py – one PDF per book with every question cropped from the
original pages (figures included), indexed by chapter and category.

Pipeline
    1. ``read_page``      – line boxes (+ font size / bold) of a page, garbled text decoded.
    2. ``scan_chapter``   – walks the lines in reading order (left column, then right
                            column, per band between full-width section headers) and
                            groups them into ``Item`` s (Example, Worked Out Example,
                            Short Answer, Objective I/II, Exercise).  An item may span
                            several *pieces* (column break / page break).
    3. ``render_item``    – crops every piece from the page and stitches them into one
                            aligned image.  Figures are included by also scanning the
                            gap below the last text line for ink.
    4. ``build_book_pdf`` – lays the items out chapter by chapter, category by category,
                            with a contents page, links and PDF bookmarks.

Run:  python -m app.question_pdf --pdf books/physics-book-1.pdf
"""

from __future__ import annotations

import argparse
import io
import logging
import re
import sqlite3
import statistics
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

import pymupdf as fitz
from PIL import Image

from .models import QuestionType

logger = logging.getLogger(__name__)

HEAD_FRAC = 0.055      # running head lives above this fraction of the page height
FOOT_FRAC = 0.975      # and anything below this fraction is footer

CATEGORIES: list[tuple[QuestionType, str, str]] = [
    (QuestionType.example,        "Examples (in-text)",         "Example"),
    (QuestionType.worked_example, "Worked Out Examples",        "Worked Out Example"),
    (QuestionType.short_answer,   "Questions for Short Answer", "Short Answer"),
    (QuestionType.objective_1,    "Objective I",                "Objective I"),
    (QuestionType.objective_2,    "Objective II",               "Objective II"),
    (QuestionType.exercise,       "Exercises",                  "Exercise"),
]
_CAT_TITLE = {k: t for k, t, _ in CATEGORIES}
_CAT_SHORT = {k: s for k, _, s in CATEGORIES}

_HEADERS: list[tuple[object, re.Pattern]] = [
    (QuestionType.worked_example, re.compile(r"WORKED OUT EXAMPLES?")),
    (QuestionType.short_answer,   re.compile(r"QUESTIONS? FOR SHORT ANSWERS?")),
    (QuestionType.objective_2,    re.compile(r"OBJECTIVE (?:II|11|LL|IL|LI|H)")),
    (QuestionType.objective_1,    re.compile(r"OBJECTIVE (?:I|1|L)")),
    (QuestionType.exercise,       re.compile(r"EXERCISES?")),
    ("END",                       re.compile(r"ANSWERS?")),
]
_NUM_RE = re.compile(r"^\s*(\d{1,3}|[IlL|])(?:\s*[.,)]\s+\S|(\s*[.,)]\s*$)|(\s+)(?=[A-Z]))")
_EXAMPLE_RE = re.compile(r"^\s*(?:Solved\s+)?Example\s+(\d+(?:[.,]\d+)?)\s*$", re.I)


# ───────────────────────────── page reading ──────────────────────────────────

def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", "", text.upper())).strip()


def decode_text(raw: str, force: bool = False) -> str:
    """Undo the PDF font shift (every glyph code is 29 lower) seen on some pages.

    Garbled lines contain \\x03 where a space belongs, e.g. ``2%-(&7,9(\\x03 ,`` is
    ``OBJECTIVE I``.  Lines without \\x03 are returned unchanged.
    """
    if "\x03" not in raw and not force:
        return raw.strip()
    out = []
    for c in raw:
        if c == "\x03":
            out.append(" ")
        elif c == " ":
            continue
        elif ord(c) <= 0x5D:
            out.append(chr(ord(c) + 29))
        else:
            out.append(c)
    return re.sub(r"\s+", " ", "".join(out)).strip()


@dataclass(eq=False)
class Line:
    page: int            # 1-based page number
    x0: float
    y0: float
    x1: float
    y1: float
    text: str
    size: float
    hdr: object = None   # QuestionType / "END" when the line is a section header
    owner: Optional["Item"] = None


@dataclass
class PageData:
    number: int
    width: float
    height: float
    lines: list[Line]


@dataclass
class Layout:
    left_m: float            # left margin of the left column
    right_m: float           # left margin of the right column
    size_reliable: bool = False   # font sizes are crisp (book typeset, not OCR)
    body_size: float = 10.0       # size of running text, used when size_reliable


def read_page(page, number: int) -> PageData:
    w, h = page.rect.width, page.rect.height
    lines: list[Line] = []
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        for l in b["lines"]:
            spans = l["spans"]
            raw = "".join(s["text"] for s in spans)
            text = decode_text(raw)
            if not text:
                continue
            dom = max(spans, key=lambda s: len(s["text"].strip()))
            x0, y0, x1, y1 = l["bbox"]
            if y1 <= h * HEAD_FRAC or y0 >= h * FOOT_FRAC:
                continue                      # running head / foot
            ln = Line(number, x0, y0, x1, y1, text, float(dom["size"]))
            norm = _norm(text)
            if len(raw.strip()) <= 34 and w * 0.30 <= (x0 + x1) / 2 <= w * 0.70:
                # centred short line: try as-is, then with the font shift undone
                for cand in (norm, _norm(decode_text(raw, force=True))):
                    kind = next((k for k, pat in _HEADERS if pat.fullmatch(cand)), None)
                    if kind is not None:
                        ln.hdr = kind
                        break
            lines.append(ln)
    return PageData(number, w, h, lines)


def detect_layout(doc, sample: int = 40) -> Layout:
    n = doc.page_count
    pages = sorted({min(n - 1, 15 + i * max(1, (n - 15) // sample)) for i in range(sample)})
    lefts, rights, sizes, crisp, tot = [], [], [], 0, 0
    for pi in pages:
        pd = read_page(doc[pi], pi + 1)
        lx = [l.x0 for l in pd.lines if len(l.text) >= 25 and l.x0 < pd.width * 0.4]
        rx = [l.x0 for l in pd.lines if len(l.text) >= 25 and l.x0 > pd.width * 0.5]
        if len(lx) >= 5 and len(rx) >= 5:
            lefts.append(sorted(lx)[int(len(lx) * 0.15)])
            rights.append(sorted(rx)[int(len(rx) * 0.15)])
        for l in pd.lines:
            if len(l.text) >= 40:
                sizes.append(round(l.size * 2) / 2)
            tot += 1
            crisp += abs(l.size * 2 - round(l.size * 2)) < 0.02
    if not lefts:
        w = doc[0].rect.width
        return Layout(w * 0.055, w * 0.52)
    return Layout(
        statistics.median(lefts), statistics.median(rights),
        size_reliable=tot > 0 and crisp / tot > 0.8,
        body_size=Counter(sizes).most_common(1)[0][0] if sizes else 10.0,
    )


# ───────────────────────────── item scanning ─────────────────────────────────

@dataclass(eq=False)
class Item:
    kind: object
    number: str
    chapter: int
    lines: list[Line] = field(default_factory=list)
    solution_seen: bool = False

    @property
    def label(self) -> str:
        return f"{_CAT_SHORT[self.kind]} {self.number}"

    @property
    def first_page(self) -> int:
        return self.lines[0].page

    @property
    def last_page(self) -> int:
        return self.lines[-1].page


@dataclass
class Cell:
    """One column of one band of one page."""
    lines: list[Line] = field(default_factory=list)
    top: float = 0.0
    bottom: float = 0.0


@dataclass
class ChapterScan:
    items: list[Item]
    cells: dict[tuple[int, int, int], Cell]
    keys: dict[int, list[tuple[int, int, int]]] = field(default_factory=dict)  # id(item) -> cell keys


def _column(line: Line, layout: Layout) -> int:
    # left-column lines end before the gutter; a mid-column equation fragment starts
    # far from either margin, so judge by where the line sits, not only where it starts
    return 1 if line.x0 >= layout.right_m - 12 or (line.x0 + line.x1) / 2 >= layout.right_m - 6 else 0


def _plausible(n: int, last: int) -> bool:
    return (n in (1, 2)) if last == 0 else (last < n <= last + 3)


def scan_chapter(pages: list[PageData], layout: Layout, chapter: int) -> ChapterScan:
    items: list[Item] = []
    cells: dict[tuple[int, int, int], Cell] = {}
    section: object = None
    last_num = 0
    cur: Optional[Item] = None
    ended = False

    def close() -> None:
        nonlocal cur
        cur = None

    for pd in pages:
        if ended:
            break
        headers = sorted((l for l in pd.lines if l.hdr is not None), key=lambda l: l.y0)
        if any(h.hdr == "END" for h in headers):      # everything after ANSWERS is the answer key
            end_y = min(h.y0 for h in headers if h.hdr == "END")
            headers = [h for h in headers if h.y0 <= end_y]
            ended = True
        body = [l for l in pd.lines if l.hdr is None]
        top_lim, bot_lim = pd.height * HEAD_FRAC, pd.height * FOOT_FRAC
        for b in range(len(headers) + 1):
            if b > 0:
                h = headers[b - 1]
                close()
                if h.hdr == "END":
                    section = None
                    last_num = -1          # nothing numbered until a new section header
                else:
                    section, last_num = h.hdr, 0
            if section is None and last_num == -1:
                break
            lo = headers[b - 1].y1 if b > 0 else top_lim
            hi = headers[b].y0 if b < len(headers) else bot_lim
            band = [l for l in body if lo - 1 <= l.y0 < hi]
            for col in (0, 1):
                cell_lines = sorted((l for l in band if _column(l, layout) == col),
                                    key=lambda l: (l.y0, l.x0))
                if not cell_lines:
                    continue
                cells[(pd.number, b, col)] = Cell(cell_lines, lo, hi)
                margin = layout.right_m if col else layout.left_m
                for ln in cell_lines:
                    started = False
                    if ln.x0 <= margin + 14:
                        if section is None and len(ln.text) <= 24:
                            m = _EXAMPLE_RE.match(ln.text)
                            if m:
                                close()
                                cur = Item(QuestionType.example, _example_number(m.group(1), chapter), chapter)
                                items.append(cur)
                                started = True
                        elif section is not None and last_num >= 0:
                            m = _NUM_RE.match(ln.text)
                            num = (1 if m.group(1) in "IlL|" else int(m.group(1))) if m else 0
                            # a lone "13." or a dot-less "26 A ..." is only trusted as the next number
                            if m and _plausible(num, last_num) and (
                                    not (m.group(2) or m.group(3)) or num == last_num + 1):
                                stray = _same_row_tail(cur, ln, cell_lines)
                                close()
                                last_num = num
                                cur = Item(section, str(num), chapter)
                                items.append(cur)
                                for sl in stray:
                                    sl.owner = cur
                                    cur.lines.append(sl)
                                started = True
                    if started:
                        cur.lines.append(ln); ln.owner = cur
                        continue
                    if cur is None:
                        continue
                    if cur.kind == QuestionType.example:
                        if ln.text.startswith("Solution"):
                            cur.solution_seen = True
                        elif cur.solution_seen and _example_over(ln, margin, layout):
                            close()
                            continue
                    cur.lines.append(ln); ln.owner = cur

    scan = ChapterScan(items, cells)
    for key, cell in cells.items():
        for ln in cell.lines:
            if ln.owner is not None:
                scan.keys.setdefault(id(ln.owner), [])
                if key not in scan.keys[id(ln.owner)]:
                    scan.keys[id(ln.owner)].append(key)
    for it in items:
        scan.keys.get(id(it), []).sort()
    return scan


def _same_row_tail(prev: Optional[Item], start: Line, cell_lines: list[Line]) -> list[Line]:
    """Fragments (vectors, fractions) printed on the same row as a new question number
    sort just before it and would be taken by the previous item; give them back."""
    if prev is None:
        return []
    moved: list[Line] = []
    for ln in reversed(prev.lines):
        if ln.page != start.page or ln not in cell_lines:
            break
        if ln.y1 > start.y0 and ln.y0 >= start.y0 - 8 and ln.x0 > start.x0:
            moved.append(ln)
        else:
            break
    for ln in moved:
        prev.lines.remove(ln)
    return moved[::-1]


def _example_number(raw: str, chapter: int) -> str:
    """'12.3' stays; OCR sometimes drops the dot ('123' -> '12.3') or makes it a comma."""
    raw = raw.replace(",", ".")
    ch = str(chapter)
    if "." not in raw and raw.startswith(ch) and len(raw) > len(ch):
        return f"{ch}.{raw[len(ch):]}"
    return raw


def _example_over(ln: Line, margin: float, layout: Layout) -> bool:
    """An in-text example is indented; running text is flush with the column margin."""
    if ln.x0 <= margin + 4 and len(ln.text) >= 3:
        return True
    if layout.size_reliable and len(ln.text) >= 12 and ln.size >= layout.body_size - 0.2:
        return True
    return False


# ───────────────────────────── cropping ──────────────────────────────────────

def _ink_rows(page, x0: float, x1: float, y0: float, y1: float) -> Optional[tuple[float, float]]:
    """(first, last) y of dark ink inside the rectangle, or None."""
    if y1 - y0 < 3 or x1 - x0 < 3:
        return None
    clip = fitz.Rect(x0, y0, x1, y1)
    pix = page.get_pixmap(clip=clip, dpi=100, colorspace=fitz.csGRAY)
    w, h, s = pix.width, pix.height, pix.samples
    ink = [sum(1 for v in s[r * w:(r + 1) * w] if v < 150) >= 3 for r in range(h)]
    runs = [i for i in range(h) if ink[i] and (i + 1 < h and ink[i + 1] or i > 0 and ink[i - 1])]
    if not runs:
        return None
    k = (y1 - y0) / h
    return y0 + runs[0] * k, y0 + (runs[-1] + 1) * k


def _col_x(page, layout: Layout, col: int) -> tuple[float, float]:
    w = page.rect.width
    pad = layout.left_m - 12
    return (max(0.0, pad), layout.right_m - 6) if col == 0 else (layout.right_m - 6, w - max(0.0, pad))


def piece_rects(doc, item: Item, scan: ChapterScan, layout: Layout) -> list[tuple[int, fitz.Rect]]:
    """Crop rectangles (page_index, rect) of an item, in reading order."""
    out = []
    for n, key in enumerate(scan.keys[id(item)]):
        pno, _band, col = key
        cell = scan.cells[key]
        mine = [l for l in cell.lines if l.owner is item]
        first, last = mine[0], mine[-1]
        page = doc[pno - 1]
        x0, x1 = _col_x(page, layout, col)
        top = first.y0 - 2
        if n > 0:                                 # continuation: a figure may sit above the text
            idx = cell.lines.index(first)
            prev_y = cell.lines[idx - 1].y1 if idx > 0 else cell.top
            ink = _ink_rows(page, x0, x1, prev_y + 1, first.y0 - 1)
            if ink:
                top = min(top, ink[0] - 2)
        bottom = last.y1 + 2
        idx = cell.lines.index(last)
        limit = max(cell.lines[idx + 1].y0, last.y1) if idx + 1 < len(cell.lines) else cell.bottom
        if limit - last.y1 > 4:
            ink = _ink_rows(page, x0, x1, last.y1 + 1, limit - 1)
            if ink:
                bottom = max(bottom, ink[1] + 2)
        bottom = min(bottom, max(limit, last.y1 + 2))
        out.append((pno - 1, fitz.Rect(x0, max(0.0, top), x1, min(page.rect.height, bottom))))
    return out


def render_item(doc, item: Item, scan: ChapterScan, layout: Layout, dpi: int = 170) -> Image.Image:
    """Crop every piece and stitch them into one left-aligned image."""
    imgs = []
    for pi, rect in piece_rects(doc, item, scan, layout):
        pix = doc[pi].get_pixmap(clip=rect, dpi=dpi, colorspace=fitz.csRGB)
        imgs.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
    gap = max(2, dpi // 25)
    width = max(i.width for i in imgs)
    canvas = Image.new("RGB", (width, sum(i.height for i in imgs) + gap * (len(imgs) - 1)), "white")
    y = 0
    for im in imgs:
        canvas.paste(im, (0, y))
        y += im.height + gap
    return canvas


# ───────────────────────────── book assembly ─────────────────────────────────

@dataclass
class ChapterSpec:
    number: int
    title: str
    page_start: int
    page_end: int


def ascii_text(s: str) -> str:
    s = (s.replace("\u2019", "'").replace("\u2018", "'").replace("\u2013", "-")
         .replace("\u2014", "-").replace("\u00b7", "|"))
    return unicodedata.normalize("NFKD", s).encode("latin-1", "replace").decode("latin-1")


def chapter_specs_from_db(db_path: Path, stem: str) -> list[ChapterSpec]:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5)
    try:
        row = con.execute("SELECT book_id FROM books WHERE filename=? OR title=? OR title=?",
                          (stem, stem, stem + ".pdf")).fetchone()
        if not row:
            raise SystemExit(f"book {stem!r} not found in {db_path}")
        rows = con.execute(
            "SELECT number, title, page_start, page_end FROM chapters WHERE book_id=? ORDER BY page_start",
            (row[0],)).fetchall()
    finally:
        con.close()
    specs = []
    for number, title, a, b in rows:
        t = re.sub(r"\s+", " ", title).strip()
        m = re.match(r"(?i)CHA\w{2,5}\s+(\d+)\s*[:\-]?\s*(.*)$", t)
        if m:
            number, t = int(m.group(1)), m.group(2).strip(" :")
        elif t in ("Front Matter", "Answers and Appendices") or re.match(r"(?i)(appendix|index)", t):
            continue
        elif number < 23 and "CHA" not in title.upper():
            continue
        if t.isupper():
            t = t.title()
        specs.append(ChapterSpec(number, t, a, b))
    return specs


def scan_book(doc, specs: list[ChapterSpec], layout: Layout) -> list[tuple[ChapterSpec, ChapterScan]]:
    out = []
    for sp in specs:
        pages = [read_page(doc[p - 1], p) for p in range(sp.page_start, min(sp.page_end, doc.page_count) + 1)]
        out.append((sp, scan_chapter(pages, layout, sp.number)))
    return out


W, H = 595.0, 842.0
MARGIN, GUTTER = 30.0, 14.0
COLW = (W - 2 * MARGIN - GUTTER) / 2
TOP, BOTTOM = 40.0, H - 36.0


def _sort_key(it: Item):
    try:
        return tuple(int(x) for x in it.number.split("."))
    except ValueError:
        return (0,)


class _Flow:
    """Two-column flow of images onto A4 pages."""

    def __init__(self, out):
        self.out = out
        self.page = None
        self.col = 0
        self.y = TOP
        self.y_start = TOP

    def new_page(self, heading: Optional[str] = None):
        self.page = self.out.new_page(width=W, height=H)
        self.col, self.y_start = 0, TOP
        if heading:
            self.page.insert_text((MARGIN, TOP + 12), ascii_text(heading), fontsize=14, fontname="hebo")
            self.page.draw_line((MARGIN, TOP + 20), (W - MARGIN, TOP + 20), width=0.8)
            self.y_start = TOP + 30
        self.y = self.y_start
        return self.page.number + 1

    def ensure(self, h: float) -> None:
        if self.y + h > BOTTOM and self.y > self.y_start:
            self.col += 1
            self.y = self.y_start
            if self.col > 1:
                self.new_page()

    @property
    def x(self) -> float:
        return MARGIN + self.col * (COLW + GUTTER)


def build_book_pdf(src_pdf: Path, out_pdf: Path, specs: list[ChapterSpec],
                   book_title: str, dpi: int = 170,
                   progress: Callable[[str], None] = print) -> dict:
    src = fitz.open(src_pdf)
    layout = detect_layout(src)
    progress(f"layout: left={layout.left_m:.0f} right={layout.right_m:.0f} "
             f"sizes_reliable={layout.size_reliable} body={layout.body_size}")
    scans = scan_book(src, specs, layout)

    # contents rows → reserve pages up front
    rows = 0
    for _sp, sc in scans:
        rows += 1 + len({it.kind for it in sc.items})
    toc_pages = max(1, -(-(rows + 8) // 58))

    out = fitz.open()
    for _ in range(toc_pages):
        out.new_page(width=W, height=H)
    flow = _Flow(out)
    toc: list[list] = []
    contents: list[tuple[int, str, int, int]] = []     # (level, text, page, count)
    totals = Counter()
    page_of: dict[int, int] = {}

    for sp, sc in scans:
        by_kind: dict[object, list[Item]] = {}
        for it in sc.items:
            by_kind.setdefault(it.kind, []).append(it)
        if not by_kind:
            progress(f"chapter {sp.number}: no questions found")
            continue
        n_items = len(sc.items)
        title = f"Chapter {sp.number}: {sp.title}"
        pg = flow.new_page(f"{title}   ({n_items} items)")
        toc.append([1, ascii_text(title), pg])
        contents.append((1, title, pg, n_items))
        for kind, _t, _s in CATEGORIES:
            group = sorted(by_kind.get(kind, []), key=_sort_key)
            if not group:
                continue
            totals[kind] += len(group)
            flow.ensure(16 + 90)
            bar = fitz.Rect(flow.x, flow.y, flow.x + COLW, flow.y + 14)
            flow.page.draw_rect(bar, color=None, fill=(0.88, 0.92, 0.98))
            flow.page.insert_text((bar.x0 + 4, bar.y0 + 10), ascii_text(f"{_CAT_TITLE[kind]} ({len(group)})"),
                                  fontsize=9, fontname="hebo", color=(0.1, 0.2, 0.45))
            flow.y += 18
            cat_page = flow.page.number + 1
            toc.append([2, ascii_text(f"{_CAT_TITLE[kind]} ({len(group)})"), cat_page])
            contents.append((2, f"{_CAT_TITLE[kind]}", cat_page, len(group)))
            for it in group:
                try:
                    img = render_item(src, it, sc, layout, dpi)
                except Exception as exc:                      # keep going; report below
                    progress(f"  ! ch{sp.number} {it.label}: {exc}")
                    continue
                nat_w, nat_h = img.width * 72 / dpi, img.height * 72 / dpi
                scale = min(COLW / nat_w, 1.15)
                avail = BOTTOM - flow.y_start - 14
                if nat_h * scale > avail:
                    scale = avail / nat_h
                w_pt, h_pt = nat_w * scale, nat_h * scale
                flow.ensure(12 + h_pt + 6)
                pages = (f"p.{it.first_page}" if it.first_page == it.last_page
                         else f"p.{it.first_page}-{it.last_page}")
                flow.page.insert_text((flow.x, flow.y + 8), ascii_text(f"Ch {sp.number} | {it.label} | PDF {pages}"),
                                      fontsize=7.5, fontname="helv", color=(0.35, 0.35, 0.4))
                buf = io.BytesIO()
                img.save(buf, "JPEG", quality=72, optimize=True)
                flow.page.insert_image(fitz.Rect(flow.x, flow.y + 11, flow.x + w_pt, flow.y + 11 + h_pt),
                                       stream=buf.getvalue())
                flow.y += 11 + h_pt + 7
        progress(f"chapter {sp.number} {sp.title}: "
                 + ", ".join(f"{_CAT_SHORT[k]}={len(v)}" for k, v in by_kind.items()))

    _write_contents(out, toc_pages, book_title, contents, totals, src_pdf.name)
    for i in range(toc_pages, out.page_count):
        out[i].insert_text((MARGIN, H - 18), ascii_text(f"{book_title} - questions"),
                           fontsize=7, fontname="helv", color=(0.5, 0.5, 0.5))
        out[i].insert_text((W - MARGIN - 20, H - 18), str(i + 1), fontsize=7, fontname="helv",
                           color=(0.5, 0.5, 0.5))
    out.set_toc(toc)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    out.save(out_pdf, garbage=3, deflate=True)
    progress(f"wrote {out_pdf} ({out.page_count} pages)")
    return {"pages": out.page_count, "totals": {k.value: v for k, v in totals.items()}}


def _write_contents(out, toc_pages: int, book_title: str, contents, totals, src_name: str) -> None:
    p = out[0]
    p.insert_text((MARGIN, 60), ascii_text(book_title), fontsize=20, fontname="hebo")
    p.insert_text((MARGIN, 80), "Question bank - cropped from the original pages", fontsize=10, fontname="helv")
    p.insert_text((MARGIN, 94), ascii_text(f"Source: {src_name}"), fontsize=8, fontname="helv", color=(0.4, 0.4, 0.4))
    summary = "   ".join(f"{_CAT_SHORT[k]}: {totals[k]}" for k, _t, _s in CATEGORIES if totals[k])
    p.insert_text((MARGIN, 110), ascii_text(summary), fontsize=8, fontname="helv")
    y, pi = 134.0, 0
    page = out[0]
    for level, text, pg, count in contents:
        if y > H - 40:
            pi += 1
            page, y = out[pi], 50.0
        x = MARGIN + (0 if level == 1 else 16)
        font = "hebo" if level == 1 else "helv"
        page.insert_text((x, y), ascii_text(f"{text}  ({count})"), fontsize=9 if level == 1 else 8.5, fontname=font)
        page.insert_text((W - MARGIN - 24, y), str(pg), fontsize=8.5, fontname="helv")
        page.insert_link({"kind": fitz.LINK_GOTO, "from": fitz.Rect(MARGIN, y - 9, W - MARGIN, y + 3),
                          "page": pg - 1, "to": fitz.Point(0, 0)})
        y += 12.5 if level == 1 else 11.5


# ───────────────────────────── CLI ───────────────────────────────────────────

def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pdf", required=True, type=Path)
    ap.add_argument("--db", type=Path, default=Path("storage/books.db"))
    ap.add_argument("--out", type=Path)
    ap.add_argument("--dpi", type=int, default=170)
    ap.add_argument("--chapters", help="comma separated chapter numbers (default: all)")
    args = ap.parse_args(argv)

    specs = chapter_specs_from_db(args.db, args.pdf.stem)
    if args.chapters:
        want = {int(x) for x in args.chapters.split(",")}
        specs = [s for s in specs if s.number in want]
    out = args.out or args.pdf.with_name(args.pdf.stem + "-questions.pdf")
    title = args.pdf.stem.replace("-", " ").title()
    build_book_pdf(args.pdf, out, specs, title, args.dpi, progress=lambda m: print(m, flush=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
