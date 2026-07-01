from __future__ import annotations

import logging
import threading
import time
import tkinter as tk
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import requests
from PIL import Image, ImageTk

from .config import (
    API_KEY_ENV_VAR,
    AppConfig,
    UserSettings,
    load_config,
    save_user_settings,
)
from .services.downloader import (
    PoTokenPair,
    YouTubeBotBlockedError,
    YouTubeNetworkError,
    YouTubeVideoUnavailableError,
    download_video,
    get_quality_options,
)
from .services.youtube_search import YouTubeSearchError, resolve_videos
from .ui.themes import Theme, get_theme
from .ui.themes import apply_theme as apply_root_theme

WINDOW_HEIGHT = 700
WINDOW_WIDTH = 650
PLACEHOLDER_TEXT = "Input video URL or title..."
SEARCH_RESULT_LIMIT = 25
THUMBNAIL_WIDTH = 120
THUMBNAIL_HEIGHT = 90
RESULT_ROW_HEIGHT = 112
logger = logging.getLogger(__name__)

root: tk.Tk
config: AppConfig
video_urls: list[str] = []
thumbnail_cache: dict[str, bytes] = {}


@dataclass
class AppState:
    download_path: Path
    selected_video_url: str | None = None
    selected_video_title: str | None = None
    theme_mode: str = "light"
    dark_theme_enabled: bool = False
    current_screen: str = "create_gui"
    connection_status: str = "Checking connection..."
    is_downloading: bool = False
    is_searching: bool = False


state = AppState(download_path=Path.home() / "Downloads")


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def create_root() -> tk.Tk:
    app_root = tk.Tk()
    screen_width = app_root.winfo_screenwidth()
    x_position = int((screen_width / 2) - (WINDOW_WIDTH / 2))
    y_position = 20
    app_root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x_position}+{y_position}")
    app_root.title("ZTube")
    return app_root


def set_theme() -> None:
    if theme_var.get():
        state.theme_mode = "dark"
        state.dark_theme_enabled = True
    else:
        state.theme_mode = "light"
        state.dark_theme_enabled = False
    apply_theme(state.theme_mode)


def apply_theme(mode_name: str) -> None:
    apply_root_theme(root, mode_name)


def apply_search_results_theme(theme: Theme) -> None:
    canvas.configure(
        bg=theme["canvas_bg"],
        highlightthickness=1,
        highlightbackground=theme["border"],
    )
    download_button.configure(
        bg=theme["button_bg"],
        fg=theme["button_fg"],
        activebackground=theme["panel_bg"],
        activeforeground=theme["button_fg"],
        font=("Segoe UI", 10, "bold"),
    )
    searched_label.configure(
        bg=theme["label_bg"],
        fg=theme["label_fg"],
        font=("Segoe UI", 14, "bold"),
    )
    progress_label.configure(
        bg=theme["label_bg"], fg=theme["label_fg"], font=("Segoe UI", 10)
    )
    destination_label.configure(
        bg=theme["panel_bg"], fg=theme["muted_fg"], font=("Segoe UI", 9)
    )
    resolution_label.configure(
        bg=theme["label_bg"],
        fg=theme["label_fg"],
        font=("Segoe UI", 10, "italic"),
    )
    top_frame.configure(bg=theme["bg"])
    suggestion_frame.configure(bg=theme["bg"])
    download_frame.configure(
        bg=theme["panel_bg"],
        highlightthickness=1,
        highlightbackground=theme["border"],
    )
    resolution_frame.configure(bg=theme["panel_bg"])


def apply_modern_styles() -> None:
    theme = get_theme(state.theme_mode)
    button_style = {
        "relief": "flat",
        "borderwidth": 1,
        "highlightthickness": 0,
        "padx": 10,
        "pady": 5,
        "font": ("Helvetica", 10, "bold"),
        "cursor": "hand2",
    }
    entry_style = {
        "relief": "flat",
        "borderwidth": 1,
        "font": ("Helvetica", 10),
        "insertbackground": theme["entry_fg"],
    }
    label_style = {
        "font": ("Helvetica", 10),
        "padx": 5,
        "pady": 5,
    }

    for widget in root.winfo_children():
        apply_modern_widget_styles(widget, button_style, entry_style, label_style)


