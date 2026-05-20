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

    def clear(self):
        for widget in self.parent.winfo_children():
            widget.destroy()

    def render(self):
        self.clear()

        if not self.app.current_book:
            self._render_empty_state()
            return

        chapter = self.app.current_book.chapters[self.app.current_chapter_index]
        self.current_chapter_text = chapter.text or ""

        header = tk.Frame(self.parent, bg=self.app.bg_color)
        header.pack(fill="x", padx=24, pady=(18, 8))

        tk.Button(
            header,
            text="← Reader",
            command=self.app.show_reader_view,
            width=12
        ).pack(side="left")

        tk.Button(
            header,
            text="Library",
            command=self.app.show_library_view,
            width=12
        ).pack(side="left", padx=(8, 0))

        title_frame = tk.Frame(header, bg=self.app.bg_color)
        title_frame.pack(side="left", padx=24, fill="x", expand=True)

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
        zoom_frame.pack(side="right")

        tk.Button(zoom_frame, text="A−", command=self.zoom_out, width=5).grid(row=0, column=0, padx=3)
        tk.Button(zoom_frame, text="A+", command=self.zoom_in, width=5).grid(row=0, column=1, padx=3)
        tk.Button(zoom_frame, text="Reset", command=self.reset_zoom, width=7).grid(row=0, column=2, padx=3)

        card = tk.Frame(
            self.parent,
            bg=self.app.panel_color,
            highlightbackground=self.app.border_color,
            highlightthickness=1
        )
        card.pack(fill="both", expand=True, padx=24, pady=(0, 12))

        text_frame = tk.Frame(card, bg=self.app.panel_color)
        text_frame.pack(fill="both", expand=True, padx=14, pady=14)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

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
        self.text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.text.yview)

        self.text.insert("1.0", self.current_chapter_text)
        self.text.bind("<Key>", lambda event: "break")
        self.text.bind("<Double-Button-1>", self.jump_to_cursor)
        self.text.bind("<ButtonRelease-1>", self._move_insert_to_click)

        self._scroll_near_reader_position()

        footer = tk.Frame(self.parent, bg=self.app.bg_color)
        footer.pack(fill="x", padx=24, pady=(0, 16))

        tk.Button(
            footer,
            text="Previous Chapter",
            command=self.previous_chapter,
            width=16
        ).pack(side="left")

        tk.Button(
            footer,
            text="Next Chapter",
            command=self.next_chapter,
            width=16
        ).pack(side="left", padx=(8, 0))

        tk.Button(
            footer,
            text="Jump Here",
            command=self.jump_to_cursor,
            width=14
        ).pack(side="right")

        tk.Button(
            footer,
            text="Save Selected Word",
            command=self.save_selected_word,
            width=18
        ).pack(side="right", padx=(0, 8))

        tk.Label(
            footer,
            text="Tip: click in the chapter, then use Jump Here. Double-click also jumps.",
            font=("Helvetica", 10),
            bg=self.app.bg_color,
            fg=self.app.subtle_text
        ).pack(side="right", padx=(0, 14))

    def _render_empty_state(self):
        header = tk.Frame(self.parent, bg=self.app.bg_color)
        header.pack(fill="x", padx=30, pady=(24, 12))

        tk.Button(
            header,
            text="← Library",
            command=self.app.show_library_view,
            width=12
        ).pack(side="left")

        tk.Label(
            self.parent,
            text="No book loaded.",
            font=("Helvetica", 20, "bold"),
            bg=self.app.bg_color,
            fg=self.app.text_color
        ).pack(pady=(120, 8))

        tk.Label(
            self.parent,
            text="Open a book first, then return to Overview.",
            font=("Helvetica", 11),
            bg=self.app.bg_color,
            fg=self.app.subtle_text
        ).pack()

    def _move_insert_to_click(self, event=None):
        if not self.text or event is None:
            return
        try:
            self.text.mark_set("insert", self.text.index(f"@{event.x},{event.y}"))
        except Exception:
            pass

    def _scroll_near_reader_position(self):
        if not self.text or not self.app.reader.has_text():
            return

        visible_before = self.app.reader.raw_index_to_visible_word_number(self.app.reader.get_index())
        if visible_before <= 0:
            self.text.see("1.0")
            return

        # Tk text indexes are line/character based, so the safest lightweight
        # approach is proportional scrolling based on visible word progress.
        total_visible = len([
            word for word in self.app.reader.words
            if word != self.app.reader.PARAGRAPH_BREAK_TOKEN
        ])
        if total_visible <= 0:
            return

        fraction = max(0.0, min(1.0, visible_before / total_visible))
        self.text.yview_moveto(fraction)

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
        self.zoom_size = min(32, self.zoom_size + 2)
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
