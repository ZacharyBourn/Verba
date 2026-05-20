
from typing import List, Dict
from Verba_App.verba.storage.app_data import get_data_file_path
from Verba_App.verba.storage.json_store import load_json, save_json


VOCAB_FILE = "vocab.json"


class VocabManager:
    def __init__(self):
        self.path = get_data_file_path(VOCAB_FILE)
        self.entries = self.load()

    def load(self) -> List[Dict]:
        return load_json(self.path, default=[])

    def save(self):
        save_json(self.path, self.entries)

    def add_entry(self, word: str, book_id: str = "", chapter_title: str = "", context: str = ""):
        word = word.strip()
        if not word:
            return

        entry = {
            "word": word,
            "book_id": book_id,
            "chapter_title": chapter_title,
            "context": context
        }

        self.entries.append(entry)
        self.save()

    def all_entries(self) -> List[Dict]:
        return self.entries

    def remove_entry(self, index: int):
        if 0 <= index < len(self.entries):
            self.entries.pop(index)
            self.save()