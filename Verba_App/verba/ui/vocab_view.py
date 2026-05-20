import tkinter as tk
from tkinter import messagebox


class VocabView:
    """Toplevel window that displays and manages saved vocabulary.

    This keeps vocab-list UI code out of MainWindow while preserving the
    existing popup-window behavior. MainWindow still owns the vocab manager,
    colors, and root window; this class only owns the vocab view layout.
    """

    def __init__(self, app):
        self.app = app
        self.window = None
        self.listbox = None
        self.entries = []

    def show(self):
        self.entries = self.app.vocab_manager.all_entries()

        if not self.entries:
            messagebox.showinfo("Vocab List", "Your vocab list is empty.")
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("Vocab List")
        self.window.geometry("760x420")
        self.window.configure(bg=self.app.bg_color)

        tk.Label(
            self.window,
            text="Saved Vocabulary",
            font=("Helvetica", 16, "bold"),
            bg=self.app.bg_color,
            fg=self.app.text_color
        ).pack(pady=(14, 10))

        list_frame = tk.Frame(self.window, bg=self.app.bg_color)
        list_frame.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(
            list_frame,
            bg=self.app.panel_color,
            fg=self.app.text_color,
            selectbackground=self.app.sidebar_select,
            selectforeground=self.app.text_color,
            activestyle="none",
            yscrollcommand=scrollbar.set,
            font=("Helvetica", 11)
        )
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)

        for entry in self.entries:
            self.listbox.insert(tk.END, self.format_entry(entry))

        details_label = tk.Label(
            self.window,
            text="Select an entry to see full context.",
            justify="left",
            anchor="w",
            wraplength=720,
            bg=self.app.bg_color,
            fg=self.app.subtle_text,
            font=("Helvetica", 10)
        )
        details_label.pack(fill="x", padx=14, pady=(0, 10))

        self.listbox.bind(
            "<<ListboxSelect>>",
            lambda event=None: self.show_selected_details(details_label)
        )

        button_frame = tk.Frame(self.window, bg=self.app.bg_color)
        button_frame.pack(pady=(0, 14))

        tk.Button(
            button_frame,
            text="Delete Selected",
            command=self.delete_selected_entry
        ).grid(row=0, column=0, padx=8)

        tk.Button(
            button_frame,
            text="Close",
            command=self.window.destroy
        ).grid(row=0, column=1, padx=8)

    def format_entry(self, entry):
        word = entry.get("word", "").strip() or "(blank)"
        chapter_title = entry.get("chapter_title", "").strip()
        context = entry.get("context", "").strip()

        preview = context[:60].strip()
        if len(context) > 60:
            preview += "..."

        if chapter_title:
            return f"{word}  |  {chapter_title}  |  {preview}"

        return f"{word}  |  {preview}"

    def show_selected_details(self, details_label):
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

        details_label.config(text=detail_text)

    def delete_selected_entry(self):
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

        if self.window:
            self.window.destroy()

        self.show()
