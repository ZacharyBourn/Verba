import tkinter as tk
from tkinter import messagebox


class NotesView:
    """Embedded book-notes view.

    The Library can open this larger notes page. The Reader uses an inline
    notes panel for quick note taking while reading.
    """

    def __init__(self, app, parent):
        self.app = app
        self.parent = parent
        self.notes_text = None
        self.status_label = None

    def clear(self):
        for widget in self.parent.winfo_children():
            widget.destroy()

    def render(self):
        self.clear()

        header = tk.Frame(self.parent, bg=self.app.bg_color)
        header.pack(fill="x", padx=30, pady=(24, 12))

        return_to_reader = (
            getattr(self.app, "notes_return_view", "library") == "reader"
            and self.app.current_book is not None
        )

        tk.Button(
            header,
            text="← Back" if return_to_reader else "← Library",
            command=self.app.show_reader_view if return_to_reader else self.app.show_library_view,
            width=12
        ).pack(side="left")

        if self.app.current_book and not return_to_reader:
            tk.Button(
                header,
                text="Reader",
                command=self.app.show_reader_view,
                width=12
            ).pack(side="left", padx=(8, 0))

        tk.Label(
            header,
            text="Book Notes",
            font=("Helvetica", 24, "bold"),
            bg=self.app.bg_color,
            fg=self.app.text_color
        ).pack(side="left", padx=24)

        card = tk.Frame(
            self.parent,
            bg=self.app.panel_color,
            highlightbackground=self.app.border_color,
            highlightthickness=1
        )
        card.pack(fill="both", expand=True, padx=30, pady=(0, 24))

        title_text = "No book selected"
        if self.app.current_book:
            title_text = f"{self.app.current_book.title} — {self.app.current_book.author}"

        tk.Label(
            card,
            text=title_text,
            font=("Helvetica", 14, "bold"),
            bg=self.app.panel_color,
            fg=self.app.text_color,
            wraplength=900,
            justify="left"
        ).pack(anchor="w", padx=18, pady=(18, 8))

        tk.Label(
            card,
            text="Use this space for general notes about the book: themes, character notes, questions, reactions, or research ideas.",
            font=("Helvetica", 11),
            bg=self.app.panel_color,
            fg=self.app.subtle_text,
            wraplength=900,
            justify="left"
        ).pack(anchor="w", padx=18, pady=(0, 12))

        self.notes_text = tk.Text(
            card,
            wrap="word",
            font=("Helvetica", 12),
            bg=self.app.text_box_bg,
            fg=self.app.text_color,
            insertbackground=self.app.text_color,
            relief="flat",
            padx=14,
            pady=12
        )
        self.notes_text.pack(fill="both", expand=True, padx=18, pady=(0, 12))

        if self.app.current_book:
            self.notes_text.insert("1.0", getattr(self.app.current_book, "notes", ""))

        footer = tk.Frame(card, bg=self.app.panel_color)
        footer.pack(fill="x", padx=18, pady=(0, 18))

        self.status_label = tk.Label(
            footer,
            text="",
            font=("Helvetica", 10),
            bg=self.app.panel_color,
            fg=self.app.subtle_text
        )
        self.status_label.pack(side="left")

        tk.Button(
            footer,
            text="Save Notes",
            command=self.save_notes,
            width=12
        ).pack(side="right")

        if return_to_reader:
            tk.Button(
                footer,
                text="← Back to Reader",
                command=self.app.show_reader_view,
                width=16
            ).pack(side="right", padx=(0, 8))

    def save_notes(self):
        if not self.app.current_book:
            messagebox.showinfo("No Book", "Open or select a book first.")
            return

        notes = self.notes_text.get("1.0", tk.END).strip()
        self.app.save_current_book_notes(notes)

        if self.status_label:
            self.status_label.config(text="Notes saved.")

        messagebox.showinfo("Saved", "Book notes saved.")
