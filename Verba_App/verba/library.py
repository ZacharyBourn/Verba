
from typing import List, Optional
from Verba_App.verba.models import Book
from Verba_App.verba.storage.app_data import get_data_file_path
from Verba_App.verba.storage.json_store import load_json, save_json


LIBRARY_FILE = "library.json"


class LibraryManager:
    def __init__(self):
        self.path = get_data_file_path(LIBRARY_FILE)
        self.books = self.load()

    def load(self) -> List[Book]:
        data = load_json(self.path, default=[])
        return [Book.from_dict(item) for item in data]

    def save(self):
        save_json(self.path, [book.to_dict() for book in self.books])

    def reload(self):
        self.books = self.load()

    def add_book(self, book: Book):
        existing = self.get_book(book.book_id)
        if existing is None:
            self.books.append(book)
            self.save()

    def get_book(self, book_id: str) -> Optional[Book]:
        return next((book for book in self.books if book.book_id == book_id), None)

    def get_book_by_path(self, file_path: str) -> Optional[Book]:
        return next((book for book in self.books if book.file_path == file_path), None)

    def all_books(self) -> List[Book]:
        return self.books

    def remove_book(self, book_id: str):
        self.books = [book for book in self.books if book.book_id != book_id]
        self.save()