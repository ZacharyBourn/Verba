import tkinter as tk
from tkinter import messagebox


class NotesView:
    """Embedded book-notes view.

    These are book-level notes, saved directly on the current Book object.
    They are accessible from both the Library and Reader screens.
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

        book = getattr(self.app, "notes_target_book", None) or self.app.current_book or self.app.get_selected_library_book()

        shell = tk.Frame(self.parent, bg=self.app.bg_color)
        shell.pack(fill="both", expand=True, padx=30, pady=24)

        top_bar = tk.Frame(shell, bg=self.app.bg_color)
        top_bar.pack(fill="x", pady=(0, 16))

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

        tk.Button(
            top_bar,
            text="Save Notes",
            command=self.save_notes,
            width=12
        ).pack(side="right")

        title = "Book Notes"
        subtitle = "Select or open a book to write notes."

        if book:
            title = f"Notes — {book.title}"
            subtitle = "General notes for this book. These save with the library entry."

        tk.Label(
            shell,
            text=title,
            font=("Helvetica", 22, "bold"),
            bg=self.app.bg_color,
            fg=self.app.text_color,
            wraplength=900,
            justify="left"
        ).pack(anchor="w", pady=(0, 6))

        tk.Label(
            shell,
            text=subtitle,
            font=("Helvetica", 11),
            bg=self.app.bg_color,
            fg=self.app.subtle_text,
            wraplength=900,
            justify="left"
        ).pack(anchor="w", pady=(0, 16))

        editor_frame = tk.Frame(
            shell,
            bg=self.app.panel_color,
            highlightbackground=self.app.border_color,
            highlightthickness=1
        )
        editor_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(editor_frame)
        scrollbar.pack(side="right", fill="y")

        self.notes_text = tk.Text(
            editor_frame,
            wrap="word",
            font=(self.app.settings.font_family, 13),
            bg=self.app.text_box_bg,
            fg=self.app.text_color,
            insertbackground=self.app.text_color,
            relief="flat",
            highlightthickness=0,
            borderwidth=0,
            padx=18,
            pady=16,
            yscrollcommand=scrollbar.set
        )
        self.notes_text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.notes_text.yview)

        if book:
            self.notes_text.insert("1.0", getattr(book, "notes", ""))
        else:
            self.notes_text.insert("1.0", "No book selected.")
            self.notes_text.config(state="disabled")

        bottom_bar = tk.Frame(shell, bg=self.app.bg_color)
        bottom_bar.pack(fill="x", pady=(12, 0))

        self.status_label = tk.Label(
            bottom_bar,
            text="",
            font=("Helvetica", 10),
            bg=self.app.bg_color,
            fg=self.app.subtle_text
        )
        self.status_label.pack(side="left")

        if book:
            self.notes_text.focus_set()

    def save_notes(self):
        if not self.notes_text:
            return

        book = getattr(self.app, "notes_target_book", None) or self.app.current_book or self.app.get_selected_library_book()
        if not book:
            messagebox.showinfo("No Book", "Select or open a book before saving notes.")
            return

        notes = self.notes_text.get("1.0", tk.END).strip()
        self.app.save_book_notes(book, notes)

        if self.status_label:
            self.status_label.config(text="Notes saved.")
            self.app.root.after(2500, lambda: self.status_label and self.status_label.config(text=""))
