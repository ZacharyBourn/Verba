
from Verba_App.verba.models import UserSettings
from Verba_App.verba.storage.app_data import get_data_file_path
from Verba_App.verba.storage.json_store import load_json, save_json


SETTINGS_FILE = "settings.json"


class SettingsManager:
    def __init__(self):
        self.path = get_data_file_path(SETTINGS_FILE)
        self.settings = self.load()

    def load(self) -> UserSettings:
        data = load_json(self.path, default={})
        return UserSettings(**data)

    def save(self):
        save_json(self.path, self.settings.to_dict())

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
        self.save()