
from ebooklib import epub, ITEM_DOCUMENT
from html.parser import HTMLParser
from pathlib import Path
import re

from Verba_App.verba.models import Book, Chapter


class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.block_tags = {
            "p", "div", "section", "article", "br",
            "h1", "h2", "h3", "h4", "h5", "h6",
            "li", "blockquote"
        }

    def handle_starttag(self, tag, attrs):
        if tag in self.block_tags and self.parts and self.parts[-1] != "\n\n":
            self.parts.append("\n\n")

    def handle_endtag(self, tag):
        if tag in self.block_tags and self.parts and self.parts[-1] != "\n\n":
            self.parts.append("\n\n")

    def handle_data(self, data):
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


def _extract_title_from_html(html_content: bytes) -> str:
    html = html_content.decode("utf-8", errors="ignore")

    heading_patterns = [
        r"<h1[^>]*>(.*?)</h1>",
        r"<h2[^>]*>(.*?)</h2>",
        r"<title[^>]*>(.*?)</title>",
    ]

    for pattern in heading_patterns:
        match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        if match:
            raw = re.sub(r"<[^>]+>", "", match.group(1)).strip()
            raw = re.sub(r"\s+", " ", raw)
            if raw:
                return raw

    return ""


def _clean_title(title: str) -> str:
    return re.sub(r"\s+", " ", title).strip()


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
    snippet = _opening_snippet(text, 180)

    title_markers = {
        "copyright",
        "volume",
        "-volume",
        "title page",
        "dedication",
        "about the author",
        "acknowledgments",
        "acknowledgements",
        "preface",
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

    if any(marker in file_l for marker in file_markers):
        return True

    if any(marker in snippet for marker in snippet_markers):
        return True

    return False


def _looks_like_back_matter(title: str, text: str, file_name: str) -> bool:
    title_l = title.lower().strip()
    file_l = file_name.lower()

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

    if any(marker in file_l for marker in file_markers):
        return True

    return False


def _is_probable_navigation_file(file_name: str) -> bool:
    lowered = file_name.lower()
    nav_markers = [
        "toc",
        "volume",
        "-volume",
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


def _is_book_or_part_title(title: str) -> bool:
    t = title.strip().lower()
    return bool(
        re.match(r"^book\s+[ivxlcdm\d]+$", t) or
        re.match(r"^part\s+[ivxlcdm\d]+$", t)
    )


def _is_chapter_like_title(title: str) -> bool:
    t = title.strip().lower()
    if not t:
        return False

    patterns = [
        r"^chapter\s+\d+$",
        r"^chapter\s+[ivxlcdm]+$",
        r"^chapter\s+[a-z0-9].*",
    ]

    return any(re.search(pattern, t) for pattern in patterns)


def _fallback_title_from_filename(file_name: str, chapter_number: int, raw_text: str) -> str:
    lowered = file_name.lower()

    if re.search(r"(^|/|\\)ch\d+\.xhtml?$", lowered):
        first_line = raw_text.split("\n")[0].strip()
        if first_line:
            cleaned = _clean_title(first_line)
            if _is_book_or_part_title(cleaned):
                return cleaned

    if re.search(r"(^|/|\\)ch\d+s\d+\.xhtml?$", lowered):
        return f"Chapter {chapter_number}"

    first_line = raw_text.split("\n")[0].strip()
    if first_line and len(first_line) <= 60:
        return first_line

    return f"Chapter {chapter_number}"


def _is_book_divider_file(file_name: str) -> bool:
    return bool(re.search(r"(^|/|\\)ch\d+\.xhtml?$", file_name.lower()))


def _is_section_file(file_name: str) -> bool:
    return bool(re.search(r"(^|/|\\)ch\d+s\d+\.xhtml?$", file_name.lower()))


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
        item_title = _clean_title(_extract_title_from_html(raw_content))

        if not raw_text:
            continue

        text_len = len(raw_text.strip())

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

        if text_len < 300 and not is_book_divider and not is_section:
            continue

        if not found_first_real_content:
            if is_book_divider or is_section or _is_book_or_part_title(item_title) or _is_chapter_like_title(item_title):
                found_first_real_content = True
            elif text_len < 2500:
                continue

        title_to_use = item_title
        if not title_to_use or len(title_to_use) > 80:
            title_to_use = _fallback_title_from_filename(file_name, visible_chapter_number, raw_text)

        if is_book_divider or _is_book_or_part_title(title_to_use):
            if not _is_book_or_part_title(title_to_use):
                first_line = raw_text.split("\n")[0].strip()
                cleaned = _clean_title(first_line)
                if _is_book_or_part_title(cleaned):
                    title_to_use = cleaned

            chapters.append(
                Chapter(
                    title=title_to_use,
                    text=raw_text
                )
            )
            continue

        if is_section and (not item_title or len(item_title) > 80 or _is_book_or_part_title(item_title)):
            title_to_use = f"Chapter {visible_chapter_number}"
        elif not title_to_use:
            title_to_use = f"Chapter {visible_chapter_number}"

        chapters.append(
            Chapter(
                title=title_to_use,
                text=raw_text
            )
        )
        visible_chapter_number += 1

    if not chapters:
        chapters.append(Chapter(title="Chapter 1", text=""))

    book_id = Path(file_path).stem.lower().replace(" ", "_")

    return Book(
        book_id=book_id,
        title=title,
        author=author,
        file_path=file_path,
        file_type="epub",
        chapters=chapters
    )