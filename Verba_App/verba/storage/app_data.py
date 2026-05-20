
from pathlib import Path
import os


APP_FOLDER_NAME = "Verba"


def get_app_data_dir() -> Path:
    appdata = os.getenv("APPDATA")

    if appdata:
        base_path = Path(appdata)
    else:
        base_path = Path.home() / ".config"

    app_dir = base_path / APP_FOLDER_NAME
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_data_file_path(filename: str) -> Path:
    return get_app_data_dir() / filename