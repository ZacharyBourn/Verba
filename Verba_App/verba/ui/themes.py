THEMES = {
    "dark": {
        "bg_color": "#1e1e1e",
        "panel_color": "#111111",
        "text_box_bg": "#2a2a2a",
        "text_color": "#ffffff",
        "subtle_text": "#cfcfcf",
        "border_color": "#333333",
        "sidebar_select": "#3a3a3a",
        "library_card": "#181818",
        "intro_accent": "#8f8f8f",
    },
    "light": {
        "bg_color": "#f4f4f4",
        "panel_color": "#ffffff",
        "text_box_bg": "#ffffff",
        "text_color": "#111111",
        "subtle_text": "#555555",
        "border_color": "#cccccc",
        "sidebar_select": "#d9d9d9",
        "library_card": "#f8f8f8",
        "intro_accent": "#7a7a7a",
    },
    "sepia": {
        "bg_color": "#f1e7d0",
        "panel_color": "#fff6df",
        "text_box_bg": "#fff6df",
        "text_color": "#2a2118",
        "subtle_text": "#6f604e",
        "border_color": "#d5c5a9",
        "sidebar_select": "#e5d4b5",
        "library_card": "#f8edda",
        "intro_accent": "#8a7358",
    },
    "forest": {
        "bg_color": "#17221b",
        "panel_color": "#0f1712",
        "text_box_bg": "#1e3025",
        "text_color": "#f1f5ed",
        "subtle_text": "#bdc8b5",
        "border_color": "#2f4536",
        "sidebar_select": "#36533f",
        "library_card": "#142019",
        "intro_accent": "#93a889",
    },
    "gray": {
        "bg_color": "#262626",
        "panel_color": "#1a1a1a",
        "text_box_bg": "#303030",
        "text_color": "#f2f2f2",
        "subtle_text": "#c2c2c2",
        "border_color": "#4a4a4a",
        "sidebar_select": "#555555",
        "library_card": "#202020",
        "intro_accent": "#a6a6a6",
    },
}

THEME_NAMES = list(THEMES.keys())


def get_theme(name: str) -> dict:
    return THEMES.get(name, THEMES["dark"])
