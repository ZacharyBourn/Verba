
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from pathlib import Path
import time

from Verba_App.verba.bookmarks import BookmarkManager
from Verba_App.verba.vocab import VocabManager
from Verba_App.verba.epub_parser import load_epub_book
from Verba_App.verba.library import LibraryManager
from Verba_App.verba.models import Bookmark, Book, Chapter
from Verba_App.verba.reader import Reader
from Verba_App.verba.session import SessionManager
from Verba_App.verba.settings import SettingsManager
from Verba_App.verba.stats import StatsManager
from Verba_App.verba.ui.stats_view import StatsView
from Verba_App.verba.ui.vocab_view import VocabView
from Verba_App.verba.ui.bookmarks_panel import BookmarksPanel
from Verba_App.verba.ui.overview_view import OverviewView
from Verba_App.verba.ui.notes_view import NotesView
from Verba_App.verba.ui.themes import get_theme, THEME_NAMES


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.reader = Reader()
        self.settings_manager = SettingsManager()
        self.session_manager = SessionManager()
        self.library_manager = LibraryManager()
        self.bookmark_manager = BookmarkManager()
        self.vocab_manager = VocabManager()
        self.stats_manager = StatsManager()

        self.current_book = None
        self.current_chapter_index = 0
        self.current_file_path = None
        self.current_bookmark_entries = []
        self.current_display_text = ""
        self.selected_word = ""
        self.notes_target_book = None

        self.settings = self.settings_manager.settings
        self.session = self.session_manager.session

        self.root.title("Verba")
        self.root.geometry(f"{self.settings.window_width}x{self.settings.window_height}")
        self.root.minsize(1100, 760)
        self.root.resizable(True, True)

        self.running = False
        self.focus_mode = False
        self.current_after_id = None

        self.session_start_time = None
        self.session_words_read = 0

        self.intro_after_ids = []
        self.intro_active = True

        self.configure_theme()
        self.build_ui()
        self.show_library_view()
        self.try_restore_last_session(open_reader=False)
        self.start_intro_sequence()

        self.overview_preview_active = False

        self.root.bind("<Escape>", self.exit_focus_mode)
        self.root.bind("<space>", self.toggle_play_pause)
        self.root.bind("<Left>", self.back_five)

    def configure_theme(self):
        palette = get_theme(self.settings.theme)

        self.bg_color = palette["bg_color"]
        self.panel_color = palette["panel_color"]
        self.text_box_bg = palette["text_box_bg"]
        self.text_color = palette["text_color"]
        self.subtle_text = palette["subtle_text"]
        self.border_color = palette["border_color"]
        self.sidebar_select = palette["sidebar_select"]
        self.library_card = palette["library_card"]
        self.intro_accent = palette["intro_accent"]

        self.root.configure(bg=self.bg_color)

    def build_ui(self):
        self.container = tk.Frame(self.root, bg=self.bg_color)
        self.container.pack(fill="both", expand=True)

        self.library_view = tk.Frame(self.container, bg=self.bg_color)
        self.reader_view = tk.Frame(self.container, bg=self.bg_color)
        self.stats_view_frame = tk.Frame(self.container, bg=self.bg_color)
        self.vocab_view_frame = tk.Frame(self.container, bg=self.bg_color)
        self.overview_view_frame = tk.Frame(self.container, bg=self.bg_color)
        self.notes_view_frame = tk.Frame(self.container, bg=self.bg_color)

        self.stats_view = StatsView(self, self.stats_view_frame)
        self.vocab_view = VocabView(self, self.vocab_view_frame)
        self.overview_view = OverviewView(self, self.overview_view_frame)
        self.notes_view = NotesView(self, self.notes_view_frame)

        self.build_library_view()
        self.build_reader_view()
        self.build_intro_overlay()

    def _hex_to_rgb(self, value):
        value = value.lstrip("#")
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))

    def _rgb_to_hex(self, rgb):
        return "#{:02x}{:02x}{:02x}".format(*rgb)

    def _blend_colors(self, c1, c2, t):
        r1, g1, b1 = self._hex_to_rgb(c1)
        r2, g2, b2 = self._hex_to_rgb(c2)

        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)

        return self._rgb_to_hex((r, g, b))

    def _animate_label_fade(self, label, start_color, end_color, duration=500, steps=18, on_complete=None):
        if not self.intro_active:
            return

        interval = max(1, duration // steps)

        def step(index=0):
            if not self.intro_active:
                return

            t = index / steps
            label.config(fg=self._blend_colors(start_color, end_color, t))

            if index < steps:
                after_id = self.root.after(interval, lambda: step(index + 1))
                self.intro_after_ids.append(after_id)
            elif on_complete:
                on_complete()

        step()

    def _hold_then_finish(self, hold_time, on_complete=None):
        if not self.intro_active:
            return

        if on_complete:
            after_id = self.root.after(hold_time, on_complete)
            self.intro_after_ids.append(after_id)

    def build_intro_overlay(self):
        self.intro_overlay = tk.Frame(self.container, bg=self.bg_color)

        self.intro_center = tk.Frame(self.intro_overlay, bg=self.bg_color)
        self.intro_center.place(relx=0.5, rely=0.5, anchor="center")

        self.intro_label = tk.Label(
            self.intro_center,
            text="Welcome to Verba",
            font=("Helvetica", 30, "bold"),
            bg=self.bg_color,
            fg=self.bg_color,
            justify="center"
        )
        self.intro_label.pack()

        self.intro_subtitle = tk.Label(
            self.intro_center,
            text="",
            font=("Helvetica", 13),
            bg=self.bg_color,
            fg=self.bg_color,
            justify="center"
        )
        self.intro_subtitle.pack(pady=(10, 0))

    def start_intro_sequence(self):
        self.intro_active = True
        self.intro_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.intro_label.config(text="Welcome to Verba", fg=self.bg_color)
        self.intro_subtitle.config(text="", fg=self.bg_color)

        self._animate_label_fade(
            self.intro_label,
            self.bg_color,
            self.text_color,
            duration=700,
            on_complete=lambda: self._hold_then_finish(
                1100,
                self.show_intro_import_message
            )
        )

    def _queue_intro(self, delay, callback):
        after_id = self.root.after(delay, callback)
        self.intro_after_ids.append(after_id)

    def show_intro_import_message(self):
        if not self.intro_active:
            return

        def fade_in_second_message():
            if not self.intro_active:
                return

            self.intro_label.config(text="Let's get reading", fg=self.bg_color)
            self.intro_subtitle.config(text="", fg=self.bg_color)

            self._animate_label_fade(
                self.intro_label,
                self.bg_color,
                self.text_color,
                duration=650,
                on_complete=lambda: self._hold_then_finish(
                    1800,
                    self.finish_intro_sequence
                )
            )

        self._animate_label_fade(
            self.intro_label,
            self.text_color,
            self.bg_color,
            duration=500,
            on_complete=fade_in_second_message
        )

    def finish_intro_sequence(self):
        if not self.intro_active:
            return

        self.intro_active = False

        for after_id in self.intro_after_ids:
            try:
                self.root.after_cancel(after_id)
            except Exception:
                pass
        self.intro_after_ids.clear()

        self.intro_overlay.place_forget()
        self.refresh_library_view()

    def build_library_view(self):
        title = tk.Label(
            self.library_view,
            text="Verba",
            font=("Helvetica", 26, "bold"),
            bg=self.bg_color,
            fg=self.text_color
        )
        title.pack(pady=(24, 8))

        subtitle = tk.Label(
            self.library_view,
            text="Your Library",
            font=("Helvetica", 13),
            bg=self.bg_color,
            fg=self.subtle_text
        )
        subtitle.pack(pady=(0, 20))

        top_buttons = tk.Frame(self.library_view, bg=self.bg_color)
        top_buttons.pack(pady=(0, 15))

        tk.Button(top_buttons, text="Import TXT / EPUB", command=self.import_book_into_library, width=18).grid(row=0, column=0, padx=6)
        tk.Button(top_buttons, text="Open Selected Book", command=self.open_selected_library_book, width=18).grid(row=0, column=1, padx=6)
        tk.Button(top_buttons, text="Remove Selected Book", command=self.remove_selected_library_book, width=18).grid(row=0, column=2, padx=6)
        tk.Button(top_buttons, text="Open Pasted Text", command=self.open_pasted_text_to_reader, width=18).grid(row=0, column=3, padx=6)
        tk.Button(top_buttons, text="Vocab", command=self.show_vocab_view, width=18).grid(row=0, column=4, padx=6)
        tk.Button(top_buttons, text="Stats", command=self.show_stats_view, width=18).grid(row=0, column=5, padx=6)

        theme_frame = tk.Frame(self.library_view, bg=self.bg_color)
        theme_frame.pack(pady=(0, 12))

        tk.Label(
            theme_frame,
            text="Theme:",
            font=("Helvetica", 10),
            bg=self.bg_color,
            fg=self.subtle_text
        ).pack(side="left", padx=(0, 8))

        self.theme_var = tk.StringVar(value=self.settings.theme if self.settings.theme in THEME_NAMES else "dark")
        self.theme_menu = tk.OptionMenu(
            theme_frame,
            self.theme_var,
            *THEME_NAMES,
            command=self.on_theme_change
        )
        self.theme_menu.config(width=10)
        self.theme_menu.pack(side="left")

        content = tk.Frame(self.library_view, bg=self.bg_color)
        content.pack(fill="both", expand=True, padx=30, pady=(5, 20))

        left_panel = tk.Frame(
            content,
            bg=self.panel_color,
            highlightbackground=self.border_color,
            highlightthickness=1
        )
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 15))

        tk.Label(
            left_panel,
            text="Books",
            font=("Helvetica", 13, "bold"),
            bg=self.panel_color,
            fg=self.text_color
        ).pack(anchor="w", padx=14, pady=(14, 8))

        self.library_listbox = tk.Listbox(
            left_panel,
            bg=self.panel_color,
            fg=self.text_color,
            selectbackground=self.sidebar_select,
            selectforeground=self.text_color,
            activestyle="none",
            relief="flat",
            highlightthickness=0,
            borderwidth=0,
            font=("Helvetica", 11)
        )
        self.library_listbox.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.library_listbox.bind("<<ListboxSelect>>", self.on_library_select)
        self.library_listbox.bind("<Double-Button-1>", self.on_library_activate)

        right_panel = tk.Frame(
            content,
            width=330,
            bg=self.library_card,
            highlightbackground=self.border_color,
            highlightthickness=1
        )
        right_panel.pack(side="right", fill="y")
        right_panel.pack_propagate(False)

        tk.Label(
            right_panel,
            text="Details",
            font=("Helvetica", 13, "bold"),
            bg=self.library_card,
            fg=self.text_color
        ).pack(anchor="w", padx=14, pady=(14, 10))

        self.library_details_title = tk.Label(
            right_panel,
            text="No book selected",
            font=("Helvetica", 14, "bold"),
            bg=self.library_card,
            fg=self.text_color,
            wraplength=280,
            justify="left",
            anchor="w"
        )
        self.library_details_title.pack(anchor="w", padx=14, pady=(0, 8))

        self.library_details_author = tk.Label(
            right_panel,
            text="",
            font=("Helvetica", 11),
            bg=self.library_card,
            fg=self.subtle_text,
            wraplength=280,
            justify="left",
            anchor="w"
        )
        self.library_details_author.pack(anchor="w", padx=14, pady=(0, 8))

        self.library_details_type = tk.Label(
            right_panel,
            text="",
            font=("Helvetica", 11),
            bg=self.library_card,
            fg=self.subtle_text,
            wraplength=280,
            justify="left",
            anchor="w"
        )
        self.library_details_type.pack(anchor="w", padx=14, pady=(0, 8))

        self.library_details_chapters = tk.Label(
            right_panel,
            text="",
            font=("Helvetica", 11),
            bg=self.library_card,
            fg=self.subtle_text,
            wraplength=280,
            justify="left",
            anchor="w"
        )
        self.library_details_chapters.pack(anchor="w", padx=14, pady=(0, 8))

        self.library_details_path = tk.Label(
            right_panel,
            text="",
            font=("Helvetica", 10),
            bg=self.library_card,
            fg=self.subtle_text,
            wraplength=280,
            justify="left",
            anchor="w"
        )
        self.library_details_path.pack(anchor="w", padx=14, pady=(0, 14))

        self.library_details_notes_preview = tk.Label(
            right_panel,
            text="",
            font=("Helvetica", 10),
            bg=self.library_card,
            fg=self.subtle_text,
            wraplength=280,
            justify="left",
            anchor="w"
        )
        self.library_details_notes_preview.pack(anchor="w", padx=14, pady=(0, 10))

        self.library_notes_button = tk.Button(
            right_panel,
            text="Book Notes",
            command=lambda: self.show_notes_view(self.get_selected_library_book()),
            width=16
        )
        self.library_notes_button.pack(anchor="w", padx=14, pady=(0, 14))

        bottom_area = tk.Frame(self.library_view, bg=self.bg_color)
        bottom_area.pack(fill="x", padx=30, pady=(0, 24))

        tk.Label(
            bottom_area,
            text="Quick paste:",
            font=("Helvetica", 12),
            bg=self.bg_color,
            fg=self.text_color
        ).pack(anchor="w", pady=(0, 6))

        self.library_paste_box = tk.Text(
            bottom_area,
            height=6,
            width=100,
            font=("Helvetica", 11),
            wrap="word",
            bg=self.text_box_bg,
            fg=self.text_color,
            insertbackground=self.text_color
        )
        self.library_paste_box.pack(fill="x")

    def build_reader_view(self):
        self.sidebar = tk.Frame(
            self.reader_view,
            width=280,
            bg=self.panel_color,
            highlightbackground=self.border_color,
            highlightthickness=1
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.main_area = tk.Frame(self.reader_view, bg=self.bg_color)
        self.main_area.pack(side="right", fill="both", expand=True)

        self.build_sidebar()
        self.build_main_area()

    def build_sidebar(self):
        self.sidebar_title = tk.Label(
            self.sidebar,
            text="No Book Loaded",
            font=("Helvetica", 14, "bold"),
            bg=self.panel_color,
            fg=self.text_color,
            wraplength=240,
            justify="left",
            anchor="w"
        )
        self.sidebar_title.pack(padx=14, pady=(14, 4), anchor="w")

        self.sidebar_author = tk.Label(
            self.sidebar,
            text="",
            font=("Helvetica", 10),
            bg=self.panel_color,
            fg=self.subtle_text,
            wraplength=240,
            justify="left",
            anchor="w"
        )
        self.sidebar_author.pack(padx=14, pady=(0, 10), anchor="w")

        tk.Frame(self.sidebar, height=1, bg=self.border_color).pack(fill="x", padx=12, pady=6)

        tk.Label(
            self.sidebar,
            text="Chapters",
            font=("Helvetica", 11, "bold"),
            bg=self.panel_color,
            fg=self.text_color
        ).pack(anchor="w", padx=14, pady=(6, 4))

        self.chapter_listbox = tk.Listbox(
            self.sidebar,
            height=20, #CHANGES THE SIZE OF THE CHAPTER LIST BOX ON SIDE OF WINDOW
            bg=self.panel_color,
            fg=self.text_color,
            selectbackground=self.sidebar_select,
            selectforeground=self.text_color,
            activestyle="none",
            relief="flat",
            highlightthickness=0,
            borderwidth=0
        )
        self.chapter_listbox.pack(fill="x", padx=12, pady=(0, 10))
        self.chapter_listbox.bind("<<ListboxSelect>>", self.on_chapter_select)

        tk.Frame(self.sidebar, height=1, bg=self.border_color).pack(fill="x", padx=12, pady=6)

        self.bookmarks_panel = BookmarksPanel(
            self.sidebar,
            panel_color=self.panel_color,
            text_color=self.text_color,
            sidebar_select=self.sidebar_select,
            on_delete=self.delete_selected_bookmark,
            on_activate=self.on_bookmark_activate
        )
        self.bookmarks_panel.pack(fill="both", expand=True)

    def build_main_area(self):
        self.top_bar = tk.Frame(self.main_area, bg=self.bg_color)
        self.top_bar.pack(fill="x", pady=(14, 0), padx=20)

        self.library_button = tk.Button(self.top_bar, text="← Library", command=self.show_library_view, width=12)
        self.library_button.pack(side="left")

        self.focus_button = tk.Button(self.top_bar, text="Focus Mode", command=self.toggle_focus_mode, width=12)
        self.focus_button.pack(side="right")

        self.reader_stats_button = tk.Button(self.top_bar, text="Stats", command=self.show_stats_view, width=10)
        self.reader_stats_button.pack(side="right", padx=(0, 8))

        self.reader_vocab_button = tk.Button(self.top_bar, text="Vocab", command=self.show_vocab_view, width=10)
        self.reader_vocab_button.pack(side="right", padx=(0, 8))

        self.reader_overview_button = tk.Button(self.top_bar, text="Overview", command=self.show_overview_view, width=10)
        self.reader_overview_button.pack(side="right", padx=(0, 8))

        self.reader_notes_button = tk.Button(self.top_bar, text="Notes", command=self.show_notes_view, width=10)
        self.reader_notes_button.pack(side="right", padx=(0, 8))

        self.title_label = tk.Label(
            self.main_area,
            text="Verba",
            font=("Helvetica", 22, "bold"),
            bg=self.bg_color,
            fg=self.text_color
        )
        self.title_label.pack(pady=(10, 10))

        self.book_label = tk.Label(
            self.main_area,
            text="No book loaded",
            font=("Helvetica", 12),
            bg=self.bg_color,
            fg=self.subtle_text
        )
        self.book_label.pack(pady=(0, 5))

        self.chapter_label = tk.Label(
            self.main_area,
            text="",
            font=("Helvetica", 12),
            bg=self.bg_color,
            fg=self.subtle_text
        )
        self.chapter_label.pack(pady=(0, 10))

        self.display_frame = tk.Frame(
            self.main_area,
            width=760,
            height=220,
            bg=self.panel_color,
            highlightbackground=self.border_color,
            highlightthickness=1
        )
        self.display_frame.pack(pady=20)
        self.display_frame.pack_propagate(False)

        self.display_text = tk.Text(
            self.display_frame,
            wrap="word",
            font=(self.settings.font_family, self.settings.font_size, "bold"),
            bg=self.panel_color,
            fg=self.text_color,
            insertbackground=self.text_color,
            relief="flat",
            highlightthickness=0,
            borderwidth=0,
            cursor="xterm",
            padx=30,
            pady=30
        )
        self.display_text.pack(expand=True, fill="both")

        self.display_text.tag_configure("selected_word", background="#444444", foreground="#ffffff")
        self.display_text.tag_configure("center", justify="center")

        self.display_text.bind("<ButtonRelease-1>", self.on_text_selection)
        self.display_text.bind("<Double-Button-1>", self.on_display_double_click)

        self.set_display_text("Load a TXT or EPUB file to begin")

        self.progress_label = tk.Label(
            self.main_area,
            text="Progress: 0%",
            font=("Helvetica", 12),
            bg=self.bg_color,
            fg=self.subtle_text
        )
        self.progress_label.pack(pady=(0, 15))

        self.controls_frame = tk.Frame(self.main_area, bg=self.bg_color)
        self.controls_frame.pack(pady=10)

        tk.Button(self.controls_frame, text="Import Book", command=self.import_book_into_library, width=12).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(self.controls_frame, text="Start", command=self.start, width=10).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(self.controls_frame, text="Pause", command=self.pause, width=10).grid(row=0, column=2, padx=5, pady=5)
        tk.Button(self.controls_frame, text="<< Back 5", command=self.back_five, width=10).grid(row=0, column=3, padx=5, pady=5)
        tk.Button(self.controls_frame, text="Reset", command=self.reset, width=10).grid(row=0, column=4, padx=5, pady=5)
        tk.Button(self.controls_frame, text="Bookmark", command=self.add_bookmark, width=10).grid(row=0, column=5, padx=5, pady=5)
        tk.Button(self.controls_frame, text="Save to Vocab", command=self.add_to_vocab, width=12).grid(row=0, column=6, padx=5, pady=5)
        tk.Button(self.controls_frame, text="Save Selected", command=self.add_selected_word_to_vocab, width=12).grid(row=0, column=7, padx=5, pady=5)

        self.chapter_controls = tk.Frame(self.main_area, bg=self.bg_color)
        self.chapter_controls.pack(pady=5)

        tk.Button(self.chapter_controls, text="Previous Chapter", command=self.previous_chapter, width=15).grid(row=0, column=0, padx=8)
        tk.Button(self.chapter_controls, text="Next Chapter", command=self.next_chapter, width=15).grid(row=0, column=1, padx=8)

        self.sliders_frame = tk.Frame(self.main_area, bg=self.bg_color)
        self.sliders_frame.pack(pady=10)

        self.wpm_scale = tk.Scale(
            self.sliders_frame,
            from_=100,
            to=900,
            orient="horizontal",
            label="Words Per Minute",
            bg=self.bg_color,
            fg=self.text_color,
            highlightthickness=0,
            length=220,
            command=self.on_wpm_change
        )
        self.wpm_scale.set(self.settings.default_wpm)
        self.wpm_scale.grid(row=0, column=0, padx=15)

        self.chunk_scale = tk.Scale(
            self.sliders_frame,
            from_=1,
            to=5,
            orient="horizontal",
            label="Chunk Size",
            bg=self.bg_color,
            fg=self.text_color,
            highlightthickness=0,
            length=220,
            command=self.on_chunk_change
        )
        self.chunk_scale.set(self.settings.default_chunk_size)
        self.chunk_scale.grid(row=0, column=1, padx=15)

        self.font_scale = tk.Scale(
            self.sliders_frame,
            from_=20,
            to=54,
            orient="horizontal",
            label="Font Size",
            bg=self.bg_color,
            fg=self.text_color,
            highlightthickness=0,
            length=220,
            command=self.on_font_change
        )
        self.font_scale.set(self.settings.font_size)
        self.font_scale.grid(row=0, column=2, padx=15)

    def hide_content_views(self):
        self.library_view.pack_forget()
        self.reader_view.pack_forget()
        self.stats_view_frame.pack_forget()
        self.vocab_view_frame.pack_forget()
        self.overview_view_frame.pack_forget()
        self.notes_view_frame.pack_forget()

    def show_library_view(self):
        if self.focus_mode:
            self.toggle_focus_mode()

        self.running = False
        self.cancel_scheduled_reader()
        self._flush_stats_session()

        self.hide_content_views()
        self.library_view.pack(fill="both", expand=True)
        self.refresh_library_view()

    def show_reader_view(self):
        self.hide_content_views()
        self.reader_view.pack(fill="both", expand=True)
        self.root.after(50, self.focus_reader_view)

    def focus_reader_view(self):
        try:
            self.display_text.focus_set()
        except Exception:
            self.root.focus_set()

    def show_stats_view(self):
        if self.focus_mode:
            self.toggle_focus_mode()

        self.running = False
        self.cancel_scheduled_reader()
        self._flush_stats_session()

        self.hide_content_views()
        self.stats_view.render()
        self.stats_view_frame.pack(fill="both", expand=True)

    def show_vocab_view(self):
        if self.focus_mode:
            self.toggle_focus_mode()

        self.running = False
        self.cancel_scheduled_reader()
        self._flush_stats_session()

        self.hide_content_views()
        self.vocab_view.render()
        self.vocab_view_frame.pack(fill="both", expand=True)

    def show_overview_view(self):
        if self.focus_mode:
            self.toggle_focus_mode()

        self.running = False
        self.cancel_scheduled_reader()
        self._flush_stats_session()

        self.hide_content_views()
        self.overview_view.render()
        self.overview_view_frame.pack(fill="both", expand=True)

    def show_notes_view(self, book=None):
        if self.focus_mode:
            self.toggle_focus_mode()

        self.running = False
        self.cancel_scheduled_reader()
        self._flush_stats_session()

        target_book = book or self.current_book or self.get_selected_library_book()
        if not target_book:
            messagebox.showinfo("No Book", "Select or open a book before writing notes.")
            return

        self.notes_target_book = target_book
        self.hide_content_views()
        self.notes_view.render()
        self.notes_view_frame.pack(fill="both", expand=True)

    def get_selected_library_book(self):
        try:
            selection = self.library_listbox.curselection()
        except Exception:
            return None

        if not selection:
            return None

        books = self.library_manager.all_books()
        index = selection[0]
        if not (0 <= index < len(books)):
            return None

        return books[index]

    def save_book_notes(self, book: Book, notes: str):
        book.notes = notes

        saved_book = self.library_manager.get_book(book.book_id)
        if saved_book:
            saved_book.notes = notes
            self.library_manager.save()

        if self.current_book and self.current_book.book_id == book.book_id:
            self.current_book.notes = notes

        self.refresh_library_notes_preview(book)

    def refresh_library_notes_preview(self, book: Book = None):
        if not hasattr(self, "library_details_notes_preview"):
            return

        if book is None:
            book = self.get_selected_library_book()

        if not book:
            self.library_details_notes_preview.config(text="")
            return

        notes = getattr(book, "notes", "").strip()
        if notes:
            preview = notes.replace("\n", " ")
            if len(preview) > 120:
                preview = preview[:117].rstrip() + "..."
            self.library_details_notes_preview.config(text=f"Notes: {preview}")
        else:
            self.library_details_notes_preview.config(text="Notes: None yet")

    def refresh_library_view(self):
        self.library_manager.reload()
        self.library_listbox.delete(0, tk.END)

        books = self.library_manager.all_books()
        for book in books:
            self.library_listbox.insert(tk.END, f"{book.title} — {book.author}")

        self.library_details_title.config(text="No book selected")
        self.library_details_author.config(text="")
        self.library_details_type.config(text="")
        self.library_details_chapters.config(text="")
        self.library_details_path.config(text="")
        self.refresh_library_notes_preview(None)

    def on_library_select(self, event):
        selection = self.library_listbox.curselection()
        if not selection:
            return

        book = self.library_manager.all_books()[selection[0]]

        self.library_details_title.config(text=book.title)
        self.library_details_author.config(text=f"Author: {book.author}")
        self.library_details_type.config(text=f"Type: {book.file_type.upper()}")
        real_chapter_count = sum(
            1 for chapter in book.chapters
            if not getattr(chapter, "is_divider", False)
        )
        self.library_details_chapters.config(text=f"Chapters: {real_chapter_count}")
        self.library_details_path.config(
            text=f"Path: {book.file_path if book.file_path else 'Local / unsaved text'}"
        )
        self.refresh_library_notes_preview(book)

    def on_library_activate(self, event):
        self.open_selected_library_book()

    def import_book_into_library(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Supported Files", "*.txt *.epub"), ("Text Files", "*.txt"), ("EPUB Files", "*.epub")]
        )

        if not file_path:
            return

        suffix = Path(file_path).suffix.lower()

        try:
            if suffix == ".txt":
                with open(file_path, "r", encoding="utf-8") as file:
                    text = file.read()

                book_id = Path(file_path).stem.lower().replace(" ", "_")
                existing = self.library_manager.get_book(book_id)

                if existing is None:
                    book = Book(
                        book_id=book_id,
                        title=Path(file_path).stem,
                        author="Unknown",
                        file_path=file_path,
                        file_type="txt",
                        chapters=[Chapter(title="Chapter 1", text=text)]
                    )
                    self.library_manager.add_book(book)

            elif suffix == ".epub":
                existing = self.library_manager.get_book_by_path(file_path)
                if existing is None:
                    book = load_epub_book(file_path)
                    self.library_manager.add_book(book)
            else:
                messagebox.showerror("Unsupported File", "Only TXT and EPUB are supported right now.")
                return

            self.refresh_library_view()
        except Exception as error:
            messagebox.showerror("Error", f"Could not import file:\n{error}")

    def open_selected_library_book(self):
        selection = self.library_listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Select a book from the library.")
            return

        book = self.library_manager.all_books()[selection[0]]
        self.set_current_book(book, chapter_index=self.get_saved_chapter_index_for_book(book.book_id))
        self.show_reader_view()

    def remove_selected_library_book(self):
        selection = self.library_listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Select a book to remove.")
            return

        book = self.library_manager.all_books()[selection[0]]
        confirm = messagebox.askyesno("Remove Book", f"Remove '{book.title}' from the library?")
        if not confirm:
            return

        self.library_manager.remove_book(book.book_id)

        if self.current_book and self.current_book.book_id == book.book_id:
            self.current_book = None
            self.current_chapter_index = 0

        self.refresh_library_view()

    def open_pasted_text_to_reader(self):
        text = self.library_paste_box.get("1.0", tk.END).strip()
        if not text:
            messagebox.showinfo("No Text", "Paste some text first.")
            return

        book = Book(
            book_id="pasted_text",
            title="Pasted Text",
            author="Local",
            file_path="",
            file_type="txt",
            chapters=[Chapter(title="Chapter 1", text=text)]
        )

        self.set_current_book(book, chapter_index=0)
        self.show_reader_view()

    def refresh_sidebar(self):
        if not self.current_book:
            self.sidebar_title.config(text="No Book Loaded")
            self.sidebar_author.config(text="")
            self.chapter_listbox.delete(0, tk.END)
            self.current_bookmark_entries = []
            self.bookmarks_panel.clear()
            return

        self.sidebar_title.config(text=self.current_book.title)
        self.sidebar_author.config(text=self.current_book.author)

        self.chapter_listbox.delete(0, tk.END)
        for i, chapter in enumerate(self.current_book.chapters):
            prefix = "→ " if i == self.current_chapter_index else "   "
            self.chapter_listbox.insert(tk.END, f"{prefix}{chapter.title}")

        if self.current_book.chapters:
            self.chapter_listbox.selection_clear(0, tk.END)
            self.chapter_listbox.selection_set(self.current_chapter_index)
            self.chapter_listbox.see(self.current_chapter_index)

        self.current_bookmark_entries = self.bookmark_manager.get_bookmarks_for_book(self.current_book.book_id)
        self.bookmarks_panel.refresh(self.current_book, self.current_bookmark_entries)

    def delete_selected_bookmark(self):
        if not self.current_book:
            messagebox.showinfo("No Book", "Load a book first.")
            return

        selected_entry = self.bookmarks_panel.get_selected_entry()
        if not selected_entry:
            messagebox.showinfo("No Selection", "Select a bookmark to delete.")
            return

        global_index, bookmark = selected_entry

        label = bookmark.label.strip() if bookmark.label.strip() else "this bookmark"
        confirm = messagebox.askyesno("Delete Bookmark", f"Delete {label}?")
        if not confirm:
            return

        self.bookmark_manager.remove_bookmark(global_index)
        self.refresh_sidebar()

    def on_chapter_select(self, event):
        if not self.current_book:
            return

        selection = self.chapter_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        if index != self.current_chapter_index:
            self.jump_to_chapter(index)

    def on_bookmark_activate(self, event=None):
        if not self.current_book:
            return

        selected_entry = self.bookmarks_panel.get_selected_entry()
        if not selected_entry:
            return

        _, bookmark = selected_entry

        self.set_current_book(self.current_book, bookmark.chapter_index)
        self.reader.set_index(bookmark.word_index)
        self.progress_label.config(text=f"Progress: {self.reader.get_progress()}%")
        self.set_display_text("Jumped to bookmark. Press Start.")
        self.save_session_position()
        self.refresh_sidebar()

    def set_display_text(self, text):
        self.current_display_text = text
        self.selected_word = ""

        self.display_text.config(state="normal")
        self.display_text.delete("1.0", tk.END)
        self.display_text.insert("1.0", text)
        self.display_text.tag_add("center", "1.0", "end")
        self.display_text.tag_remove("selected_word", "1.0", tk.END)
        self.display_text.config(state="disabled")

    def on_text_selection(self, event=None):
        try:
            index = self.display_text.index(f"@{event.x},{event.y}")
        except Exception:
            return

        self.display_text.config(state="normal")
        self.display_text.tag_remove("selected_word", "1.0", tk.END)

        start = self.display_text.index(f"{index} wordstart")
        end = self.display_text.index(f"{index} wordend")

        word = self.display_text.get(start, end).strip()
        cleaned = word.strip("\"'“”‘’()[]{}.,;:!?")

        if cleaned:
            self.selected_word = cleaned
            self.display_text.tag_add("selected_word", start, end)
        else:
            self.selected_word = ""

        self.display_text.config(state="disabled")

    def add_selected_word_to_vocab(self):
        if not self.selected_word:
            messagebox.showinfo("No Selection", "Click a word in the reading text first.")
            return

        chapter_title = ""
        book_id = ""

        if self.current_book:
            book_id = self.current_book.book_id
            if 0 <= self.current_chapter_index < len(self.current_book.chapters):
                chapter_title = self.current_book.chapters[self.current_chapter_index].title

        self.vocab_manager.add_entry(
            word=self.selected_word,
            book_id=book_id,
            chapter_title=chapter_title,
            context=self.current_display_text
        )

        messagebox.showinfo("Saved", f"Saved selected word:\n{self.selected_word}")

    def on_wpm_change(self, value):
        self.settings_manager.update(default_wpm=int(float(value)))

    def on_chunk_change(self, value):
        self.settings_manager.update(default_chunk_size=int(float(value)))

    def on_font_change(self, value):
        font_size = int(float(value))
        self.display_text.config(font=(self.settings.font_family, font_size, "bold"))
        if not self.focus_mode:
            self.settings_manager.update(font_size=font_size)

    def on_theme_change(self, theme_name):
        if theme_name not in THEME_NAMES:
            return

        if theme_name == self.settings.theme:
            return

        self.settings_manager.update(theme=theme_name)
        self.settings = self.settings_manager.settings

        messagebox.showinfo(
            "Theme Saved",
            "Theme saved. Restart Verba to apply it everywhere."
        )

    def on_display_double_click(self, event=None):
        self.add_to_vocab()

    def get_saved_chapter_index_for_book(self, book_id: str) -> int:
        if self.session.current_book_id == book_id:
            return self.session.current_chapter_index
        return 0

    def set_current_book(self, book: Book, chapter_index: int = 0):
        self.running = False
        self.cancel_scheduled_reader()

        self.current_book = book
        self.stats_manager.mark_book_opened(book.book_id)
        self.current_file_path = book.file_path
        self.current_chapter_index = max(0, min(chapter_index, len(book.chapters) - 1))

        saved_word_index = 0
        if (
            self.session.current_book_id == book.book_id
            and self.session.current_chapter_index == self.current_chapter_index
        ):
            saved_word_index = self.session.current_word_index

        chapter = book.chapters[self.current_chapter_index]
        self.reader.load_text_with_index(chapter.text, saved_word_index)

        self.book_label.config(text=f"{book.title} — {book.author}")
        self.chapter_label.config(text=chapter.title)
        self.set_display_text(f"Loaded {book.title}. Press Start.")
        self.progress_label.config(text=f"Progress: {self.reader.get_progress()}%")

        self.session_manager.update(
            current_book_id=book.book_id,
            current_chapter_index=self.current_chapter_index,
            current_word_index=self.reader.get_index(),
            last_opened_file=book.file_path
        )
        self.session = self.session_manager.session
        self.refresh_sidebar()

    def try_restore_last_session(self, open_reader=False):
        if not self.session.current_book_id or not self.session.last_opened_file:
            self.refresh_library_view()
            return

        path = Path(self.session.last_opened_file)
        if not path.exists():
            self.refresh_library_view()
            return

        existing = self.library_manager.get_book_by_path(str(path))
        if existing:
            self.set_current_book(existing, chapter_index=self.get_saved_chapter_index_for_book(existing.book_id))
            if open_reader:
                self.show_reader_view()
            else:
                self.show_library_view()
            return

        self.refresh_library_view()

    def restore_reader_layout(self):
        for widget in [
            self.top_bar,
            self.title_label,
            self.book_label,
            self.chapter_label,
            self.display_frame,
            self.progress_label,
            self.controls_frame,
            self.chapter_controls,
            self.sliders_frame,
        ]:
            widget.pack_forget()

        self.top_bar.pack(fill="x", pady=(14, 0), padx=20)
        self.title_label.pack(pady=(10, 10))
        self.book_label.pack(pady=(0, 5))
        self.chapter_label.pack(pady=(0, 10))
        self.display_frame.pack(pady=20)
        self.progress_label.pack(pady=(0, 15))
        self.controls_frame.pack(pady=10)
        self.chapter_controls.pack(pady=5)
        self.sliders_frame.pack(pady=10)

        self.display_frame.config(width=760, height=220)
        self.display_text.config(
            font=(self.settings.font_family, self.settings.font_size, "bold")
        )

    def toggle_focus_mode(self):
        self.focus_mode = not self.focus_mode

        if self.focus_mode:
            self.sidebar.pack_forget()
            self.controls_frame.pack_forget()
            self.chapter_controls.pack_forget()
            self.sliders_frame.pack_forget()
            self.progress_label.pack_forget()
            self.book_label.pack_forget()
            self.chapter_label.pack_forget()
            self.top_bar.pack_forget()

            self.display_frame.config(width=1000, height=420)
            self.display_frame.pack_configure(pady=90)

            self.display_text.config(
                font=(self.settings.font_family, self.settings.font_size + 10, "bold")
            )

            self.root.attributes("-fullscreen", True)

        else:
            self.root.attributes("-fullscreen", False)
            self.sidebar.pack(side="left", fill="y")
            self.restore_reader_layout()
            self.root.after(75, self.focus_reader_view)

    def exit_focus_mode(self, event=None):
        if self.focus_mode:
            self.toggle_focus_mode()

    def cancel_scheduled_reader(self):
        if self.current_after_id is not None:
            try:
                self.root.after_cancel(self.current_after_id)
            except Exception:
                pass
            self.current_after_id = None

    def _flush_stats_session(self):
        if self.session_start_time is not None:
            elapsed = int(time.time() - self.session_start_time)
            self.stats_manager.add_reading_time(elapsed)
            self.session_start_time = None

        if self.session_words_read > 0:
            self.stats_manager.add_words(self.session_words_read)
            self.session_words_read = 0

    def start(self):
        if not self.reader.has_text():
            self.set_display_text("Please load a book first")
            return

        if not self.running:
            self.running = True
            self.session_start_time = time.time()
            self.session_words_read = 0
            self.stats_manager.start_session()
            self.run_reader()

        self.overview_preview_active = False

    def pause(self):
        self.running = False
        self.cancel_scheduled_reader()
        self._flush_stats_session()
        self.save_session_position()

    def reset(self):
        self.running = False
        self.cancel_scheduled_reader()
        self._flush_stats_session()
        self.reader.reset()
        self.set_display_text("Reset. Press Start to begin again.")
        self.progress_label.config(text="Progress: 0%")
        self.save_session_position()

    def back(self):
        self.running = False
        self.cancel_scheduled_reader()
        self._flush_stats_session()
        self.reader.step_back(10)
        self.set_display_text("Went back 10 words. Press Start.")
        self.progress_label.config(text=f"Progress: {self.reader.get_progress()}%")
        self.save_session_position()

    def toggle_play_pause(self, event=None):
        if self.running:
            self.pause()
        else:
            self.start()

    def back_five(self, event=None):
        if not self.reader.has_text():
            return

        self.running = False
        self.cancel_scheduled_reader()
        self._flush_stats_session()

        self.reader.step_back(5)
        self.set_display_text("Went back 5 words.\nPress Start.")
        self.progress_label.config(text=f"Progress: {self.reader.get_progress()}%")
        self.save_session_position()

    def next_chapter(self):
        if not self.current_book:
            return
        if self.current_chapter_index >= len(self.current_book.chapters) - 1:
            return

        self.current_chapter_index += 1
        self.set_current_book(self.current_book, self.current_chapter_index)

    def previous_chapter(self):
        if not self.current_book:
            return
        if self.current_chapter_index <= 0:
            return

        self.current_chapter_index -= 1
        self.set_current_book(self.current_book, self.current_chapter_index)

    def jump_to_chapter(self, chapter_index: int):
        if not self.current_book:
            return
        if not (0 <= chapter_index < len(self.current_book.chapters)):
            return

        self.set_current_book(self.current_book, chapter_index)

    def add_bookmark(self):
        if not self.current_book:
            messagebox.showinfo("No Book", "Load a book first.")
            return

        label = simpledialog.askstring("Bookmark", "Enter a bookmark label (optional):")
        if label is None:
            return

        bookmark = Bookmark(
            book_id=self.current_book.book_id,
            chapter_index=self.current_chapter_index,
            word_index=self.reader.get_index(),
            label=label
        )
        self.bookmark_manager.add_bookmark(bookmark)
        self.refresh_sidebar()
        messagebox.showinfo("Saved", "Bookmark added.")

    def add_to_vocab(self):
        text = self.current_display_text.strip()

        if not text:
            messagebox.showinfo("No Text", "There is no displayed text to save yet.")
            return

        suggested = text
        if len(suggested) > 40:
            suggested = suggested[:40].strip()

        word = simpledialog.askstring(
            "Save to Vocab",
            "Edit the word or phrase to save:",
            initialvalue=suggested
        )

        if word is None:
            return

        chapter_title = ""
        book_id = ""

        if self.current_book:
            book_id = self.current_book.book_id
            if 0 <= self.current_chapter_index < len(self.current_book.chapters):
                chapter_title = self.current_book.chapters[self.current_chapter_index].title

        self.vocab_manager.add_entry(
            word=word,
            book_id=book_id,
            chapter_title=chapter_title,
            context=text
        )

        messagebox.showinfo("Saved", f"Saved to vocab:\n{word}")


    def get_reader_display_start_index(self) -> int:
        """Return the raw reader index that best represents the text currently on screen.

        Reader.index points to the *next* word to read after a chunk is displayed.
        For overview highlighting, users expect the highlight to mark the chunk they
        are currently seeing, not the next unread word. This method walks backward
        from the next unread index by the number of visible words currently shown.
        """
        if not self.reader.has_text():
            return 0

        if getattr(self, "overview_preview_active", False):
            return self.reader.index

        current_index = self.reader.get_index()
        display_text = (self.current_display_text or "").strip()

        placeholder_messages = {
            "Jumped from overview. Press Start.",
            "Finished chapter!",
            "No text loaded.",
            "Press Start.",
        }

        if not display_text or display_text in placeholder_messages:
            return current_index

        display_words = [
            word for word in Reader()._tokenize_text(display_text)
            if word != Reader.PARAGRAPH_BREAK_TOKEN
        ]

        if not display_words:
            return current_index

        remaining_visible_words = len(display_words)
        candidate_index = current_index

        while candidate_index > 0 and remaining_visible_words > 0:
            candidate_index -= 1
            try:
                if self.reader.words[candidate_index] != Reader.PARAGRAPH_BREAK_TOKEN:
                    remaining_visible_words -= 1
            except IndexError:
                break

        return max(0, candidate_index)

    def jump_to_reader_word_index(self, word_index: int):
        if not self.current_book or not self.reader.has_text():
            return

        self.running = False
        self.cancel_scheduled_reader()
        self._flush_stats_session()

        self.reader.set_index(word_index)
        self.progress_label.config(text=f"Progress: {self.reader.get_progress()}%")

        selected_word = ""

        if self.reader.has_text() and 0 <= word_index < len(self.reader.words):
            selected_word = self.reader.words[word_index]

        if selected_word == Reader.PARAGRAPH_BREAK_TOKEN:
            selected_word = ""

        self.overview_preview_active = True
        self.set_display_text(selected_word or "Press Start.")

        self.save_session_position()
        self.refresh_sidebar()
        self.show_reader_view()
        self.root.after(75, self.focus_reader_view)

    def show_stats_window(self):
        self.show_stats_view()

    def show_vocab_window(self):
        self.show_vocab_view()

    def save_session_position(self):
        if not self.current_book:
            return

        self.session_manager.update(
            current_book_id=self.current_book.book_id,
            current_chapter_index=self.current_chapter_index,
            current_word_index=self.reader.get_index(),
            last_opened_file=self.current_book.file_path
        )
        self.session = self.session_manager.session

    def run_reader(self):
        if not self.running:
            return

        self.overview_preview_active = False

        if self.reader.is_finished():
            self.running = False
            self._flush_stats_session()

            if (
                self.current_book is not None
                and self.current_chapter_index == len(self.current_book.chapters) - 1
            ):
                self.stats_manager.mark_book_finished(self.current_book.book_id)

            self.set_display_text("Finished chapter!")
            self.progress_label.config(text="Progress: 100%")
            self.save_session_position()
            return

        chunk_size = self.chunk_scale.get()
        punctuation_slowdown = self.settings_manager.settings.punctuation_slowdown

        text, multiplier, reading_units = self.reader.get_next_chunk(
            chunk_size=chunk_size,
            punctuation_slowdown=punctuation_slowdown
        )

        milliseconds_per_word = 60000 / self.wpm_scale.get()

        # RSVP-style one-word display tends to feel faster than traditional
        # reading because each word replaces the last immediately. This small
        # comfort factor keeps the selected WPM feeling closer to human-paced
        # reading without changing the reader engine itself.
        comfort_pacing_factor = 1.15
        delay = int(milliseconds_per_word * reading_units * multiplier * comfort_pacing_factor)
        delay = max(delay, 90)

        if text:
            self.set_display_text(text)
            self.progress_label.config(text=f"Progress: {self.reader.get_progress()}%")
            self.session_words_read += max(1, int(round(reading_units)))
            self.save_session_position()

        self.current_after_id = self.root.after(delay, self.run_reader)