def apply_modern_widget_styles(
    widget: tk.Widget,
    button_style: dict[str, object],
    entry_style: dict[str, object],
    label_style: dict[str, object],
) -> None:
    if isinstance(widget, tk.Button):
        widget.configure(**button_style)
    elif isinstance(widget, tk.Entry):
        widget.configure(**entry_style)
    elif isinstance(widget, tk.Label):
        widget.configure(**label_style)

    for sub_widget in widget.winfo_children():
        apply_modern_widget_styles(sub_widget, button_style, entry_style, label_style)


def check_connection_thread() -> None:
    while True:
        if state.current_screen == "create_gui":
            try:
                response = requests.get("https://www.google.com", timeout=3)
                response.raise_for_status()
                is_online = response.status_code == 200
            except requests.exceptions.RequestException:
                is_online = False

            root.after(0, lambda online=is_online: update_status(online))

        time.sleep(5)


def update_status(is_online: bool) -> None:
    state.connection_status = "Online" if is_online else "Offline"
    if state.current_screen != "create_gui" or state.is_searching:
        return

    status_color = "green" if is_online else "red"
    status_text = "Online" if is_online else "Offline - check your connection"
    status_label.config(text=status_text, fg=status_color)


def search_videos(query: str) -> list[dict[str, str]]:
    if not config.youtube_api_key:
        raise ValueError(f"Set {API_KEY_ENV_VAR} before searching YouTube.")

    return resolve_videos(
        config.youtube_api_key, query, max_results=SEARCH_RESULT_LIMIT
    )


def update_suggestions() -> None:
    if state.is_searching:
        return

    query = search_entry.get().strip()
    if not query or query == PLACEHOLDER_TEXT:
        messagebox.showinfo("Error", "Please input a search term or video URL.")
        return

    if not config.youtube_api_key:
        messagebox.showerror(
            "Missing API key",
            f"Set {API_KEY_ENV_VAR} before searching YouTube.",
        )
        return

    state.is_searching = True
    search_button.config(text="Searching...", state=tk.DISABLED)
    status_label.config(text="Searching YouTube...", fg="#0078d4")
    threading.Thread(target=search_worker, args=(query,), daemon=True).start()


def search_worker(query: str) -> None:
    try:
        videos = search_videos(query)
    except YouTubeSearchError as error:
        root.after(0, lambda message=str(error): handle_search_error(message))
        return
    except ValueError as error:
        root.after(0, lambda message=str(error): handle_search_error(message))
        return
    except Exception as error:
        logger.exception("Unexpected search failure")
        root.after(
            0,
            lambda message=str(error): handle_search_error(
                f"Unexpected search failure: {message}"
            ),
        )
        return

    root.after(0, lambda: render_search_results(query, videos))


def handle_search_error(message: str) -> None:
    reset_search_state()
    messagebox.showinfo("Sorry!", f"Failed to search YouTube.\nError: {message}")


def reset_search_state() -> None:
    state.is_searching = False
    if state.current_screen == "create_gui":
        search_button.config(text="Search", state=tk.NORMAL)
        status_color = "green" if state.connection_status == "Online" else "red"
        status_label.config(text=state.connection_status, fg=status_color)


