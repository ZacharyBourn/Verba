# Verba Architecture

This document explains how Verba is organized and how the major parts of the app work together.

Verba is currently a desktop Python reading app built with Tkinter. It imports TXT and EPUB books, stores them in a local library, displays text in a focused reading view, saves bookmarks and vocabulary words, and tracks reading stats.

## High-Level App Flow

```text
main.py
  creates Tk root window
  creates MainWindow
  starts Tkinter mainloop

MainWindow
  builds the UI
  connects buttons and controls
  loads books through managers/parsers
  updates reader state
  updates session/bookmarks/stats/vocab

Managers
  handle saved app data
  load and save JSON files
  keep data behavior separate from the UI
```

## Main Entry Point

```text
Verba_App/main.py
```

This file should stay very small.

Its job is to:

1. Import Tkinter.
2. Import `MainWindow`.
3. Create the root window.
4. Create the app window.
5. Start `root.mainloop()`.

Avoid putting feature logic in `main.py`.

## Main UI Controller

```text
Verba_App/verba/ui/main_window.py
```

`main_window.py` is currently the center of the app. It builds the interface and coordinates the rest of the code.

It likely handles:

- Library screen
- Reader screen
- Intro/welcome sequence
- Importing TXT and EPUB files
- Opening selected books
- Removing books
- Opening pasted text
- Navigating chapters
- Starting, pausing, and resetting reading
- Saving session state
- Updating reading stats
- Managing focus mode
- Selecting displayed words
- Saving vocabulary words
- Displaying bookmarks
- Deleting bookmarks
- Opening stats and vocab windows

Because this file touches so many features, edit it carefully. A small change can affect several parts of the app.

## Core Modules

### `models.py`

Holds shared data structures used across the app.

Likely objects include:

- `Book`
- `Chapter`
- `Bookmark`

Use this file when multiple parts of the app need to agree on the structure of an object.

### `reader.py`

Contains reading engine logic.

This should handle:

- Loaded text
- Word list
- Current word index
- Chunk size
- Forward movement
- Backward movement
- Reset behavior
- Progress calculation
- End-of-text behavior

The UI should tell the reader what to do, but the reader should own the logic of moving through text.

### `epub_parser.py`

Handles EPUB parsing.

This should handle:

- Opening EPUB files
- Extracting title/author metadata
- Extracting chapter text
- Returning a usable book structure

The parser should not be responsible for saving the book to the library. It should parse and return data.

## Manager Modules

Verba uses manager-style files to keep storage and business logic separate from the UI.

### `library.py`

Responsible for the saved book library.

Likely responsibilities:

- Load library data
- Save library data
- Add books
- Remove books
- Return all books
- Find books by ID/path

### `bookmarks.py`

Responsible for bookmark data.

Likely responsibilities:

- Add bookmarks
- Delete bookmarks
- Get bookmarks for a book
- Save bookmark data

### `vocab.py`

Responsible for saved vocabulary words.

Likely responsibilities:

- Add vocabulary entries
- Save selected words
- Store book/chapter/context when available
- Return saved vocabulary entries

### `stats.py`

Responsible for reading statistics.

Likely responsibilities:

- Total reading time
- Total words read
- Session count
- Books opened
- Books finished
- Last read date
- Current streak
- Longest streak

Stats should be changed through `StatsManager`, not by manually editing raw JSON from the UI.

### `session.py`

Responsible for remembering the user’s last reading session.

Likely responsibilities:

- Last opened book
- Current chapter index
- Current word index
- Restore position on app launch

### `settings.py`

Responsible for user preferences.

Likely responsibilities:

- Theme
- Font size
- WPM
- Chunk size
- Window behavior
- Other persisted preferences

## Storage Helpers

```text
Verba_App/verba/storage/
```

### `app_data.py`

Decides where Verba stores local app data.

Other files should ask this helper for file paths instead of hardcoding locations.

### `json_store.py`

Provides generic JSON load/save helpers.

Managers should use this file instead of duplicating JSON logic.

## Design Rule

When adding or changing a feature, ask:

1. Is this UI behavior?
   - Put it in `verba/ui/`.

2. Is this reading movement or progress logic?
   - Put it in `reader.py`.

3. Is this saved data?
   - Put it in the correct manager file.

4. Is this a shared object?
   - Put it in `models.py`.

5. Is this JSON loading or saving?
   - Use `storage/json_store.py`.

Following this rule will keep Verba easier to maintain.
