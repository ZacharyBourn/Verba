# Verba Data Files

This document describes the local data files Verba uses or is expected to use.

Exact file locations should be handled by:

```text
verba/storage/app_data.py
```

JSON loading and saving should be handled by:

```text
verba/storage/json_store.py
```

## General Rule

Do not hardcode data paths across the app.

Use the storage helpers instead.

Good pattern:

```python
self.path = get_data_file_path("stats.json")
self.stats = load_json(self.path, default={...})
```

## Expected Local JSON Files

Verba likely uses several local JSON files for app data:

```text
library.json
bookmarks.json
vocab.json
stats.json
session.json
settings.json
```

The exact location depends on `app_data.py`.

## `library.json`

Managed by:

```text
verba/library.py
```

Purpose:

Stores the user’s imported books.

Likely contents:

- Book ID
- Title
- Author
- File path
- File type
- Chapters or chapter references
- Import metadata

Be careful when changing this format. If book IDs change, bookmarks and sessions may break.

## `bookmarks.json`

Managed by:

```text
verba/bookmarks.py
```

Purpose:

Stores saved reading positions.

Likely contents:

- Book ID
- Chapter index
- Word index
- Bookmark label
- Date created, if supported

Bookmarks depend on book IDs and chapter/word indexes.

If the structure of books or chapters changes, test bookmarks carefully.

## `vocab.json`

Managed by:

```text
verba/vocab.py
```

Purpose:

Stores saved vocabulary words.

Likely contents:

- Word
- Book title or book ID
- Chapter title or chapter index
- Context, if supported
- Date added, if supported
- Definition, if supported later
- Notes, if supported later

Future fields can be added safely if old entries use defaults.

Example:

```python
definition = entry.get("definition", "")
```

## `stats.json`

Managed by:

```text
verba/stats.py
```

Purpose:

Stores reading statistics.

Likely contents:

```json
{
  "total_reading_seconds": 0,
  "total_words_read": 0,
  "session_count": 0,
  "books_opened": [],
  "books_finished": [],
  "last_read_date": "",
  "current_streak": 0,
  "longest_streak": 0
}
```

Stats should only be updated through `StatsManager`.

Avoid editing this file directly from UI code.

For a reset stats feature, add a method such as:

```python
def reset(self):
    self.stats = self.default_stats()
    self.save()
```

## `session.json`

Managed by:

```text
verba/session.py
```

Purpose:

Stores the user’s last reading position.

Likely contents:

- Last book ID
- Last chapter index
- Last word index
- Possibly last file path/title

Session restore is sensitive to changes in:

- Book IDs
- Chapter order
- Word indexes
- Library format

After editing session behavior, test closing and reopening the app.

## `settings.json`

Managed by:

```text
verba/settings.py
```

Purpose:

Stores user preferences.

Likely contents:

- Theme
- Font size
- WPM
- Chunk size
- Window preferences
- Focus/display preferences

When adding settings, include defaults so old settings files still load.

Example:

```python
theme = settings.get("theme", "dark")
```

## Backward Compatibility

When changing JSON formats, avoid assuming every field exists.

Use:

```python
value = data.get("field_name", default_value)
```

instead of:

```python
value = data["field_name"]
```

This helps old data continue working after updates.

## Data Safety

Before testing changes to data formats, commit first:

```bash
git add .
git commit -m "Working version before data format changes"
```

For extra safety, temporarily back up app data files before testing major changes.