def render_search_results(query: str, videos: list[dict[str, str]]) -> None:
    state.is_searching = False
    if not videos:
        open_searched_results(query)
        show_results_empty_state("No videos found for that search.")
        return

    open_searched_results(query)
    canvas.delete("all")
    video_urls.clear()

    y_position = 12
    canvas.image_list = []

    def apply_selection_style(selected_tag: str) -> None:
        for index in range(len(videos)):
            text_tag = f"text_{index}"
            text_fill = get_theme(state.theme_mode)["label_fg"]
            canvas.itemconfig(text_tag, font=("Helvetica", 10), fill=text_fill)

        canvas.itemconfig(
            selected_tag,
            font=("Helvetica", 10, "bold"),
            fill=get_theme(state.theme_mode)["selection"],
        )

    for index, video in enumerate(videos):
        video_id = video["videoId"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        video_urls.append(video_url)
        thumbnail_url = video["thumbnail"]

        image_tag = f"image_{index}"
        text_tag = f"text_{index}"
        border_tag = f"border_{index}"
        draw_thumbnail_placeholder(image_tag, y_position, "Loading")
        threading.Thread(
            target=thumbnail_worker,
            args=(thumbnail_url, image_tag, y_position),
            daemon=True,
        ).start()

        canvas.create_rectangle(
            8,
            y_position - 2,
            132,
            y_position + 92,
            outline="",
            width=2,
            tags=border_tag,
        )
        title_fill = get_theme(state.theme_mode)["label_fg"]
        text_item = canvas.create_text(
            152,
            y_position + 30,
            anchor=tk.NW,
            text=video["title"],
            font=("Helvetica", 10),
            fill=title_fill,
            width=430,
        )

        canvas.itemconfig(text_item, tags=text_tag)

        def handle_video_click(
            video_url=video_url, tag=text_tag, border=border_tag, title=video["title"]
        ):
            on_video_click(video_url, title)
            apply_selection_style(tag)
            for item_index in range(len(videos)):
                canvas.itemconfig(f"border_{item_index}", outline="", width=2)
            canvas.itemconfig(
                border, outline=get_theme(state.theme_mode)["selection"], width=3
            )
            canvas.tag_raise(border)

        canvas.tag_bind(
            image_tag,
            "<Button-1>",
            lambda _event, callback=handle_video_click: callback(),
        )
        canvas.tag_bind(
            text_tag,
            "<Button-1>",
            lambda _event, callback=handle_video_click: callback(),
        )
        y_position += RESULT_ROW_HEIGHT

    canvas.config(scrollregion=canvas.bbox("all"))


def load_thumbnail(thumbnail_url: str) -> bytes:
    if thumbnail_url not in thumbnail_cache:
        response = requests.get(thumbnail_url, timeout=5)
        response.raise_for_status()
        thumbnail_cache[thumbnail_url] = response.content

    return thumbnail_cache[thumbnail_url]


def draw_thumbnail_placeholder(tag: str, y_position: int, label: str) -> None:
    theme = get_theme(state.theme_mode)
    canvas.create_rectangle(
        10,
        y_position,
        10 + THUMBNAIL_WIDTH,
        y_position + THUMBNAIL_HEIGHT,
        fill=theme["placeholder_bg"],
        outline=theme["border"],
        tags=tag,
    )
    canvas.create_text(
        10 + THUMBNAIL_WIDTH / 2,
        y_position + THUMBNAIL_HEIGHT / 2,
        text=label,
        fill=theme["placeholder_fg"],
        font=("Segoe UI", 9),
        justify="center",
        tags=tag,
    )


def thumbnail_worker(thumbnail_url: str, image_tag: str, y_position: int) -> None:
    try:
        thumbnail_data = load_thumbnail(thumbnail_url)
    except (requests.exceptions.RequestException, OSError):
        root.after(
            0,
            lambda tag=image_tag, y=y_position: replace_thumbnail_with_error(tag, y),
        )
        return

    root.after(
        0,
        lambda data=thumbnail_data, tag=image_tag, y=y_position: apply_thumbnail(
            data, tag, y
        ),
    )


def replace_thumbnail_with_error(image_tag: str, y_position: int) -> None:
    if state.current_screen != "open_searched_results":
        return

    canvas.delete(image_tag)
    draw_thumbnail_placeholder(image_tag, y_position, "Thumbnail\nunavailable")


def apply_thumbnail(thumbnail_data: bytes, image_tag: str, y_position: int) -> None:
    if state.current_screen != "open_searched_results":
        return

    try:
        img_data = Image.open(BytesIO(thumbnail_data))
        img_data = img_data.resize(
            (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.Resampling.LANCZOS
        )
        img = ImageTk.PhotoImage(img_data)
    except OSError:
        replace_thumbnail_with_error(image_tag, y_position)
        return

    canvas.delete(image_tag)
    canvas.create_image(10, y_position, anchor=tk.NW, image=img, tags=image_tag)
    canvas.image_list.append(img)
    result_index = image_tag.rsplit("_", 1)[-1]
    canvas.tag_raise(f"border_{result_index}")


def on_video_click(url: str, title: str) -> None:
    state.selected_video_url = url
    state.selected_video_title = title
    quality_combobox.set("Loading qualities...")
    quality_combobox["values"] = []
    download_button.config(state=tk.DISABLED)
    update_quality_options(url)


def update_quality_options(url: str) -> None:
    threading.Thread(target=quality_worker, args=(url,), daemon=True).start()


def quality_worker(url: str) -> None:
    try:
        if not url:
            raise ValueError("No video URL provided.")
        quality_options = get_quality_options(url, get_po_token_pair())
        if not quality_options:
            raise ValueError("No quality options available.")
    except (
        YouTubeBotBlockedError,
        YouTubeVideoUnavailableError,
        YouTubeNetworkError,
        ValueError,
    ) as error:
        root.after(0, lambda message=str(error): handle_quality_error(url, message))
    except Exception as error:
        logger.exception("Unexpected quality lookup failure")
        root.after(0, lambda message=str(error): handle_quality_error(url, message))
        return

    root.after(
        0, lambda options=quality_options: handle_quality_options_loaded(url, options)
    )


def handle_quality_options_loaded(url: str, quality_options: list[str]) -> None:
    if state.selected_video_url != url:
        return

    quality_combobox["values"] = quality_options
    quality_combobox.current(0)
    download_button.config(text="Download", state=tk.NORMAL)


def handle_quality_error(url: str, message: str) -> None:
    if state.selected_video_url != url:
        return

    quality_combobox["values"] = []
    quality_combobox.set("Unavailable")
    download_button.config(state=tk.DISABLED)
    messagebox.showerror("Quality unavailable", message)


def get_po_token_pair() -> PoTokenPair | None:
    if config.youtube_visitor_data and config.youtube_po_token:
        return config.youtube_visitor_data, config.youtube_po_token
    return None


def download() -> None:
    if state.is_downloading:
        return

    state.is_downloading = True
    download_button.config(text="Downloading...", state=tk.DISABLED)
    progress_label.config(text="Downloading...")
    progress_bar.config(mode="indeterminate", value=0)
    progress_bar.start(12)
    threading.Thread(target=threaded_download, daemon=True).start()


def threaded_download() -> None:
    try:
        selected_quality = quality_combobox.get()
        if not selected_quality:
            raise ValueError("No quality selected.")

        resolution = selected_quality.split(" - ")[-2]
        url = state.selected_video_url

        if not url:
            raise ValueError("No video URL selected.")

        output_path = state.download_path

        root.after(0, lambda: progress_bar.config(value=0))

        download_video(url, resolution, output_path, on_progress, get_po_token_pair())
        root.after(
            0,
            lambda: messagebox.showinfo(
                "Success",
                f"Video downloaded successfully to {output_path}",
            ),
        )
        root.after(0, reset_download_state)

    except YouTubeBotBlockedError as error:
        root.after(
            0,
            lambda message=str(error): messagebox.showerror(
                "YouTube blocked this request",
                message,
            ),
        )
        root.after(0, reset_download_state)
    except YouTubeVideoUnavailableError as error:
        root.after(
            0,
            lambda message=str(error): messagebox.showwarning(
                "Video unavailable",
                message,
            ),
        )
        root.after(0, reset_download_state)
    except YouTubeNetworkError as error:
        root.after(
            0,
            lambda message=str(error): messagebox.showerror(
                "YouTube connection failed",
                message,
            ),
        )
        root.after(0, reset_download_state)
    except Exception as error:
        logger.exception("Unexpected download failure")
        root.after(
            0,
            lambda message=str(error): messagebox.showerror(
                "Error",
                f"Failed to download video: {message}",
            ),
        )
        root.after(0, reset_download_state)


def reset_download_state() -> None:
    progress_bar.stop()
    progress_bar.config(mode="determinate")
    progress_bar.config(value=0)
    progress_label.config(text="0.00% downloaded")
    download_button.config(text="Download", state=tk.NORMAL)
    state.is_downloading = False


def select_save_location() -> tk.StringVar:
    save_path = filedialog.askdirectory()
    if not save_path:
        return path

    state.download_path = Path(save_path)
    download_folder_entry.config(state="normal")
    path.set(save_path)
    download_folder_entry.config(state="readonly")
    if "destination_label" in globals():
        destination_label.config(text=f"Destination: {state.download_path}")
    return path


def on_progress(stream, chunk, bytes_remaining: int) -> None:
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage = (bytes_downloaded / total_size) * 100
    root.after(0, lambda: update_progress(percentage))


def update_progress(percentage: float) -> None:
    progress_bar.stop()
    progress_bar.config(mode="determinate")
    progress_bar["value"] = percentage
    progress_label.config(text=f"{percentage:.2f}% downloaded")


def add_placeholder(entry: tk.Entry, placeholder_text: str) -> None:
    theme = get_theme(state.theme_mode)
    entry.insert(0, placeholder_text)
    entry.config(fg=theme["muted_fg"], insertbackground=theme["entry_fg"])

    def on_focus_in(_event) -> None:
        if entry.get() == placeholder_text:
            entry.delete(0, tk.END)
        entry.config(fg=theme["entry_fg"], insertbackground=theme["entry_fg"])

    def on_focus_out(_event) -> None:
        if not entry.get().strip():
            entry.insert(0, placeholder_text)
            entry.config(fg=theme["muted_fg"])
        else:
            entry.config(fg=theme["entry_fg"])

    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)


def create_back_button(parent: tk.Widget) -> None:
    back_button = tk.Button(parent, text="Back", command=back_to_main)
    back_button.pack(anchor="nw", side="left", padx=(0, 12), pady=4)


def save_settings() -> None:
    save_user_settings(
        UserSettings(
            download_path=state.download_path,
            dark_theme_enabled=state.dark_theme_enabled,
        )
    )
    messagebox.showinfo("Settings", "Settings saved.")


def create_gui() -> None:
    global search_button, search_entry, status_label
    state.current_screen = "create_gui"
    root.title("ZTube")

    search_frame = tk.Frame(root, pady=24)
    search_frame.pack(fill="x", padx=20)
    search_frame.columnconfigure(0, weight=0)
    search_frame.columnconfigure(1, weight=1)
    search_frame.columnconfigure(2, weight=0)

    search_button = tk.Button(search_frame, text="Search", command=update_suggestions)
    search_button.grid(row=0, column=0, ipadx=10)

    search_entry = tk.Entry(search_frame, width=50)
    search_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0), ipady=5)
    add_placeholder(search_entry, PLACEHOLDER_TEXT)
    search_entry.bind("<Return>", lambda _event: update_suggestions())

    settings_button = tk.Button(search_frame, text="Settings", command=open_settings)
    settings_button.grid(row=0, column=2, padx=(10, 0), ipadx=5)

    start_label = tk.Label(
        root,
        text=(
            "Search for a video or paste a YouTube link to begin."
        ),
        wraplength=420,
        justify="center",
        font=("Segoe UI", 12),
    )
    start_label.pack(expand=True)

    status_label = tk.Label(root, text=state.connection_status)
    status_label.pack(side="bottom", pady=10)

    apply_theme(state.theme_mode)
    apply_modern_styles()


