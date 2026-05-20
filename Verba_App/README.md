# Verba

Verba is a focused desktop reading app for TXT and EPUB books.

The goal of Verba is to make reading feel cleaner, less distracting, and easier to track. It currently supports importing books, reading in a focused word/chunk view, saving bookmarks, tracking reading stats, and saving vocabulary words.

## Current Features

- Import TXT and EPUB books
- Save imported books to a local library
- Read books in a focused chunk-based display
- Adjust WPM, chunk size, and font size
- Save and revisit bookmarks
- Save selected vocabulary words
- Track reading stats
- Restore the last reading session
- Use focus mode for a cleaner reading experience

## Running the App

From the repository root:

```bash
python Verba_App/main.py
```

Depending on your setup, you may need to run it from inside the `Verba_App` folder:

```bash
cd Verba_App
python main.py
```

## Project Structure

```text
Verba_App/
  main.py
  README.md
  TODO
  docs/
    ARCHITECTURE.md
    EDITING_GUIDE.md
    FEATURE_MAP.md
    DATA_FILES.md
    ROADMAP.md
  verba/
    storage/
    ui/
    bookmarks.py
    epub_parser.py
    library.py
    models.py
    reader.py
    session.py
    settings.py
    stats.py
    vocab.py
```

## Developer Documentation

For development notes, see:

- `docs/ARCHITECTURE.md`
- `docs/EDITING_GUIDE.md`
- `docs/FEATURE_MAP.md`
- `docs/DATA_FILES.md`
- `docs/ROADMAP.md`

## Development Philosophy

Verba should remain simple, readable, and easy to modify.

When adding a feature, try to keep responsibilities separated:

- UI behavior belongs in `verba/ui/`
- Reading movement/progress logic belongs in `reader.py`
- Saved data belongs in the correct manager file
- Shared objects belong in `models.py`
- JSON loading/saving should go through `storage/json_store.py`

## Roadmap

See `docs/ROADMAP.md`.
