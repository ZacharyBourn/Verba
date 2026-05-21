from ebooklib import epub, ITEM_DOCUMENT
from html.parser import HTMLParser
from pathlib import Path
import re

from Verba_App.verba.models import Book, Chapter


NUMBER_WORDS = "one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve"
ROMAN_OR_NUMBER = rf"(?:[ivxlcdm]+|\d+|{NUMBER_WORDS})"


class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip_depth = 0
        self.block_tags = {
            "p", "div", "section", "article", "br",
            "h1", "h2", "h3", "h4", "h5", "h6",
            "li", "blockquote"
        }

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()

        if tag in {"head", "script", "style", "nav"}:
            self.skip_depth += 1
            return

        if self.skip_depth:
            return

        if tag in self.block_tags and self.parts and self.parts[-1] != "\n\n":
            self.parts.append("\n\n")

    def handle_endtag(self, tag):
        tag = tag.lower()

        if tag in {"head", "script", "style", "nav"}:
            self.skip_depth = max(0, self.skip_depth - 1)
            return

        if self.skip_depth:
            return

        if tag in self.block_tags and self.parts and self.parts[-1] != "\n\n":
            self.parts.append("\n\n")

    def handle_data(self, data):
        if self.skip_depth:
            return

        text = data.strip()
        if text:
            self.parts.append(text)

    def get_text(self):
        text = "".join(self.parts)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def _extract_clean_text(html_content: bytes) -> str:
    parser = HTMLTextExtractor()
    parser.feed(html_content.decode("utf-8", errors="ignore"))
    return parser.get_text().strip()


def _clean_title(title: str) -> str:
    return re.sub(r"\s+", " ", title).strip()


def _strip_tags(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _extract_headings_from_html(html_content: bytes) -> list[str]:
    html = html_content.decode("utf-8", errors="ignore")
    headings = []

    for match in re.finditer(r"<h([1-6])[^>]*>(.*?)</h\1>", html, re.IGNORECASE | re.DOTALL):
        heading = _strip_tags(match.group(2))
        if heading:
            headings.append(heading)

    return headings


def _extract_title_from_html(html_content: bytes) -> str:
    headings = _extract_headings_from_html(html_content)

    # Prefer true chapters over dividers like PART I or VOLUME ONE.
    for heading in headings:
        if _is_chapter_like_title(heading):
            return heading

    for heading in headings:
        if not _is_volume_or_divider_title(heading):
            return heading

    if headings:
        return headings[0]

    html = html_content.decode("utf-8", errors="ignore")
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)

    if title_match:
        return _strip_tags(title_match.group(1))

    return ""


def _opening_snippet(text: str, limit: int = 220) -> str:
    return text[:limit].strip().lower()


def _looks_like_toc(title: str, text: str, file_name: str) -> bool:
    title_l = title.lower()
    file_l = file_name.lower()
    snippet = _opening_snippet(text, 1200)

    if "table of contents" in title_l:
        return True

    if title_l == "contents":
        return True

    if "toc" in file_l or "contents" in file_l:
        return True

    dotted_lines = len(re.findall(r"\.{3,}", snippet))
    if dotted_lines >= 3 and len(text) < 5000:
        return True

    chapter_hits = snippet.count("chapter")
    if chapter_hits >= 5 and len(text) < 5000:
        return True

    return False


def _looks_like_front_matter(title: str, text: str, file_name: str) -> bool:
    title_l = title.lower().strip()
    file_l = file_name.lower()
    snippet = _opening_snippet(text, 500)

    title_markers = {
        "copyright",
        "title page",
        "dedication",
        "about the author",
        "acknowledgments",
        "acknowledgements",
        "foreword",
        "introduction",
        "half title",
        "also by",
        "illustrations",
        "credits",
        "epigraph",
    }

    file_markers = {
        "copyright",
        "titlepage",
        "cover",
        "dedication",
        "preface",
        "foreword",
        "introduction",
        "epigraph",
    }

    snippet_markers = {
        "all rights reserved",
        "published by",
        "isbn",
    }

    if title_l in title_markers:
        return True

    if "preface" in title_l:
        return True

    if any(marker in file_l for marker in file_markers):
        return True

    if any(marker in snippet for marker in snippet_markers):
        return True

    return False


