# Verba Feature Map

This document maps user-facing features to the files that control them.

Use this when deciding where to make a change.

## App Startup

Primary file:

```text
main.py
```

Related file:

```text
verba/ui/main_window.py
```

Use this area for:

- Starting the Tkinter app
- Creating the main window
- Launching the event loop

Keep `main.py` small.

## Library View

Primary files:

```text
verba/ui/main_window.py
verba/library.py
verba/models.py
```

Related files:

```text
verba/epub_parser.py
verba/storage/json_store.py
verba/storage/app_data.py
```

Use this area for:

- Displaying saved books
- Importing books
- Removing books
- Selecting books
- Showing book details

## TXT Import

Primary files:

```text
verba/ui/main_window.py
verba/library.py
verba/models.py
```

Use this area for:

- Importing plain text files
- Creating a book object from TXT content
- Adding the imported book to the saved library

## EPUB Import

Primary files:

```text
verba/ui/main_window.py
verba/epub_parser.py
verba/library.py
verba/models.py
```

Use this area for:

- Parsing EPUB metadata
- Extracting chapters
- Creating book/chapter objects
- Adding EPUB books to the library

## Reader Display

Primary files:

```text
verba/ui/main_window.py
verba/reader.py
```

Related files:

```text
verba/session.py
verba/stats.py
```

Use this area for:

- Showing the current text chunk
- Starting reading
- Pausing reading
- Resetting reading
- Moving backward
- Updating progress
- Changing WPM
- Changing chunk size
- Changing font size

## Chapter Navigation

Primary files:

```text
verba/ui/main_window.py
verba/reader.py
verba/session.py
```

Use this area for:

- Previous chapter
- Next chapter
- Chapter list selection
- Restoring chapter position
- Updating current chapter label

## Bookmarks

Primary files:

```text
verba/ui/main_window.py
verba/bookmarks.py
verba/models.py
```

Related file:

```text
verba/session.py
```

Use this area for:

- Adding bookmarks
- Displaying bookmarks
- Opening bookmarks
- Deleting bookmarks
- Saving bookmark position

## Vocabulary

Primary files:

```text
verba/ui/main_window.py
verba/vocab.py
```

Related files:

```text
verba/models.py
verba/storage/json_store.py
```

Use this area for:

- Selecting a displayed word
- Saving a selected word
- Viewing the vocab list
- Later adding definitions, notes, or context

## Stats

Primary files:

```text
verba/ui/main_window.py
verba/stats.py
```

Related file:

```text
verba/storage/json_store.py
```

Use this area for:

- Total reading time
- Total words read
- Session count
- Books opened
- Books finished
- Reading streaks
- Reset stats button

## Session Restore

Primary files:

```text
verba/session.py
verba/ui/main_window.py
```

Related files:

```text
verba/library.py
verba/reader.py
```

Use this area for:

- Remembering last book
- Remembering chapter index
- Remembering word index
- Reopening the last reading position

## Settings

Primary files:

```text
verba/settings.py
verba/ui/main_window.py
```

Use this area for:

- Theme
- Font size
- WPM
- Chunk size
- Window/user preferences

## Focus Mode

Primary file:

```text
verba/ui/main_window.py
```

Use this area for:

- Entering fullscreen/focus mode
- Hiding sidebars/controls
- Exiting focus mode
- Restoring normal layout

## Keyboard Shortcuts

Primary file:

```text
verba/ui/main_window.py
```

Possible related file:

```text
verba/reader.py
```

Use this area for:

- Space = Play/Pause
- Left arrow = Back 5 words
- Right arrow = Forward

Recommended approach:

- Bind keys in `MainWindow`.
- Add a clean `toggle_play_pause()` method.
- Reuse existing start/pause/back behavior.
- Add reader support only if needed.

## Reset Stats Button

Primary files:

```text
verba/stats.py
verba/ui/main_window.py
```

Recommended approach:

1. Add `reset()` method to `StatsManager`.
2. Add button in stats window.
3. Confirm before resetting.
4. Call `self.stats_manager.reset()`.
5. Refresh stats display.

## Zoomed-Out Book View

Primary file at first:

```text
verba/ui/main_window.py
```

Possible future file:

```text
verba/ui/book_view_window.py
```

Recommended stages:

1. Add read-only scrollable chapter view.
2. Add click-to-save-word behavior.
3. Add click-to-jump-to-word behavior.
4. Expand from current chapter to whole-book view.

## Themes

Primary files:

```text
verba/settings.py
verba/ui/main_window.py
```

Possible future file:

```text
verba/ui/themes.py
```

Recommended approach:

- Store theme name in settings.
- Keep color palettes centralized.
- Avoid scattering color values throughout the UI.

## Future Phone Integration

Do not start this too early.

Before mobile/sync work, Verba should have:

- Stable data models
- Stable JSON formats
- Better separation between UI and core logic
- Import/export support
- Clear documentation
