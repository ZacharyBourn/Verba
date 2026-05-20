# Verba Editing Guide

This guide explains how to safely make changes to Verba without breaking unrelated features.

## Before Editing

Before making meaningful changes, commit the current working version:

```bash
git status
git add .
git commit -m "Working version before changes"
```

This makes it easy to undo a broken experiment.

## Use Branches for Features

For larger changes, create a feature branch:

```bash
git checkout -b feature/keyboard-shortcuts
```

After the feature works:

```bash
git add .
git commit -m "Add keyboard shortcuts"
git push
```

## If Something Breaks

To discard uncommitted changes:

```bash
git restore .
```

To return to the last commit and discard all uncommitted work:

```bash
git reset --hard HEAD
```

Use `git reset --hard HEAD` carefully. It permanently discards uncommitted changes.

## Where to Make Changes

### UI changes

Use:

```text
verba/ui/main_window.py
```

Examples:

- Add buttons
- Change layout
- Add keyboard shortcuts
- Open stats/vocab windows
- Show confirmation dialogs
- Change colors
- Change focus mode behavior

### Reading behavior

Use:

```text
verba/reader.py
```

Examples:

- Change how many words are shown
- Change forward/backward movement
- Change progress calculation
- Change reset behavior
- Change end-of-chapter behavior

### Saved book library

Use:

```text
verba/library.py
```

Examples:

- Add/remove books
- Prevent duplicate imports
- Change saved book metadata
- Change how the library file is loaded/saved

### Bookmarks

Use:

```text
verba/bookmarks.py
```

Examples:

- Add bookmark labels
- Change bookmark sorting
- Save more bookmark metadata
- Delete bookmarks

### Vocabulary

Use:

```text
verba/vocab.py
```

Examples:

- Save definitions
- Save word context
- Prevent duplicate words
- Add notes or known/unknown status

### Stats

Use:

```text
verba/stats.py
```

Examples:

- Reset stats
- Change streak behavior
- Change total reading time logic
- Track new stat fields

### Session restore

Use:

```text
verba/session.py
```

Examples:

- Restore last opened book
- Restore chapter index
- Restore word index
- Change startup behavior

### Settings

Use:

```text
verba/settings.py
```

Examples:

- Save theme
- Save font size
- Save WPM
- Save chunk size
- Add future user preferences

## Manual Test Checklist

Run this checklist after major edits.

### Startup

- App opens without errors.
- Welcome/intro behavior works.
- Library view appears.
- App does not crash if no book is loaded.

### Library

- Import TXT book.
- Import EPUB book.
- Select a book.
- Details panel updates.
- Open selected book.
- Remove selected book.

### Reader

- Book opens to reader view.
- Chapter list appears.
- Start begins reading.
- Pause stops reading.
- Reset returns to beginning.
- Back moves backward.
- Progress updates.
- WPM slider works.
- Chunk size slider works.
- Font size slider works.

### Chapters

- Previous chapter works.
- Next chapter works.
- Clicking a chapter jumps correctly.
- Current chapter indicator updates.

### Bookmarks

- Add bookmark.
- Bookmark appears.
- Open bookmark.
- Delete bookmark.

### Vocabulary

- Click/select displayed word.
- Save selected word.
- Open vocab list.
- Confirm saved word appears.

### Stats

- Start reading increases session count if intended.
- Reading time saves after pause.
- Words read count increases.
- Stats window opens.
- Streak behavior works.

### Session Restore

- Open a book.
- Move into the book.
- Close the app.
- Reopen the app.
- Last position restores correctly.

### Focus Mode

- Focus mode opens.
- Controls/sidebar hide as expected.
- Escape exits focus mode.
- Layout returns correctly.

## Risky Areas

### `main_window.py`

This file touches almost everything. Be extra careful when editing it.

Changes here may affect:

- Chapter loading
- Bookmarks
- Session restore
- Stats tracking
- Focus mode
- Vocab saving
- Reader progress

### JSON data structures

Changing saved JSON fields may break existing user data.

When adding fields, prefer defaults so old data still loads.

Example:

```python
entry.get("new_field", default_value)
```

### Stats

Do not manually edit `stats.json` from the UI.

Instead, add or update methods in `StatsManager`.

Example:

```python
self.stats_manager.reset()
```

### Session

Session restore depends on book IDs, chapter indexes, and word indexes. Be careful when changing book or chapter structures.

## Good Development Pattern

1. Make a small change.
2. Run the app.
3. Test the directly affected feature.
4. Test related features.
5. Commit once it works.

Avoid changing several major systems at once.
