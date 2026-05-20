
from typing import List, Tuple
from Verba_App.verba.models import Bookmark
from Verba_App.verba.storage.app_data import get_data_file_path
from Verba_App.verba.storage.json_store import load_json, save_json


BOOKMARKS_FILE = "bookmarks.json"


class BookmarkManager:
    def __init__(self):
        self.path = get_data_file_path(BOOKMARKS_FILE)
        self.bookmarks = self.load()

    def load(self) -> List[Bookmark]:
        data = load_json(self.path, default=[])
        return [Bookmark(**item) for item in data]

    def save(self):
        save_json(self.path, [bookmark.to_dict() for bookmark in self.bookmarks])

    def add_bookmark(self, bookmark: Bookmark):
        self.bookmarks.append(bookmark)
        self.save()

    def get_bookmarks_for_book(self, book_id: str) -> List[Tuple[int, Bookmark]]:
        return [
            (index, bookmark)
            for index, bookmark in enumerate(self.bookmarks)
            if bookmark.book_id == book_id
        ]

    def remove_bookmark(self, index: int):
        if 0 <= index < len(self.bookmarks):
            self.bookmarks.pop(index)
            self.save()