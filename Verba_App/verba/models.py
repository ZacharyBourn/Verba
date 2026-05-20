
from dataclasses import dataclass, asdict, field
from typing import Optional, List


@dataclass
class UserSettings:
    theme: str = "dark"
    font_size: int = 34
    font_family: str = "Helvetica"
    default_wpm: int = 240
    default_chunk_size: int = 1
    punctuation_slowdown: bool = True
    window_width: int = 1000
    window_height: int = 750

    def to_dict(self):
        return asdict(self)


@dataclass
class ReadingSession:
    current_book_id: Optional[str] = None
    current_chapter_index: int = 0
    current_word_index: int = 0
    last_opened_file: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class Bookmark:
    book_id: str
    chapter_index: int
    word_index: int
    label: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class Chapter:
    title: str
    text: str

    def to_dict(self):
        return asdict(self)


@dataclass
class Book:
    book_id: str
    title: str
    author: str = "Unknown"
    file_path: str = ""
    file_type: str = "txt"
    chapters: List[Chapter] = field(default_factory=list)

    def to_dict(self):
        return {
            "book_id": self.book_id,
            "title": self.title,
            "author": self.author,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "chapters": [chapter.to_dict() for chapter in self.chapters],
        }

    @classmethod
    def from_dict(cls, data: dict):
        chapters = [Chapter(**chapter) for chapter in data.get("chapters", [])]
        return cls(
            book_id=data["book_id"],
            title=data["title"],
            author=data.get("author", "Unknown"),
            file_path=data.get("file_path", ""),
            file_type=data.get("file_type", "txt"),
            chapters=chapters,
        )