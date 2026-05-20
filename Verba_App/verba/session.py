
from Verba_App.verba.models import ReadingSession
from Verba_App.verba.storage.app_data import get_data_file_path
from Verba_App.verba.storage.json_store import load_json, save_json


SESSION_FILE = "session.json"


class SessionManager:
    def __init__(self):
        self.path = get_data_file_path(SESSION_FILE)
        self.session = self.load()

    def load(self) -> ReadingSession:
        data = load_json(self.path, default={})
        return ReadingSession(**data)

    def save(self):
        save_json(self.path, self.session.to_dict())

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self.session, key):
                setattr(self.session, key, value)
        self.save()

    def clear(self):
        self.session = ReadingSession()
        self.save()