def open_settings() -> None:
    global download_folder_entry, path, theme_var
    state.current_screen = "open_settings"
    for widget in root.winfo_children():
        widget.destroy()

    root.title("ZTube - Settings")

    theme = get_theme(state.theme_mode)

    main_frame = tk.Frame(root, bg=theme["bg"])
    main_frame.pack(fill=tk.BOTH, padx=20, pady=20)

    top_frame_local = tk.Frame(main_frame, bg=theme["bg"])
    top_frame_local.pack(fill=tk.X)
    create_back_button(top_frame_local)

    header_label = tk.Label(
        top_frame_local,
        text="Settings",
        font=("Arial", 18, "bold"),
        bg=theme["bg"],
        fg=theme["label_fg"],
    )
    header_label.pack(side="top", pady=2)

    theme_frame = tk.LabelFrame(
        main_frame,
        text="Theme",
        font=("Arial", 12, "bold"),
        padx=10,
        pady=10,
        bg=theme["panel_bg"],
        fg=theme["label_fg"],
    )
    theme_frame.pack(fill=tk.X, pady=(2, 0))

    theme_var = tk.BooleanVar()
    theme_var.set(state.dark_theme_enabled)

    dark_label = tk.Label(
        theme_frame, text="Dark Mode", font=("Arial", 12), bg=theme["panel_bg"]
    )
    dark_label.pack(side="left", padx=10)

    theme_checkbutton = tk.Checkbutton(
        theme_frame, variable=theme_var, command=set_theme, bg=theme["panel_bg"]
    )
    theme_checkbutton.pack(side="right")

    directory_frame = tk.LabelFrame(
        main_frame,
        text="Default Directory",
        font=("Arial", 12, "bold"),
        padx=10,
        pady=10,
        bg=theme["panel_bg"],
        fg=theme["label_fg"],
    )
    directory_frame.pack(fill=tk.X, pady=(3, 1))

    path = tk.StringVar()
    path.set(str(state.download_path))

    download_folder_button = tk.Button(
        directory_frame,
        text="Select Folder",
        command=select_save_location,
        font=("Arial", 10),
        bg=theme["button_bg"],
        fg=theme["button_fg"],
    )
    download_folder_button.pack(side="left", padx=5)

    download_folder_entry = tk.Entry(
        directory_frame,
        textvariable=path,
        width=40,
        state="readonly",
        font=("Arial", 10),
    )
    download_folder_entry.pack(side="left", padx=5)

    about_frame = tk.LabelFrame(
        main_frame,
        text="About the App",
        font=("Arial", 12, "bold"),
        padx=10,
        pady=10,
        bg=theme["panel_bg"],
        fg=theme["label_fg"],
    )
    about_frame.pack(fill=tk.X, pady=(15, 10))

    about_app_text = tk.Label(
        about_frame,
        text=(
            "ZTube\nA simple and intuitive YouTube video downloader. It allows "
            "users to search, preview, and download videos directly from YouTube."
        ),
        justify="center",
        wraplength=400,
        font=("Segoe UI", 10, "italic"),
        bg=theme["panel_bg"],
        fg=theme["muted_fg"],
        padx=10,
        pady=10,
        anchor="center",
    )
    about_app_text.pack(anchor="center")

    save_button = tk.Button(
        main_frame,
        text="Save Settings",
        command=save_settings,
        font=("Arial", 12),
        bg=theme["button_bg"],
        fg=theme["button_fg"],
    )
    save_button.pack(side="bottom", pady=10)

    apply_theme(state.theme_mode)