def _looks_like_back_matter(title: str, text: str, file_name: str) -> bool:
    title_l = title.lower().strip()
    file_l = file_name.lower()
    snippet = _opening_snippet(text, 500)

    title_markers = {
        "appendix",
        "notes",
        "endnotes",
        "glossary",
        "bibliography",
        "discussion questions",
        "reading group guide",
        "about this ebook",
        "license",
        "colophon",
        "footnotes",
        "footnotes:",
        "the full project gutenberg™ license",
        "the full project gutenberg license",
    }

    file_markers = {
        "appendix",
        "endnotes",
        "glossary",
        "bibliography",
        "license",
        "colophon",
    }

    if title_l in title_markers:
        return True

    if "project gutenberg" in title_l and "license" in title_l:
        return True

    if "footnote" in title_l:
        return True

    if "end of the project gutenberg ebook" in snippet:
        return True

    if any(marker in file_l for marker in file_markers):
        return True

    return False


def _looks_like_gutenberg_header(title: str, text: str) -> bool:
    title_l = title.lower().strip()
    snippet = _opening_snippet(text, 700)

    return (
        "project gutenberg" in title_l
        and "this ebook is for the use of anyone anywhere" in snippet
    )


def _is_probable_navigation_file(file_name: str) -> bool:
    lowered = file_name.lower()
    nav_markers = [
        "toc",
        "contents",
        "nav",
        "navigation",
        "copyright",
        "titlepage",
        "cover",
    ]
    return any(marker in lowered for marker in nav_markers)


def _looks_like_book_title_page(book_title: str, title: str, text: str) -> bool:
    bt = book_title.strip().lower()
    tt = title.strip().lower()
    sample = _opening_snippet(text, 250)

    if not bt:
        return False

    if tt == bt and len(text) < 2500:
        return True

    if bt in sample and len(text) < 2500:
        return True

    return False


def _is_volume_or_divider_title(title: str) -> bool:
    t = title.strip().lower()
    if not t:
        return False

    return bool(
        re.match(rf"^volume\s+{ROMAN_OR_NUMBER}(?:[\.:].*)?$", t) or
        re.match(rf"^book\s+{ROMAN_OR_NUMBER}(?:[\.:].*)?$", t) or
        re.match(rf"^part\s+{ROMAN_OR_NUMBER}(?:[\.:].*)?$", t) or
        t == "epilogue"
    )


def _is_book_or_part_title(title: str) -> bool:
    return _is_volume_or_divider_title(title)


def _is_chapter_like_title(title: str) -> bool:
    t = title.strip().lower()
    if not t:
        return False

    return bool(
        re.match(r"^chapter\s+\d+(?:[\.:].*)?$", t) or
        re.match(r"^chapter\s+[ivxlcdm]+(?:[\.:].*)?$", t) or
        re.match(r"^chapter\s+[a-z0-9].*", t)
    )


def _is_simple_roman_heading(title: str) -> bool:
    return bool(re.match(r"^[ivxlcdm]+$", title.strip().lower()))


def _fallback_title_from_filename(file_name: str, chapter_number: int, raw_text: str) -> str:
    first_line = raw_text.split("\n")[0].strip()
    if first_line and len(first_line) <= 80:
        return _clean_title(first_line)

    return f"Chapter {chapter_number}"


def _is_book_divider_file(file_name: str) -> bool:
    return bool(re.search(r"(^|/|\\)ch\d+\.xhtml?$", file_name.lower()))


def _is_section_file(file_name: str) -> bool:
    return bool(re.search(r"(^|/|\\)ch\d+s\d+\.xhtml?$", file_name.lower()))


def _append_divider(chapters: list[Chapter], title: str):
    title = _clean_title(title)
    if not title:
        return

    if chapters and chapters[-1].title == title and getattr(chapters[-1], "is_divider", False):
        return

    chapters.append(
        Chapter(
            title=title,
            text=title,
            is_divider=True
        )
    )


def _extract_leading_dividers(headings: list[str], actual_heading: str = "") -> list[str]:
    dividers = []

    for heading in headings:
        if actual_heading and heading == actual_heading:
            break

        if _is_chapter_like_title(heading):
            break

        if _is_volume_or_divider_title(heading):
            dividers.append(heading)

    return dividers


