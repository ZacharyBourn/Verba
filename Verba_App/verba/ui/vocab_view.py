import tkinter as tk
from tkinter import messagebox


class VocabView:
    """Embedded vocabulary view.

    This view renders inside MainWindow's main container. It does not create a
    popup/Toplevel window.
    """

    def __init__(self, app, parent):
        self.app = app
        self.parent = parent
        self.listbox = None
        self.details_label = None
        self.entries = []

    def clear(self):
        for widget in self.parent.winfo_children():
            widget.destroy()

    def render(self):
        self.clear()
        self.entries = self.app.vocab_manager.all_entries()

        header = tk.Frame(self.parent, bg=self.app.bg_color)
        header.pack(fill="x", padx=30, pady=(24, 12))

        tk.Button(
            header,
            text="← Library",
            command=self.app.show_library_view,
            width=12
        ).pack(side="left")

        if self.app.current_book:
            tk.Button(
                header,
                text="Reader",
                command=self.app.show_reader_view,
                width=12
            ).pack(side="left", padx=(8, 0))

        tk.Label(
            header,
            text="Saved Vocabulary",
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

        if not self.entries:
            tk.Label(
                card,
                text="Your vocab list is empty.",
                font=("Helvetica", 15, "bold"),
                bg=self.app.panel_color,
                fg=self.app.text_color
            ).pack(pady=(80, 8))

            tk.Label(
                card,
                text="Words you save from the reader will appear here.",
                font=("Helvetica", 11),
                bg=self.app.panel_color,
                fg=self.app.subtle_text
            ).pack()
            return

        list_frame = tk.Frame(card, bg=self.app.panel_color)
        list_frame.pack(fill="both", expand=True, padx=18, pady=(18, 10))

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(
            list_frame,
            bg=self.app.library_card,
            fg=self.app.text_color,
            selectbackground=self.app.sidebar_select,
            selectforeground=self.app.text_color,
            activestyle="none",
            yscrollcommand=scrollbar.set,
            font=("Helvetica", 11),
            relief="flat",
            highlightthickness=0,
            borderwidth=0
        )
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)

        for entry in self.entries:
            self.listbox.insert(tk.END, self.format_entry(entry))

        self.details_label = tk.Label(
            card,
            text="Select an entry to see full context.",
            justify="left",
            anchor="w",
            wraplength=980,
            bg=self.app.panel_color,
            fg=self.app.subtle_text,
            font=("Helvetica", 10)
        )
        self.details_label.pack(fill="x", padx=18, pady=(0, 12))

        self.listbox.bind("<<ListboxSelect>>", self.show_selected_details)

        button_frame = tk.Frame(card, bg=self.app.panel_color)
        button_frame.pack(anchor="w", padx=18, pady=(0, 18))

        tk.Button(
            button_frame,
            text="Delete Selected",
            command=self.delete_selected_entry,
            width=16
        ).pack(side="left")

    def format_entry(self, entry):
        word = entry.get("word", "").strip() or "(blank)"
        chapter_title = entry.get("chapter_title", "").strip()
        context = entry.get("context", "").strip()

        preview = context[:80].strip()
        if len(context) > 80:
            preview += "..."

        if chapter_title:
            return f"{word}  |  {chapter_title}  |  {preview}"

        return f"{word}  |  {preview}"

    def show_selected_details(self, event=None):
        if not self.listbox or not self.details_label:
            return

        selection = self.listbox.curselection()
        if not selection:
            return

        entry = self.entries[selection[0]]
        word = entry.get("word", "").strip()
        chapter_title = entry.get("chapter_title", "").strip()
        context = entry.get("context", "").strip()

        detail_text = f"Word/Phrase: {word}"
        if chapter_title:
            detail_text += f"\nChapter: {chapter_title}"
        if context:
            detail_text += f"\nContext: {context}"

        self.details_label.config(text=detail_text)

    def delete_selected_entry(self):
        if not self.listbox:
            return

        selection = self.listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Select a vocab entry to delete.")
            return

        index = selection[0]
        self.entries = self.app.vocab_manager.all_entries()

        if not (0 <= index < len(self.entries)):
            return

        word = self.entries[index].get("word", "").strip() or "this entry"
        confirm = messagebox.askyesno("Delete Vocab Entry", f"Delete '{word}' from vocab?")
        if not confirm:
            return

        self.app.vocab_manager.remove_entry(index)
        self.render()