def open_searched_results(searched: str) -> None:
    global progress_label, download_button, searched_label, resolution_label
    global resolution_frame, top_frame, suggestion_frame, download_frame
    global canvas, progress_bar, quality_combobox
    global destination_label

    state.current_screen = "open_searched_results"

    for widget in root.winfo_children():
        widget.destroy()

    root.title("ZTube - Search Results")

    top_frame = tk.Frame(root)
    top_frame.pack(fill=tk.X, padx=16, pady=(10, 6))

    create_back_button(top_frame)

    searched_label = tk.Label(top_frame, text=f"Searched result for: {searched}")
    searched_label.pack(side="left", fill=tk.X, expand=True)

    suggestion_frame = tk.Frame(root, height=490, width=WINDOW_WIDTH)
    suggestion_frame.pack(padx=16, pady=(0, 6), fill=tk.BOTH, expand=True)
    suggestion_frame.pack_propagate(False)

    canvas = tk.Canvas(suggestion_frame, height=480, width=WINDOW_WIDTH - 20)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(
        suggestion_frame, orient=tk.VERTICAL, command=canvas.yview
    )
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.bind(
        "<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    bind_canvas_scroll(canvas)

    download_frame = tk.Frame(root)
    download_frame.pack(fill=tk.X, padx=16, pady=(0, 8), ipadx=8, ipady=6)

    destination_label = tk.Label(
        download_frame, text=f"Destination: {state.download_path}"
    )
    destination_label.pack(side="top", pady=(0, 4), anchor="center")

    resolution_frame = tk.Frame(download_frame)
    resolution_frame.pack(side="top", padx=20, pady=(0, 4))

    resolution_label = tk.Label(resolution_frame, text="Quality")
    resolution_label.pack(side="left")

    quality_combobox = ttk.Combobox(resolution_frame, width=28, state="readonly")
    quality_combobox.pack(side="right")

    download_button = tk.Button(download_frame, text="Download", command=download)
    download_button.config(state=tk.DISABLED)
    download_button.pack(side="top", pady=(2, 4), anchor="center")

    progress_bar = ttk.Progressbar(
        root, orient="horizontal", length=300, mode="determinate"
    )
    progress_bar.pack(pady=(0, 2))

    progress_label = tk.Label(root, text="0.00% downloaded")
    progress_label.pack(pady=(0, 4))

    apply_search_results_theme(get_theme(state.theme_mode))


def bind_canvas_scroll(target_canvas: tk.Canvas) -> None:
    def on_mousewheel(event) -> str:
        if event.num == 4:
            target_canvas.yview_scroll(-3, "units")
        elif event.num == 5:
            target_canvas.yview_scroll(3, "units")
        else:
            target_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    target_canvas.bind("<MouseWheel>", on_mousewheel)
    target_canvas.bind("<Button-4>", on_mousewheel)
    target_canvas.bind("<Button-5>", on_mousewheel)


def show_results_empty_state(message: str) -> None:
    canvas.delete("all")
    video_urls.clear()
    quality_combobox.set("")
    quality_combobox["values"] = []
    download_button.config(state=tk.DISABLED)
    theme = get_theme(state.theme_mode)
    canvas.create_text(
        (WINDOW_WIDTH - 20) / 2,
        180,
        text=message,
        fill=theme["label_fg"],
        font=("Segoe UI", 12, "bold"),
        width=420,
        justify="center",
    )


def back_to_main() -> None:
    for widget in root.winfo_children():
        widget.destroy()
    create_gui()


def start_app() -> None:
    global root, config, state
    configure_logging()
    config = load_config()
    state = AppState(
        download_path=config.default_download_path,
        theme_mode="dark" if config.dark_theme_enabled else "light",
        dark_theme_enabled=config.dark_theme_enabled,
    )
    root = create_root()
    create_gui()
    online_thread = threading.Thread(target=check_connection_thread, daemon=True)
    online_thread.start()
    root.mainloop()
