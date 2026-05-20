import tkinter as tk
from tkinter import messagebox


class StatsView:
    """Toplevel window that displays and resets reading stats.

    This keeps stats UI code out of MainWindow while preserving the
    existing popup-window behavior. MainWindow still owns the managers,
    colors, and root window; this class only owns the stats view layout.
    """

    def __init__(self, app):
        self.app = app
        self.window = None

    def show(self):
        stats = self.app.stats_manager.get_stats_summary()

        self.window = tk.Toplevel(self.app.root)
        self.window.title("Reading Stats")
        self.window.geometry("760x800")
        self.window.configure(bg=self.app.bg_color)
        self.window.resizable(False, False)

        tk.Label(
            self.window,
            text="Reading Stats",
            font=("Helvetica", 16, "bold"),
            bg=self.app.bg_color,
            fg=self.app.text_color
        ).pack(pady=(14, 10))

        card = tk.Frame(
            self.window,
            bg=self.app.panel_color,
            highlightbackground=self.app.border_color,
            highlightthickness=1
        )
        card.pack(fill="both", expand=True, padx=18, pady=(0, 14))

        header = tk.Label(
            card,
            text="Your Verba Progress",
            font=("Helvetica", 13, "bold"),
            bg=self.app.panel_color,
            fg=self.app.text_color
        )
        header.pack(anchor="w", padx=16, pady=(16, 10))

        stats_grid = tk.Frame(card, bg=self.app.panel_color)
        stats_grid.pack(fill="x", padx=16, pady=(0, 8))

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

            stats_grid.grid_columnconfigure(col, weight=1)

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
                font=("Helvetica", 18, "bold"),
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
        footer.pack(anchor="w", padx=16, pady=(8, 12))

        button_frame = tk.Frame(self.window, bg=self.app.bg_color)
        button_frame.pack(pady=(0, 14))

        tk.Button(
            button_frame,
            text="Reset Stats",
            command=self.reset_stats,
            width=12
        ).grid(row=0, column=0, padx=8)

        tk.Button(
            button_frame,
            text="Close",
            command=self.window.destroy,
            width=12
        ).grid(row=0, column=1, padx=8)

    def reset_stats(self):
        confirm = messagebox.askyesno(
            "Reset Stats",
            "Are you sure you want to reset all reading stats? This cannot be undone."
        )

        if not confirm:
            return

        self.app.stats_manager.reset()

        if self.window:
            self.window.destroy()

        self.show()
