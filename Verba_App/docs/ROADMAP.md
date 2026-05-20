# Verba Roadmap

This roadmap organizes future Verba ideas into practical development stages.

## Current Priority

The current priority is to make Verba easier to maintain and edit.

Before adding major features, add:

- Documentation
- Clear README
- Feature map
- Manual testing checklist
- Cleaner TODO/roadmap

## Stage 1: Immediate Polish

These are small improvements that should make the app feel better quickly.

### Keyboard Controls

Add:

- Space = Play/Pause
- Left arrow = Back 5 words
- Right arrow = Forward

Likely files:

```text
verba/ui/main_window.py
verba/reader.py
```

### Reset Stats Button

Add a reset button to the stats window.

Requirements:

- Confirm before resetting
- Reset all stats to defaults
- Refresh stats display after reset

Likely files:

```text
verba/stats.py
verba/ui/main_window.py
```

### README and Docs

Add:

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/EDITING_GUIDE.md`
- `docs/FEATURE_MAP.md`
- `docs/DATA_FILES.md`
- `docs/ROADMAP.md`

## Stage 2: Reading Experience Improvements

These features improve the actual reading experience.

### Zoomed-Out Chapter View

Add a scrollable view of the current chapter.

First version:

- Opens in a new window
- Displays full current chapter
- Read-only text
- No jumping yet

Later versions:

- Click a word to save it to vocab
- Click a word to jump reader position
- Expand from chapter view to whole-book view

Likely files:

```text
verba/ui/main_window.py
```

Possible future file:

```text
verba/ui/book_view_window.py
```

### Better Word Interaction

Improve selected-word behavior.

Ideas:

- Single-click selects word
- Double-click saves word
- Show selected word more clearly
- Save nearby context

Likely files:

```text
verba/ui/main_window.py
verba/vocab.py
```

## Stage 3: Appearance and Themes

Status: Started for V1.

Implemented themes:

- Dark
- Light
- Sepia
- Forest
- Gray

Themes are centralized in:

```text
verba/ui/themes.py
```

The current V1 theme selector saves the selected theme and applies it after restarting Verba. Future polish could make theme switching fully live without a restart.

## Stage 4: Vocab Expansion

Turn saved vocab into a stronger feature.

Ideas:

- Save word context
- Add definitions
- Add notes
- Mark word as known/learning
- Sort/filter vocab
- Export vocab list

Likely files:

```text
verba/vocab.py
verba/ui/main_window.py
```

Possible future file:

```text
verba/ui/vocab_window.py
```

## Stage 5: Stats Expansion

Improve reading stats.

Ideas:

- Reset stats button
- Daily reading time
- Weekly reading time
- Books completed
- Average WPM
- Reading streak calendar
- Words read by book

Likely files:

```text
verba/stats.py
verba/ui/main_window.py
```

Possible future file:

```text
verba/ui/stats_window.py
```

## Stage 6: Refactor UI

Do not rush this. Refactor only once the current app starts becoming hard to change.

Possible future structure:

```text
verba/ui/
  main_window.py
  library_view.py
  reader_view.py
  stats_window.py
  vocab_window.py
  themes.py
```

Recommended order:

1. Add documentation first.
2. Add small features.
3. Notice repeated patterns.
4. Split UI when it becomes clearly useful.

Do not refactor just for neatness.

## Stage 7: Mobile or Sync Planning

Phone integration should wait until the desktop data model is stable.

Before starting phone/mobile work, Verba should have:

- Stable JSON formats
- Clear models
- Import/export support
- Good docs
- Reduced dependence on `main_window.py`
- Clean separation between core logic and UI

Possible future paths:

1. Keep desktop app and add export/import.
2. Build a separate mobile version later.
3. Add a sync layer only after data format is stable.

## Development Philosophy

Build Verba in small, safe steps.

Good pattern:

1. Commit working version.
2. Add one feature.
3. Test related features.
4. Commit again.

Avoid adding several large features at the same time.