def _split_text_at_simple_roman_headings(raw_text: str, roman_headings: list[str]) -> list[tuple[str, str]]:
    """Split an Epilogue-style file into sections such as I and II."""
    if not roman_headings:
        return []

    matches = []
    for heading in roman_headings:
        pattern = rf"(?m)^\s*{re.escape(heading)}\s*$"
        match = re.search(pattern, raw_text)
        if match:
            matches.append((heading, match.start(), match.end()))

    matches.sort(key=lambda item: item[1])

    sections = []
    for index, (heading, start, end) in enumerate(matches):
        next_start = matches[index + 1][1] if index + 1 < len(matches) else len(raw_text)
        section_text = raw_text[start:next_start].strip()
        if section_text:
            sections.append((heading, section_text))

    return sections


def load_epub_book(file_path: str) -> Book:
    epub_book = epub.read_epub(file_path)

    title = "Unknown Title"
    author = "Unknown"

    title_meta = epub_book.get_metadata("DC", "title")
    if title_meta:
        title = title_meta[0][0]

    author_meta = epub_book.get_metadata("DC", "creator")
    if author_meta:
        author = author_meta[0][0]

    item_map = {
        item.get_id(): item
        for item in epub_book.get_items()
        if item.get_type() == ITEM_DOCUMENT
    }

    chapters = []
    visible_chapter_number = 1
    found_first_real_content = False

    for spine_id, _ in epub_book.spine:
        item = item_map.get(spine_id)
        if not item:
            continue

        file_name = getattr(item, "file_name", "") or ""
        raw_content = item.get_content()
        raw_text = _extract_clean_text(raw_content)
        headings = _extract_headings_from_html(raw_content)
        item_title = _clean_title(_extract_title_from_html(raw_content))

        if not raw_text:
            continue

        text_len = len(raw_text.strip())

        if _looks_like_gutenberg_header(item_title, raw_text):
            continue

        if _looks_like_toc(item_title, raw_text, file_name):
            continue

        if _looks_like_front_matter(item_title, raw_text, file_name):
            continue

        if _looks_like_book_title_page(title, item_title, raw_text):
            continue

        if _is_probable_navigation_file(file_name) and not _is_book_divider_file(file_name) and not _is_section_file(file_name):
            continue

        if _looks_like_back_matter(item_title, raw_text, file_name):
            continue

        is_book_divider = _is_book_divider_file(file_name)
        is_section = _is_section_file(file_name)

        actual_heading = next((heading for heading in headings if _is_chapter_like_title(heading)), "")

        # Handle Epilogue files that contain roman sub-sections, such as:
        # EPILOGUE / I / II. These should become two real readable chapters,
        # with EPILOGUE shown as a divider.
        has_epilogue_divider = any(heading.strip().lower() == "epilogue" for heading in headings)
        roman_headings = [
            heading for heading in headings
            if _is_simple_roman_heading(heading)
        ]

        if has_epilogue_divider and roman_headings and not actual_heading:
            _append_divider(chapters, "EPILOGUE")
            for roman_title, section_text in _split_text_at_simple_roman_headings(raw_text, roman_headings):
                chapters.append(
                    Chapter(
                        title=f"Epilogue {roman_title}",
                        text=section_text,
                        is_divider=False
                    )
                )
                visible_chapter_number += 1
            found_first_real_content = True
            continue

        for divider_title in _extract_leading_dividers(headings, actual_heading):
            _append_divider(chapters, divider_title)

        if text_len < 300 and not actual_heading:
            # Keep pure divider files, but do not count them as chapters.
            if any(_is_volume_or_divider_title(heading) for heading in headings):
                found_first_real_content = True
            continue

        if not found_first_real_content:
            if is_book_divider or is_section or _is_book_or_part_title(item_title) or _is_chapter_like_title(item_title):
                found_first_real_content = True
            elif text_len < 2500:
                continue

        title_to_use = actual_heading or item_title

        if not title_to_use or len(title_to_use) > 100 or _is_volume_or_divider_title(title_to_use):
            title_to_use = _fallback_title_from_filename(file_name, visible_chapter_number, raw_text)

        if _is_volume_or_divider_title(title_to_use) and not actual_heading:
            _append_divider(chapters, title_to_use)
            found_first_real_content = True
            continue

        chapters.append(
            Chapter(
                title=title_to_use,
                text=raw_text,
                is_divider=False
            )
        )
        visible_chapter_number += 1
        found_first_real_content = True

    if not chapters:
        chapters.append(Chapter(title="Chapter 1", text="", is_divider=False))

    book_id = Path(file_path).stem.lower().replace(" ", "_")

    return Book(
        book_id=book_id,
        title=title,
        author=author,
        file_path=file_path,
        file_type="epub",
        chapters=chapters
    )
