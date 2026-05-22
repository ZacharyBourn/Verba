import tkinter as tk
from tkinter import messagebox


class NotesView:
    """Embedded full-page book notes view."""

    def __init__(self, app, parent):
        self.app = app
        self.parent = parent
        self.book = None
        self.return_target = "library"
        self.text = None
        self.title_label = None
        self.status_label = None

    def render(self, book=None, return_target="library"):
        for widget in self.parent.winfo_children():
            widget.destroy()

        self.book = book or self.app.current_book
        self.return_target = return_target

        container = tk.Frame(self.parent, bg=self.app.bg_color)
        container.pack(fill="both", expand=True, padx=30, pady=24)

        top_bar = tk.Frame(container, bg=self.app.bg_color)
        top_bar.pack(fill="x", pady=(0, 18))

        tk.Button(
            top_bar,
            text="← Library",
            command=self.app.show_library_view,
            width=12
        ).pack(side="left")

        if self.app.current_book:
            tk.Button(
                top_bar,
                text="Reader",
                command=self.app.show_reader_view,
                width=12
            ).pack(side="left", padx=(8, 0))

        self.title_label = tk.Label(
            container,
            text=self._title_text(),
            font=("Helvetica", 22, "bold"),
            bg=self.app.bg_color,
            fg=self.app.text_color,
            wraplength=900,
            justify="left"
        )
        self.title_label.pack(anchor="w", pady=(0, 8))

        tk.Label(
            container,
            text="General notes for this book.",
            font=("Helvetica", 12),
            bg=self.app.bg_color,
            fg=self.app.subtle_text
        ).pack(anchor="w", pady=(0, 12))

        text_frame = tk.Frame(
            container,
            bg=self.app.panel_color,
            highlightbackground=self.app.border_color,
            highlightthickness=1
        )
        text_frame.pack(fill="both", expand=True)

        self.text = tk.Text(
            text_frame,
            wrap="word",
            font=("Helvetica", 12),
            bg=self.app.text_box_bg,
            fg=self.app.text_color,
            insertbackground=self.app.text_color,
            relief="flat",
            highlightthickness=0,
            borderwidth=0,
            padx=18,
            pady=18
        )
        self.text.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(text_frame, command=self.text.yview)
        scrollbar.pack(side="right", fill="y")
        self.text.configure(yscrollcommand=scrollbar.set)

        if self.book:
            self.text.insert("1.0", getattr(self.book, "notes", ""))

        button_bar = tk.Frame(container, bg=self.app.bg_color)
        button_bar.pack(fill="x", pady=(16, 0))

        tk.Button(
            button_bar,
            text="Save Notes",
            command=self.save_notes,
            width=14
        ).pack(side="left")

        tk.Button(
            button_bar,
            text="Back",
            command=self.go_back,
            width=12
        ).pack(side="left", padx=(8, 0))

        self.status_label = tk.Label(
            button_bar,
            text="",
            font=("Helvetica", 11),
            bg=self.app.bg_color,
            fg=self.app.subtle_text
        )
        self.status_label.pack(side="left", padx=(12, 0))

        self.text.focus_set()

    def _title_text(self):
        if not self.book:
            return "Book Notes"

        return f"Book Notes: {self.book.title}"

    def save_notes(self):
        if not self.book:
            messagebox.showinfo("No Book", "Open or select a book first.")
            return

        self.book.notes = self.text.get("1.0", tk.END).strip()
        self.app.save_book_notes(self.book)

        if self.status_label:
            self.status_label.config(text="Saved.")

        self.app.refresh_library_note_preview_for_book(self.book)

    def go_back(self):
        if self.return_target == "reader" and self.app.current_book:
            self.app.show_reader_view()
        else:
            self.app.show_library_view()
