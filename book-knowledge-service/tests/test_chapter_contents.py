"""tests/test_chapter_contents.py – chapters taken from a printed Table of Contents
when the PDF has no bookmarks."""

from app.chapter_parser import detect_chapters, parse_chapters_from_contents
from app.pdf_processor import ExtractedPage, PDFMeta

CONTENTS = (
    "Table of Contents\nChapters 1–22\nVolume–1\nChapter 23\nHeat and Temperature\n1\n"
    "23.1 Hot and Cold Bodies\n1\n23.2 Zeroth Law\n1\n23.3 Scales\n3\n"
    "Worked Out Examples\n7\nChapter 24\nKinetic Theory of Gases\n15\n24.1 Introduction\n15\n"
)
CONTENTS_2 = (
    "24.2 Assumptions\n16\n24.3 Pressure\n17\n24.4 Speed\n18\n"
    "Chapter 25\nCalorimetry\n39\n25.1 Heat\n39\n25.2 Specific heat\n40\n"
    "Chapter 26\nLaws of\nThermodynamics\n49\n26.1 First law\n49\n"
)
# 'CHAPTER 25' as it comes out of a PDF with a shifted font: every glyph +29 lower
SHIFTED_25 = " \x03&+$37(5\x03 \x15\x18\nCALORIMETRY\n" + "x" * 50


def _book():
    texts = ["Title page", CONTENTS, CONTENTS_2,
             "CHAPTER 23\nHEAT AND TEMPERATURE\nbody", "more heat text",
             "CHAPTER 24\nKINETIC THEORY\nbody", "more gas text",
             SHIFTED_25, "more calorimetry",
             "CHAPTER 26\nLAWS OF THERMODYNAMICS\nbody", "first law text",
             "ANSWERS\nOBJECTIVE I\n1. (d)"]
    return [ExtractedPage(i + 1, t, False, False, False) for i, t in enumerate(texts)]


def test_chapters_follow_the_printed_contents():
    ch = parse_chapters_from_contents("b", _book())
    assert [(c.number, c.page_start, c.page_end) for c in ch] == [
        (23, 4, 5), (24, 6, 7), (25, 8, 9), (26, 10, 11), (27, 12, 12)]
    assert [c.title for c in ch[:4]] == [
        "Heat and Temperature", "Kinetic Theory of Gases", "Calorimetry", "Laws of Thermodynamics"]
    assert ch[-1].title == "Answers and Appendices"
    assert {c.source for c in ch} == {"contents"}


def test_detect_chapters_prefers_contents_over_text_guessing_and_adds_front_matter():
    meta = PDFMeta(title="", author="", total_pages=12, toc=[])
    ch = detect_chapters("b", meta, _book())
    assert ch[0].number == 0 and ch[0].page_end == 3          # front matter before chapter 23
    assert all(c.source != "inferred" for c in ch[1:])


def test_chapters_are_numbered_0_1_2_even_when_the_book_starts_at_23():
    """Volume 2 of a series prints chapters 23, 24, ... - the app numbers them 1, 2, ..."""
    meta = PDFMeta(title="", author="", total_pages=12, toc=[])
    ch = detect_chapters("b", meta, _book())
    assert [c.number for c in ch] == list(range(len(ch)))                  # 0, 1, 2, 3, ...
    assert [c.printed_number for c in ch[1:5]] == [23, 24, 25, 26]          # kept for reference
    assert ch[0].printed_number is None                                     # front matter
    assert [c.chapter_id for c in ch[1:3]] == ["b_ch023", "b_ch024"]        # ids unchanged


def test_text_inferred_chapters_are_also_numbered_from_1():
    pages = [ExtractedPage(i + 1, t, False, False, False) for i, t in enumerate([
        "cover", "Chapter 7: Waves and Sound\nbody", "more", "Chapter 8: Light and Optics\nbody", "more"])]
    ch = detect_chapters("b", PDFMeta(title="", author="", total_pages=5, toc=[]), pages)
    assert [(c.number, c.printed_number) for c in ch] == [(0, None), (1, 7), (2, 8)]


def test_no_contents_page_returns_nothing():
    pages = [ExtractedPage(i, f"plain text {i}", False, False, False) for i in range(1, 6)]
    assert parse_chapters_from_contents("b", pages) == []
