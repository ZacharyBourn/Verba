from datetime import datetime, date
from Verba_App.verba.storage.app_data import get_data_file_path
from Verba_App.verba.storage.json_store import load_json, save_json


STATS_FILE = "stats.json"


class StatsManager:
    def __init__(self):
        self.path = get_data_file_path(STATS_FILE)
        self.stats = self.load()

    def load(self):
        return load_json(
            self.path,
            default={
                "total_reading_seconds": 0,
                "total_words_read": 0,
                "session_count": 0,
                "books_opened": [],
                "books_finished": [],
                "last_read_date": "",
                "current_streak": 0,
                "longest_streak": 0,
            }
        )

    def save(self):
        save_json(self.path, self.stats)

    def start_session(self):
        self.stats["session_count"] += 1
        self._update_streak()
        self.save()

    def add_reading_time(self, seconds: int):
        self.stats["total_reading_seconds"] += max(0, int(seconds))
        self.save()

    def add_words(self, count: int):
        self.stats["total_words_read"] += max(0, int(count))
        self.save()

    def mark_book_opened(self, book_id: str):
        if book_id and book_id not in self.stats["books_opened"]:
            self.stats["books_opened"].append(book_id)
            self.save()

    def mark_book_finished(self, book_id: str):
        if book_id and book_id not in self.stats["books_finished"]:
            self.stats["books_finished"].append(book_id)
            self.save()

    def _update_streak(self):
        today = date.today()
        last_str = self.stats.get("last_read_date", "")

        if last_str:
            last_date = datetime.strptime(last_str, "%Y-%m-%d").date()
            diff = (today - last_date).days

            if diff == 1:
                self.stats["current_streak"] += 1
            elif diff == 0:
                pass
            else:
                self.stats["current_streak"] = 1
        else:
            self.stats["current_streak"] = 1

        self.stats["last_read_date"] = today.strftime("%Y-%m-%d")

        if self.stats["current_streak"] > self.stats["longest_streak"]:
            self.stats["longest_streak"] = self.stats["current_streak"]

    def get_stats_summary(self):
        total_seconds = int(self.stats["total_reading_seconds"])
        total_minutes = total_seconds // 60
        hours = total_minutes // 60
        minutes = total_minutes % 60

        return {
            "hours": hours,
            "minutes": minutes,
            "words": self.stats["total_words_read"],
            "sessions": self.stats["session_count"],
            "books_opened": len(self.stats["books_opened"]),
            "books_finished": len(self.stats["books_finished"]),
            "streak": self.stats["current_streak"],
            "best_streak": self.stats["longest_streak"],
        }