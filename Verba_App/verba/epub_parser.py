from ebooklib import epub, ITEM_DOCUMENT
from html.parser import HTMLParser
from pathlib import Path
import re

from Verba_App.verba.models import Book, Chapter

def clean_book_title(title: str) -> str:
    """Clean known Project Gutenberg / EPUB titles without over-trimming real titles."""
    if not title:
        return "Unknown Title"

    title = " ".join(title.split()).strip()

    # Specific fix:
    # Gutenberg's Naval War of 1812 title metadata can be extremely long,
    # but the actual display title should be just this.
    if "naval war of 1812" in title.lower():
        return "The Naval War of 1812"

    return title

NUMBER_WORDS = (
    "one|two|three|four|five|six|seven|eight|nine|ten|"
    "eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|"
    "eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|"
    "eighty|ninety|hundred"
)
ROMAN_OR_NUMBER = rf"(?:[ivxlcdm]+|\d+|{NUMBER_WORDS})"
CHAPTER_HEADING_RE = re.compile(
    rf"^chapter\s+{ROMAN_OR_NUMBER}(?:[\.:]\s*.*)?$",
    re.IGNORECASE,
)
DIVIDER_RE = re.compile(
    rf"^(volume|book|part)\s+{ROMAN_OR_NUMBER}(?:[\.:]\s*.*)?$",
    re.IGNORECASE,
)


