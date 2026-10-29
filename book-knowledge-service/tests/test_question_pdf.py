"""Tests for app/question_pdf.py – layout-based question cropping."""

import pymupdf as fitz

from app.models import QuestionType
from app.question_pdf import (
    ChapterSpec, Layout, build_book_pdf, decode_text, detect_layout,
    read_page, render_item, scan_chapter, _example_number,
)

W, H = 600, 800
LEFT, RIGHT = 40, 320


def _put(page, x, y, text, size=10):
    page.insert_text((x, y), text, fontsize=size, fontname="helv")


def _synthetic() -> fitz.Document:
    """Two pages of a chapter: an in-text example, a section header mid-page,
    numbered questions in both columns and one question that runs onto page 2."""
    doc = fitz.open()
    p1 = doc.new_page(width=W, height=H)
    _put(p1, 260, 20, "Running head")
    _put(p1, LEFT, 100, "Example 3.1")
    _put(p1, LEFT + 18, 114, "A body of mass 2 kg is pushed.")
    _put(p1, LEFT + 10, 128, "Solution : The force is 4 N.")
    _put(p1, LEFT, 160, "Plain running text of the chapter continues here.")
    _put(p1, 250, 300, "EXERCISES")
    _put(p1, LEFT, 340, "1. First exercise line")
    _put(p1, LEFT + 14, 352, "second line of the first exercise")
    _put(p1, LEFT, 380, "2. Second exercise line")
    _put(p1, RIGHT, 340, "3. Third exercise in the right column")
    _put(p1, RIGHT + 14, 352, "continues on the next page")
    p1.draw_rect(fitz.Rect(RIGHT + 14, 362, RIGHT + 100, 420), color=(0, 0, 0), fill=(0, 0, 0))
    p2 = doc.new_page(width=W, height=H)
    _put(p2, LEFT, 80, "and finishes at the top of page two")
    _put(p2, LEFT, 120, "4. Fourth exercise")
    _put(p2, 250, 300, "ANSWERS")
    _put(p2, LEFT, 340, "1. (a)  2. (b)")
    return doc


def _scan(doc):
    layout = Layout(left_m=LEFT, right_m=RIGHT)
    pages = [read_page(doc[i], i + 1) for i in range(doc.page_count)]
    return layout, scan_chapter(pages, layout, 3)


def test_scan_finds_items_by_category_and_number():
    _layout, sc = _scan(_synthetic())
    got = [(i.kind, i.number) for i in sc.items]
    assert got == [
        (QuestionType.example, "3.1"),
        (QuestionType.exercise, "1"),
        (QuestionType.exercise, "2"),
        (QuestionType.exercise, "3"),
        (QuestionType.exercise, "4"),
    ]


def test_running_head_and_answer_grid_are_excluded():
    _layout, sc = _scan(_synthetic())
    texts = " ".join(l.text for i in sc.items for l in i.lines)
    assert "Running head" not in texts
    assert "(a)" not in texts


def test_item_spanning_a_page_break_has_two_pieces():
    doc = _synthetic()
    layout, sc = _scan(doc)
    third = next(i for i in sc.items if i.number == "3")
    assert third.first_page == 1 and third.last_page == 2
    assert len(sc.keys[id(third)]) == 2


def test_example_stops_at_following_plain_text():
    _layout, sc = _scan(_synthetic())
    ex = sc.items[0]
    assert all("Plain running text" not in l.text for l in ex.lines)


def test_render_stitches_pieces_and_keeps_figure_ink():
    doc = _synthetic()
    layout, sc = _scan(doc)
    third = next(i for i in sc.items if i.number == "3")
    single = next(i for i in sc.items if i.number == "2")
    img = render_item(doc, third, sc, layout, dpi=100)
    one = render_item(doc, single, sc, layout, dpi=100)
    assert img.height > one.height * 2          # two text pieces + black figure box
    dark = img.convert("L").point(lambda v: 255 if v < 40 else 0).getbbox()
    assert dark is not None and (dark[2] - dark[0]) * (dark[3] - dark[1]) > 500   # filled rectangle cropped in


def test_decode_garbled_text_and_ocr_example_numbers():
    assert decode_text("2%-(&7,9(\x03 ,") == "OBJECTIVE I"
    assert decode_text("Plain text") == "Plain text"
    assert _example_number("123", 12) == "12.3"
    assert _example_number("12.3", 12) == "12.3"
    assert _example_number("12,3", 12) == "12.3"


def test_section_header_detected_even_when_garbled():
    doc = fitz.open()
    page = doc.new_page(width=W, height=H)
    _put(page, 250, 100, "EXERCISES")
    pd = read_page(page, 1)
    assert pd.lines[0].hdr == QuestionType.exercise


def test_build_book_pdf_writes_indexed_pdf(tmp_path):
    src = tmp_path / "book.pdf"
    _synthetic().save(src)
    out = tmp_path / "book-questions.pdf"
    spec = ChapterSpec(3, "Forces", 1, 2)
    result = build_book_pdf(src, out, [spec], "Test Book", dpi=80, progress=lambda m: None)
    assert result["totals"]["exercise"] == 4 and result["totals"]["example"] == 1
    book = fitz.open(out)
    toc = book.get_toc()
    assert toc[0][1].startswith("Chapter 3: Forces")
    assert [t[1] for t in toc[1:]] == ["Examples (in-text) (1)", "Exercises (4)"]
    assert "Ch 3 | Exercise 3" in book[1].get_text()
