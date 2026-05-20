import tkinter as tk
from tkinter import messagebox


class StatsView:
    """Embedded reading-stats view.

    This view renders inside MainWindow's main container. It does not create a
    popup/Toplevel window.
    """

    def __init__(self, app, parent):
        self.app = app
        self.parent = parent

    def clear(self):
        for widget in self.parent.winfo_children():
            widget.destroy()

    def render(self):
        self.clear()
        stats = self.app.stats_manager.get_stats_summary()

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
            text="Reading Stats",
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

        tk.Label(
            card,
            text="Your Verba Progress",
            font=("Helvetica", 14, "bold"),
            bg=self.app.panel_color,
            fg=self.app.text_color
        ).pack(anchor="w", padx=18, pady=(18, 12))

        stats_grid = tk.Frame(card, bg=self.app.panel_color)
        stats_grid.pack(fill="x", padx=18, pady=(0, 8))
        stats_grid.grid_columnconfigure(0, weight=1)
        stats_grid.grid_columnconfigure(1, weight=1)

        stat_items = [
            ("Total Reading Time", f"{stats['hours']}h {stats['minutes']}m"),
            ("Total Words Read", f"{stats['words']}"),
            ("Reading Sessions", f"{stats['sessions']}"),
            ("Books Opened", f"{stats['books_opened']}"),
            ("Books Finished", f"{stats['books_finished']}"),
            ("Current Streak", f"{stats['streak']}"),
            ("Best Streak", f"{stats['best_streak']}"),
        ]

        for i, (label_text, value_text) in enumerate(stat_items):
            row = i // 2
            col = i % 2

            item_frame = tk.Frame(
                stats_grid,
                bg=self.app.library_card,
                highlightbackground=self.app.border_color,
                highlightthickness=1
            )
            item_frame.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

            tk.Label(
                item_frame,
                text=label_text,
                font=("Helvetica", 11),
                bg=self.app.library_card,
                fg=self.app.subtle_text,
                anchor="w"
            ).pack(anchor="w", padx=14, pady=(14, 4))

            tk.Label(
                item_frame,
                text=value_text,
                font=("Helvetica", 20, "bold"),
                bg=self.app.library_card,
                fg=self.app.text_color,
                anchor="w"
            ).pack(anchor="w", padx=14, pady=(0, 14))

        footer = tk.Label(
            card,
            text="Stats are saved automatically as you read.",
            font=("Helvetica", 10),
            bg=self.app.panel_color,
            fg=self.app.subtle_text
        )
        footer.pack(anchor="w", padx=18, pady=(8, 12))

        button_frame = tk.Frame(card, bg=self.app.panel_color)
        button_frame.pack(anchor="w", padx=18, pady=(0, 18))

        tk.Button(
            button_frame,
            text="Reset Stats",
            command=self.reset_stats,
            width=14
        ).pack(side="left")

    def reset_stats(self):
        confirm = messagebox.askyesno(
            "Reset Stats",
            "Are you sure you want to reset all reading stats? This cannot be undone."
        )

        if not confirm:
            return

        self.app.stats_manager.reset()
        self.render()
