import re
import tkinter as tk
from tkinter import messagebox

from Verba_App.verba.reader import Reader


class OverviewView:
    """Embedded full-chapter overview view.

    This view gives the user a normal scrollable reading surface for the
    current chapter, plus zoom controls and a jump-back-to-reader action.
    It renders inside MainWindow's main container and does not create a
    popup/Toplevel window.
    """

    def __init__(self, app, parent):
        self.app = app
        self.parent = parent
        self.text = None
        self.zoom_size = max(14, min(28, int(self.app.settings.font_size * 0.55)))
        self.current_chapter_text = ""
        self.word_spans = []

    def clear(self):
        for widget in self.parent.winfo_children():
            widget.destroy()

        # Reset geometry configuration in case this view is rebuilt.
        for row in range(3):
            self.parent.grid_rowconfigure(row, weight=0)
        self.parent.grid_columnconfigure(0, weight=0)

    def render(self):
        self.clear()

        if not self.app.current_book:
            self._render_empty_state()
            return

        chapter = self.app.current_book.chapters[self.app.current_chapter_index]
        self.current_chapter_text = chapter.text or ""
        self.word_spans = self._build_word_spans(self.current_chapter_text)

        self.parent.grid_rowconfigure(0, weight=0)
        self.parent.grid_rowconfigure(1, weight=1)
        self.parent.grid_rowconfigure(2, weight=0)
        self.parent.grid_columnconfigure(0, weight=1)

        header = tk.Frame(self.parent, bg=self.app.bg_color)
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(18, 8))
        header.grid_columnconfigure(2, weight=1)

        tk.Button(
            header,
            text="← Reader",
            command=self.app.show_reader_view,
            width=12
        ).grid(row=0, column=0, sticky="w")

        tk.Button(
            header,
            text="Library",
            command=self.app.show_library_view,
            width=12
        ).grid(row=0, column=1, sticky="w", padx=(8, 0))

        title_frame = tk.Frame(header, bg=self.app.bg_color)
        title_frame.grid(row=0, column=2, sticky="ew", padx=24)

        tk.Label(
            title_frame,
            text="Chapter Overview",
            font=("Helvetica", 22, "bold"),
            bg=self.app.bg_color,
            fg=self.app.text_color,
            anchor="w"
        ).pack(anchor="w")

        tk.Label(
            title_frame,
            text=f"{self.app.current_book.title} — {chapter.title}",
            font=("Helvetica", 11),
            bg=self.app.bg_color,
            fg=self.app.subtle_text,
            anchor="w"
        ).pack(anchor="w")

        zoom_frame = tk.Frame(header, bg=self.app.bg_color)
        zoom_frame.grid(row=0, column=3, sticky="e")

        tk.Button(zoom_frame, text="A−", command=self.zoom_out, width=5).grid(row=0, column=0, padx=3)
        tk.Button(zoom_frame, text="A+", command=self.zoom_in, width=5).grid(row=0, column=1, padx=3)
        tk.Button(zoom_frame, text="Reset", command=self.reset_zoom, width=7).grid(row=0, column=2, padx=3)

        card = tk.Frame(
            self.parent,
            bg=self.app.panel_color,
            highlightbackground=self.app.border_color,
            highlightthickness=1
        )
        card.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 12))
        card.grid_rowconfigure(0, weight=1)
        card.grid_columnconfigure(0, weight=1)

        text_frame = tk.Frame(card, bg=self.app.panel_color)
        text_frame.grid(row=0, column=0, sticky="nsew", padx=14, pady=14)
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.text = tk.Text(
            text_frame,
            wrap="word",
            bg=self.app.text_box_bg,
            fg=self.app.text_color,
            insertbackground=self.app.text_color,
            selectbackground=self.app.sidebar_select,
            relief="flat",
            highlightthickness=0,
            borderwidth=0,
            padx=22,
            pady=18,
            font=(self.app.settings.font_family, self.zoom_size),
            yscrollcommand=scrollbar.set
        )
        self.text.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=self.text.yview)

        self.text.tag_configure(
            "current_position",
            background=self.app.sidebar_select,
            foreground=self.app.text_color
        )
        self.text.tag_configure(
            "current_line",
            background=self.app.sidebar_bg
        )

        self.text.insert("1.0", self.current_chapter_text)
        self.text.bind("<Key>", lambda event: "break")
        self.text.bind("<Double-Button-1>", self.jump_to_cursor)
        self.text.bind("<ButtonRelease-1>", self._move_insert_to_click)

        self._highlight_and_scroll_to_reader_position()

        footer = tk.Frame(self.parent, bg=self.app.bg_color)
        footer.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 16))
        footer.grid_columnconfigure(2, weight=1)

        tk.Button(
            footer,
            text="Previous Chapter",
            command=self.previous_chapter,
            width=16
        ).grid(row=0, column=0, sticky="w")

        tk.Button(
            footer,
            text="Next Chapter",
            command=self.next_chapter,
            width=16
        ).grid(row=0, column=1, sticky="w", padx=(8, 0))

        tk.Label(
            footer,
            text="Highlighted word = current reader position. Click elsewhere, then Jump Here.",
            font=("Helvetica", 10),
            bg=self.app.bg_color,
            fg=self.app.subtle_text
        ).grid(row=0, column=2, sticky="e", padx=(14, 14))

        tk.Button(
            footer,
            text="Save Selected Word",
            command=self.save_selected_word,
            width=18
        ).grid(row=0, column=3, sticky="e", padx=(0, 8))

        tk.Button(
            footer,
            text="Jump Here",
            command=self.jump_to_cursor,
            width=14
        ).grid(row=0, column=4, sticky="e")

    def _render_empty_state(self):
        self.parent.grid_rowconfigure(0, weight=0)
        self.parent.grid_rowconfigure(1, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)

        header = tk.Frame(self.parent, bg=self.app.bg_color)
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=(24, 12))

        tk.Button(
            header,
            text="← Library",
            command=self.app.show_library_view,
            width=12
        ).pack(side="left")

        body = tk.Frame(self.parent, bg=self.app.bg_color)
        body.grid(row=1, column=0, sticky="nsew")

        tk.Label(
            body,
            text="No book loaded.",
            font=("Helvetica", 20, "bold"),
            bg=self.app.bg_color,
            fg=self.app.text_color
        ).pack(pady=(120, 8))

        tk.Label(
            body,
            text="Open a book first, then return to Overview.",
            font=("Helvetica", 11),
            bg=self.app.bg_color,
            fg=self.app.subtle_text
        ).pack()

    def _build_word_spans(self, text):
        """Return character spans for visible words in the original chapter text."""
        return [(match.start(), match.end()) for match in re.finditer(r"\S+", text)]

    def _word_index_to_text_indexes(self, visible_word_number):
        if not self.text or not self.word_spans:
            return None, None

        safe_index = max(0, min(int(visible_word_number), len(self.word_spans) - 1))
        start_offset, end_offset = self.word_spans[safe_index]
        start = self.text.index(f"1.0 + {start_offset} chars")
        end = self.text.index(f"1.0 + {end_offset} chars")
        return start, end

    def _move_insert_to_click(self, event=None):
        if not self.text or event is None:
            return
        try:
            self.text.mark_set("insert", self.text.index(f"@{event.x},{event.y}"))
        except Exception:
            pass

    def _highlight_and_scroll_to_reader_position(self):
        if not self.text or not self.app.reader.has_text():
            return

        visible_before = self.app.reader.raw_index_to_visible_word_number(self.app.reader.get_index())
        start, end = self._word_index_to_text_indexes(visible_before)
        if not start or not end:
            self.text.see("1.0")
            return

        self.text.tag_remove("current_position", "1.0", tk.END)
        self.text.tag_remove("current_line", "1.0", tk.END)
        self.text.tag_add("current_position", start, end)

        try:
            line_start = self.text.index(f"{start} linestart")
            line_end = self.text.index(f"{start} lineend")
            self.text.tag_add("current_line", line_start, line_end)
            self.text.tag_lower("current_line", "current_position")
        except Exception:
            pass

        self.text.mark_set("insert", start)
        self.text.see(start)

        # Nudge the highlighted word a bit down from the very top when possible.
        self.text.after(50, lambda: self._center_current_position(start))

    def _center_current_position(self, start_index):
        if not self.text:
            return
        try:
            bbox = self.text.bbox(start_index)
            if bbox is None:
                self.text.see(start_index)
                return

            _, y, _, _ = bbox
            height = max(1, self.text.winfo_height())
            if y < height * 0.25:
                self.text.yview_scroll(-6, "units")
        except Exception:
            pass

    def _visible_words_before_index(self, text_index):
        if not self.text:
            return 0

        try:
            word_start = self.text.index(f"{text_index} wordstart")
            prefix = self.text.get("1.0", word_start)
        except Exception:
            return 0

        tokens = Reader()._tokenize_text(prefix)
        return len([word for word in tokens if word != Reader.PARAGRAPH_BREAK_TOKEN])

    def jump_to_cursor(self, event=None):
        if not self.text or not self.app.current_book:
            return "break"

        try:
            cursor_index = self.text.index("insert")
        except Exception:
            cursor_index = "1.0"

        visible_before = self._visible_words_before_index(cursor_index)
        raw_index = self.app.reader.visible_word_number_to_raw_index(visible_before)
        self.app.jump_to_reader_word_index(raw_index)
        return "break"

    def save_selected_word(self):
        if not self.text:
            return

        word = ""
        try:
            word = self.text.get(tk.SEL_FIRST, tk.SEL_LAST).strip()
        except Exception:
            try:
                cursor = self.text.index("insert")
                start = self.text.index(f"{cursor} wordstart")
                end = self.text.index(f"{cursor} wordend")
                word = self.text.get(start, end).strip()
            except Exception:
                word = ""

        word = word.strip(" \n\t\r.,;:!?\"'“”‘’()[]{}")
        if not word:
            messagebox.showinfo("No Selection", "Select or click a word to save.")
            return

        chapter = self.app.current_book.chapters[self.app.current_chapter_index]
        context = self._context_around_cursor()

        self.app.vocab_manager.add_entry(
            word=word,
            book_id=self.app.current_book.book_id,
            chapter_title=chapter.title,
            context=context
        )

        messagebox.showinfo("Saved", f"Saved to vocab:\n{word}")

    def _context_around_cursor(self):
        if not self.text:
            return ""

        try:
            cursor = self.text.index("insert")
            start = self.text.index(f"{cursor} - 120 chars")
            end = self.text.index(f"{cursor} + 120 chars")
            return self.text.get(start, end).replace("\n", " ").strip()
        except Exception:
            return ""

    def zoom_in(self):
        self.zoom_size = min(36, self.zoom_size + 2)
        self._apply_zoom()

    def zoom_out(self):
        self.zoom_size = max(10, self.zoom_size - 2)
        self._apply_zoom()

    def reset_zoom(self):
        self.zoom_size = max(14, min(28, int(self.app.settings.font_size * 0.55)))
        self._apply_zoom()

    def _apply_zoom(self):
        if self.text:
            self.text.config(font=(self.app.settings.font_family, self.zoom_size))
            self._highlight_and_scroll_to_reader_position()

    def previous_chapter(self):
        before = self.app.current_chapter_index
        self.app.previous_chapter()
        if self.app.current_chapter_index != before:
            self.render()

    def next_chapter(self):
        before = self.app.current_chapter_index
        self.app.next_chapter()
        if self.app.current_chapter_index != before:
            self.render()
