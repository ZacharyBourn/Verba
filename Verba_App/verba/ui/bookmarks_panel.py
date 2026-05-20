import tkinter as tk


class BookmarksPanel(tk.Frame):
    """Reader sidebar panel for listing, opening, and deleting bookmarks.

    This class owns the bookmark list UI only. MainWindow still owns the actual
    bookmark actions because it has the current reader/book/session state.
    """

    def __init__(
        self,
        parent,
        panel_color,
        text_color,
        sidebar_select,
        on_delete,
        on_activate
    ):
        super().__init__(parent, bg=panel_color)

        self.panel_color = panel_color
        self.text_color = text_color
        self.sidebar_select = sidebar_select
        self.on_delete = on_delete
        self.on_activate = on_activate

        self.entries = []

        self._build()

    def _build(self):
        header = tk.Frame(self, bg=self.panel_color)
        header.pack(fill="x", padx=14, pady=(6, 4))

        tk.Label(
            header,
            text="Bookmarks",
            font=("Helvetica", 11, "bold"),
            bg=self.panel_color,
            fg=self.text_color
        ).pack(side="left")

        tk.Button(
            header,
            text="Delete",
            command=self.on_delete,
            width=8
        ).pack(side="right")

        self.listbox = tk.Listbox(
            self,
            height=12,
            bg=self.panel_color,
            fg=self.text_color,
            selectbackground=self.sidebar_select,
            selectforeground=self.text_color,
            activestyle="none",
            relief="flat",
            highlightthickness=0,
            borderwidth=0
        )
        self.listbox.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.listbox.bind("<Double-Button-1>", self.on_activate)

    def clear(self):
        self.entries = []
        self.listbox.delete(0, tk.END)

    def refresh(self, book, entries):
        self.clear()
        self.entries = list(entries or [])

        if not book:
            return

        for _, bookmark in self.entries:
            chapter_name = f"Ch {bookmark.chapter_index + 1}"
            if 0 <= bookmark.chapter_index < len(book.chapters):
                chapter_name = book.chapters[bookmark.chapter_index].title

            label = bookmark.label.strip() if bookmark.label.strip() else "Bookmark"
            self.listbox.insert(tk.END, f"{chapter_name} | {label}")

    def get_selected_entry(self):
        selection = self.listbox.curselection()
        if not selection:
            return None

        selected_index = selection[0]
        if selected_index < 0 or selected_index >= len(self.entries):
            return None

        return self.entries[selected_index]
