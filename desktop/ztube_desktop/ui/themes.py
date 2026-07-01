from __future__ import annotations

import tkinter as tk
from tkinter import ttk

Theme = dict[str, str]


LIGHT_THEME: Theme = {
    "bg": "#f6f7fb",
    "fg": "#17202a",
    "button_bg": "#ffffff",
    "button_fg": "#17202a",
    "entry_bg": "#ffffff",
    "entry_fg": "#17202a",
    "label_bg": "#f6f7fb",
    "label_fg": "#17202a",
    "checkbox_bg": "#f6f7fb",
    "checkbox_fg": "#17202a",
    "canvas_bg": "#ffffff",
    "scrollbar_bg": "#d7dce5",
    "muted_fg": "#667085",
    "accent": "#3f4754",
    "accent_fg": "#ffffff",
    "selection": "#2563eb",
    "panel_bg": "#ffffff",
    "border": "#d9e0ea",
    "placeholder_bg": "#edf1f7",
    "placeholder_fg": "#475467",
}

DARK_THEME: Theme = {
    "bg": "#101828",
    "fg": "#f9fafb",
    "button_bg": "#1d2939",
    "button_fg": "#f9fafb",
    "entry_bg": "#111827",
    "entry_fg": "#f9fafb",
    "label_bg": "#101828",
    "label_fg": "#f9fafb",
    "checkbox_bg": "#101828",
    "checkbox_fg": "#f9fafb",
    "canvas_bg": "#111827",
    "scrollbar_bg": "#344054",
    "muted_fg": "#98a2b3",
    "accent": "#d0d5dd",
    "accent_fg": "#101828",
    "selection": "#60a5fa",
    "panel_bg": "#111827",
    "border": "#344054",
    "placeholder_bg": "#1d2939",
    "placeholder_fg": "#d0d5dd",
}


def get_theme(mode_name: str) -> Theme:
    return DARK_THEME if mode_name == "dark" else LIGHT_THEME


def apply_widget_theme(widget: tk.Widget, theme: Theme) -> None:
    if isinstance(widget, tk.Label):
        if widget.cget("text") in {"GitHub", "LinkedIn", "Email"}:
            widget.configure(bg=theme["label_bg"], fg="blue", font=("Arial", 10))
        else:
            widget.configure(bg=theme["label_bg"], fg=theme["label_fg"])
    elif isinstance(widget, tk.Button):
        widget.configure(
            bg=theme["button_bg"],
            fg=theme["button_fg"],
            activebackground=theme["panel_bg"],
            activeforeground=theme["button_fg"],
        )
    elif isinstance(widget, tk.Checkbutton):
        widget.configure(
            bg=theme["checkbox_bg"],
            fg=theme["checkbox_fg"],
            activebackground=theme["checkbox_bg"],
            activeforeground=theme["checkbox_fg"],
            selectcolor=theme["entry_bg"],
        )
    elif isinstance(widget, tk.Entry):
        widget.configure(
            bg=theme["entry_bg"],
            fg=theme["entry_fg"],
            insertbackground=theme["entry_fg"],
            readonlybackground=theme["entry_bg"],
            disabledbackground=theme["entry_bg"],
            disabledforeground=theme["muted_fg"],
        )
    elif isinstance(widget, tk.LabelFrame):
        widget.configure(
            bg=theme["panel_bg"],
            fg=theme["label_fg"],
            highlightbackground=theme["border"],
        )
    elif isinstance(widget, tk.Frame):
        widget.configure(bg=theme["bg"])

    for child in widget.winfo_children():
        apply_widget_theme(child, theme)


def apply_theme(root: tk.Tk, mode_name: str) -> Theme:
    theme = get_theme(mode_name)
    root.configure(bg=theme["bg"])
    apply_ttk_theme(theme)

    for widget in root.winfo_children():
        apply_widget_theme(widget, theme)

    return theme


def apply_ttk_theme(theme: Theme) -> None:
    style = ttk.Style()
    style.configure(
        "TCombobox",
        fieldbackground=theme["entry_bg"],
        background=theme["entry_bg"],
        foreground=theme["entry_fg"],
        arrowcolor=theme["fg"],
        bordercolor=theme["border"],
        lightcolor=theme["border"],
        darkcolor=theme["border"],
    )
    style.configure(
        "Horizontal.TProgressbar",
        background=theme["accent"],
        troughcolor=theme["bg"],
    )