class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip_depth = 0
        self.block_tags = {
            "p", "div", "section", "article", "br",
            "h1", "h2", "h3", "h4", "h5", "h6",
            "li", "blockquote", "tr",
        }

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in {"head", "script", "style", "nav"}:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag in self.block_tags:
            self._add_block_break()

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in {"head", "script", "style", "nav"}:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.skip_depth:
            return
        if tag in self.block_tags:
            self._add_block_break()

    def handle_data(self, data):
        if self.skip_depth:
            return
        if not data:
            return

        compact = re.sub(r"\s+", " ", data)
        stripped = compact.strip()
        if not stripped:
            if self.parts and not self.parts[-1].endswith((" ", "\n")):
                self.parts.append(" ")
            return

        if data[:1].isspace() and self.parts and not self.parts[-1].endswith((" ", "\n")):
            self.parts.append(" ")

        self.parts.append(stripped)

        if data[-1:].isspace():
            self.parts.append(" ")

    def _add_block_break(self):
        if not self.parts:
            return
        last = self.parts[-1]
        if last == "\n\n":
            return
        if last == " ":
            self.parts[-1] = "\n\n"
        else:
            self.parts.append("\n\n")

    def get_text(self):
        text = "".join(self.parts)
        text = text.replace("\u00a0", " ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" *\n *", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def load_epub_book(file_path: str) -> Book:
    epub_book = epub.read_epub(file_path)

    title = _get_epub_title(epub_book)
    author = _get_epub_author(epub_book)

    text_blocks = _extract_spine_text_blocks(epub_book)
    chapters = _parse_chapters_from_spine(text_blocks)

    if not chapters:
        full_text = _build_clean_full_text(text_blocks)
        chapters = _split_full_text_into_chapters(full_text)

    if not chapters:
        chapters.append(Chapter(title="Chapter 1", text="", is_divider=False))

    book_id = Path(file_path).stem.lower().replace(" ", "_")

    return Book(
        book_id=book_id,
        title=clean_book_title(title),
        author=author,
        file_path=file_path,
        file_type="epub",
        chapters=chapters,
    )


def _get_epub_title(epub_book) -> str:
    title_meta = epub_book.get_metadata("DC", "title")
    if title_meta and title_meta[0][0]:
        return _clean_book_title(title_meta[0][0])
    return "Unknown Title"


def _get_epub_author(epub_book) -> str:
    author_meta = epub_book.get_metadata("DC", "creator")
    authors = []
    for value in author_meta:
        if value and value[0]:
            name = _clean_title(value[0])
            if name and name not in authors:
                authors.append(name)
    return ", ".join(authors) if authors else "Unknown"


def _extract_spine_text_blocks(epub_book) -> list[tuple[str, bytes, str, list[str]]]:
    item_map = {
        item.get_id(): item
        for item in epub_book.get_items()
        if item.get_type() == ITEM_DOCUMENT
    }

    blocks = []
    for spine_id, _ in epub_book.spine:
        item = item_map.get(spine_id)
        if not item:
            continue

        file_name = getattr(item, "file_name", "") or ""
        if _is_probable_navigation_or_cover_file(file_name):
            continue

        raw_content = item.get_content()
        text = _extract_clean_text(raw_content)
        if not text:
            continue

        if _is_gutenberg_header_or_license_file(file_name, text):
            continue

        headings = _extract_headings_from_html(raw_content)
        blocks.append((file_name, raw_content, text, headings))

    return blocks


def _parse_chapters_from_spine(text_blocks: list[tuple[str, bytes, str, list[str]]]) -> list[Chapter]:
    chapters = []
    started = False

    for file_name, raw_content, raw_text, headings in text_blocks:
        text = _strip_gutenberg_header_and_footer(raw_text)
        text = _clean_body_text(text)
        if not text:
            continue

        title = _best_title_for_block(file_name, text, headings)

        # Do not create selectable fake chapters like VOLUME ONE. They caused
        # confusing entries in the sidebar and could open as nonsense content.
        if _is_divider_title(title) and not _contains_chapter_heading(text):
            continue

        if not started:
            if _is_bad_front_matter(title, text, file_name):
                continue
            if not _is_chapter_like_title(title) and not _contains_chapter_heading(text) and _word_count(text) < 600:
                continue
            started = True

        title, body = _strip_leading_title_lines(title, text)

        if not title:
            title = f"Chapter {len(chapters) + 1}"

        if _is_bad_chapter(title, body):
            continue

        chapters.append(Chapter(title=title, text=body, is_divider=False))

    return chapters


def _best_title_for_block(file_name: str, text: str, headings: list[str]) -> str:
    for heading in headings:
        cleaned = _clean_title(heading)
        if _is_chapter_like_title(cleaned):
            return cleaned

    for heading in headings:
        cleaned = _clean_title(heading)
        if cleaned and not _is_divider_title(cleaned) and not _is_bad_title(cleaned):
            return cleaned

    for line in _nonempty_lines(text)[:4]:
        if _is_chapter_like_title(line):
            return _clean_title(line)

    first_line = _nonempty_lines(text)[0] if _nonempty_lines(text) else ""
    if first_line and len(first_line) <= 90 and not _is_bad_title(first_line):
        return _clean_title(first_line)

    return f"Chapter {_chapter_number_from_filename(file_name)}"


def _strip_leading_title_lines(title: str, text: str) -> tuple[str, str]:
    lines = _nonempty_lines(text)
    if not lines:
        return title, text

    cleaned_title = _clean_title(title)

    # Drop leading dividers and repeated chapter headings from the body.
    while lines and (
        _is_divider_title(lines[0])
        or _titles_match(lines[0], cleaned_title)
        or _is_chapter_like_title(lines[0])
    ):
        lines.pop(0)

    # If the file starts with "Chapter 1" and the next line is the subtitle,
    # combine those into the title. This also handles Gutenberg books that split
    # chapter number and title into separate tags/paragraphs.
    if _is_bare_chapter_heading(cleaned_title) and lines:
        possible_subtitle = _clean_title(lines[0])
        if _looks_like_subtitle(possible_subtitle):
            cleaned_title = f"{cleaned_title}. {possible_subtitle}"
            lines.pop(0)

    body = "\n\n".join(lines).strip()
    if not body:
        body = text.strip()

    return cleaned_title, body


def _extract_clean_text(html_content: bytes) -> str:
    parser = HTMLTextExtractor()
    parser.feed(html_content.decode("utf-8", errors="ignore"))
    return _clean_body_text(parser.get_text())


def _extract_headings_from_html(html_content: bytes) -> list[str]:
    html = html_content.decode("utf-8", errors="ignore")
    headings = []
    for match in re.finditer(r"<h([1-6])[^>]*>(.*?)</h\1>", html, re.IGNORECASE | re.DOTALL):
        heading = _strip_tags(match.group(2))
        if heading:
            headings.append(heading)
    return headings


def _strip_tags(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _build_clean_full_text(text_blocks: list[tuple[str, bytes, str, list[str]]]) -> str:
    full_text = "\n\n".join(text for _, _, text, _ in text_blocks)
    full_text = _strip_gutenberg_header_and_footer(full_text)
    full_text = _strip_front_matter_before_first_real_chapter(full_text)
    return _clean_body_text(full_text)


def _split_full_text_into_chapters(full_text: str) -> list[Chapter]:
    chapter_matches = _find_real_chapter_matches(full_text)
    if not chapter_matches:
        return []

    chapters = []
    for index, match in enumerate(chapter_matches):
        start = match.start()
        end = chapter_matches[index + 1].start() if index + 1 < len(chapter_matches) else len(full_text)
        section_text = full_text[start:end].strip()
        title, body = _extract_chapter_title_and_body(section_text)
        if not title:
            title = f"Chapter {len(chapters) + 1}"
        if body and not _is_bad_chapter(title, body):
            chapters.append(Chapter(title=title, text=body, is_divider=False))
    return chapters


def _find_real_chapter_matches(text: str) -> list[re.Match]:
    matches = list(re.finditer(rf"(?im)^\s*(chapter\s+{ROMAN_OR_NUMBER}(?:[\.:]\s*.*)?)$", text))
    return matches


def _extract_chapter_title_and_body(section_text: str) -> tuple[str, str]:
    lines = _nonempty_lines(section_text)
    if not lines:
        return "", ""
    title = _clean_title(lines[0])
    body_lines = lines[1:]
    if _is_bare_chapter_heading(title) and body_lines and _looks_like_subtitle(body_lines[0]):
        title = f"{title}. {_clean_title(body_lines[0])}"
        body_lines = body_lines[1:]
    return title, "\n\n".join(body_lines).strip()


def _strip_gutenberg_header_and_footer(text: str) -> str:
    cleaned = text
    start_patterns = [
        r"\*\*\*\s*START OF (?:THE )?PROJECT GUTENBERG EBOOK.*?\*\*\*",
        r"\*\*\*\s*START OF THIS PROJECT GUTENBERG EBOOK.*?\*\*\*",
    ]
    for pattern in start_patterns:
        match = re.search(pattern, cleaned, re.IGNORECASE | re.DOTALL)
        if match:
            cleaned = cleaned[match.end():]
            break

    end_patterns = [
        r"\*\*\*\s*END OF (?:THE )?PROJECT GUTENBERG EBOOK.*",
        r"\*\*\*\s*END OF THIS PROJECT GUTENBERG EBOOK.*",
        r"End of (?:the )?Project Gutenberg.*",
        r"THE FULL PROJECT GUTENBERG LICENSE.*",
    ]
    for pattern in end_patterns:
        match = re.search(pattern, cleaned, re.IGNORECASE | re.DOTALL)
        if match:
            cleaned = cleaned[:match.start()]
            break
    return cleaned.strip()


def _strip_front_matter_before_first_real_chapter(text: str) -> str:
    matches = _find_real_chapter_matches(text)
    if not matches:
        return text
    return text[matches[0].start():].strip()


def _is_probable_navigation_or_cover_file(file_name: str) -> bool:
    lowered = file_name.lower()
    markers = ["toc", "nav", "navigation", "cover", "titlepage", "wrap"]
    return any(marker in lowered for marker in markers)


def _is_gutenberg_header_or_license_file(file_name: str, text: str) -> bool:
    sample = text[:2500].lower()
    lowered = file_name.lower()
    if "pg-header" in lowered:
        return True
    if "end of the project gutenberg ebook" in sample:
        return True
    if "the full project gutenberg license" in sample:
        return True
    if "this ebook is for the use of anyone anywhere" in sample and "*** start of" in sample:
        return True
    return False


def _is_bad_front_matter(title: str, text: str, file_name: str) -> bool:
    t = _clean_title(title).lower()
    f = file_name.lower()
    sample = text[:800].lower()
    if _is_bad_title(t):
        return True
    if any(marker in f for marker in ["contents", "copyright", "titlepage", "cover"]):
        return True
    if t in {"dedication", "preface", "foreword", "introduction", "illustrations"}:
        return True
    if "table of contents" in sample or sample.count("chapter") >= 8:
        return True
    return False


def _is_bad_chapter(title: str, body: str) -> bool:
    combined = f"{title}\n{body}".lower()
    bad_markers = [
        "project gutenberg",
        "gutenberg ebook",
        "this ebook is for the use of anyone anywhere",
        "terms of the project gutenberg license",
        "gutenberg literary archive foundation",
        "www.gutenberg.org",
        "produced by",
        "distributed proofreaders",
    ]
    if any(marker in combined for marker in bad_markers):
        return True
    if _is_bad_title(title):
        return True
    if _word_count(body) < 60:
        return True
    return False


def _is_bad_title(title: str) -> bool:
    t = _clean_title(title).lower()
    bad_titles = {
        "contents", "table of contents", "illustrations", "acknowledgments",
        "acknowledgements", "preface", "preface to third edition",
        "principal authorities referred to", "authorities referred to",
        "appendix", "index", "license", "the full project gutenberg license",
        "the full project gutenberg™ license",
    }
    return t in bad_titles or "project gutenberg" in t


def _is_chapter_like_title(title: str) -> bool:
    return bool(CHAPTER_HEADING_RE.match(_clean_title(title)))


def _is_bare_chapter_heading(title: str) -> bool:
    return bool(re.match(rf"(?i)^chapter\s+{ROMAN_OR_NUMBER}[\.:]?$", _clean_title(title)))


def _contains_chapter_heading(text: str) -> bool:
    return any(_is_chapter_like_title(line) for line in _nonempty_lines(text)[:6])


def _is_divider_title(title: str) -> bool:
    return bool(DIVIDER_RE.match(_clean_title(title)))


def _looks_like_subtitle(value: str) -> bool:
    value = _clean_title(value)
    if not value or len(value) > 90:
        return False
    if _is_chapter_like_title(value) or _is_bad_title(value) or _is_divider_title(value):
        return False
    if len(value.split()) > 12:
        return False
    # Avoid treating normal opening prose as a subtitle.
    if value.endswith((".", "!", "?", ",", ";", ":")):
        return False
    return True


def _titles_match(a: str, b: str) -> bool:
    def normalize(value: str) -> str:
        value = _clean_title(value).lower()
        value = value.replace(" — ", "—").replace(" – ", "–")
        value = re.sub(r"\s+", " ", value)
        return value.strip()

    return normalize(a) == normalize(b)


def _clean_book_title(title: str) -> str:
    title = _clean_title(title)
    word_count = len(title.split())
    if len(title) > 85 or word_count > 14:
        for separator in [" / or ", "/ or ", "; or,", ": or,"]:
            if separator in title.lower():
                return title.split(separator, 1)[0].strip()
        if ";" in title:
            return title.split(";", 1)[0].strip()
    return title or "Unknown Title"


def _clean_title(title: str) -> str:
    title = str(title).replace("\u00a0", " ")
    title = re.sub(r"\s+", " ", title)
    return title.strip()


def _clean_body_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("—", " — ").replace("–", " – ").replace("―", " ― ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    paragraphs = re.split(r"\n\s*\n+", text)
    cleaned_paragraphs = []
    for paragraph in paragraphs:
        cleaned = _clean_paragraph(paragraph)
        if cleaned:
            cleaned_paragraphs.append(cleaned)
    return "\n\n".join(cleaned_paragraphs).strip()


def _clean_paragraph(paragraph: str) -> str:
    lines = [line.strip() for line in paragraph.splitlines() if line.strip()]
    if not lines:
        return ""
    joined = " ".join(lines)
    joined = re.sub(r"\s+", " ", joined)
    return joined.strip()


def _nonempty_lines(text: str) -> list[str]:
    paragraphs = re.split(r"\n\s*\n+", text)
    return [_clean_paragraph(paragraph) for paragraph in paragraphs if _clean_paragraph(paragraph)]


def _word_count(text: str) -> int:
    text = text.replace("—", " ").replace("–", " ").replace("―", " ")
    return len(re.findall(r"\b[\w'-]+\b", text))


def _chapter_number_from_filename(file_name: str) -> str:
    match = re.search(r"(?:-|_)(\d+)(?:\.|$)", file_name)
    if match:
        return str(int(match.group(1)))
    return "1"
