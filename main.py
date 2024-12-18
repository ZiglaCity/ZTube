import tkinter as tk
from tkinter import filedialog
from tkinter import ttk, messagebox
from googleapiclient.discovery import build
from pytubefix import YouTube
from io import BytesIO
import requests
from PIL import Image, ImageTk
from pathlib import Path


window_height = 700
window_width = 650
video_urls = []
download_path = str(Path.home() / "Downloads")

with open("api_key.txt", 'r') as key:
    API_KEY = key.read()

def search_videos(query):
    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        request = youtube.search().list(
            q=query,
            part='snippet',
            type='video',
            maxResults=10
        )
        response = request.execute()
        print(f"response found: {response}")
        return [{'title': item['snippet']['title'], 
                'videoId': item['id']['videoId'], 
                'thumbnail': item['snippet']['thumbnails']['default']['url']} 
                for item in response['items']]
    except Exception as e:
        print(e)
        messagebox.showinfo("Sorry!", "Failed to connect!")
        return 


def update_suggestions():
    query = search_entry.get()

    if query:
        videos = search_videos(query)
        print(f"videos found are: {videos}")
        if not videos:
            return
        openSearchedResults(query)
        canvas.delete("all") 
        video_urls.clear()

        y_position = 10
        images = [] 

        def apply_selection_style(canvas, selected_tag):
            for index in range(len(videos)):
                text_tag = f"text_{index}"
                if theme_var.get():    
                    canvas.itemconfig(text_tag, font=("Helvetica", 10), fill="white")
                else:
                    canvas.itemconfig(text_tag, font=("Helvetica", 10), fill="black")

            canvas.itemconfig(selected_tag, font=("Helvetica", 10, "bold"), fill="blue")

        for index, video in enumerate(videos):
            video_id = video['videoId']
            video_url = f"https://www.youtube.com/watch?v={video_id}" 
            video_urls.append(video_url)  
            thumbnail_url = video['thumbnail']
            response = requests.get(thumbnail_url)

            if response.status_code == 200:
                img_data = Image.open(BytesIO(response.content))
                img_data = img_data.resize((120, 90), Image.Resampling.LANCZOS)  # Resize thumbnail
                img = ImageTk.PhotoImage(img_data)
                images.append(img)  

                image_item = canvas.create_image(10, y_position, anchor=tk.NW, image=img)
                text_item = canvas.create_text(140, y_position + 30, anchor=tk.NW, text=video['title'], font=("Helvetica", 10), fill="black")

                image_tag = f"image_{index}"
                text_tag = f"text_{index}"

                canvas.itemconfig(image_item, tags=image_tag)
                canvas.itemconfig(text_item, tags=text_tag)

                canvas.tag_bind(image_tag, "<Button-1>", lambda e, url=video_url, tag=text_tag: [on_video_click(url), apply_selection_style(canvas, tag)])
                canvas.tag_bind(text_tag, "<Button-1>", lambda e, url=video_url, tag=text_tag: [on_video_click(url), apply_selection_style(canvas, tag)])

                y_position += 100

            else:
                print(f"Failed to load image from {thumbnail_url}")
    else:
        return messagebox.showinfo("Error", "Please input to search!")
    canvas.image_list = images

    canvas.config(scrollregion=canvas.bbox("all"))


def on_video_click(url):
    global selected_video_url
    selected_video_url = url    
    update_quality_options(url)


def update_quality_options(url):
    try:
        if not url:
            raise ValueError("No video URL provided.")
        yt = YouTube(url)
        streams = yt.streams.filter(progressive=True, file_extension='mp4')

        if not streams:
            raise ValueError("No available streams found.")

        quality_options = [f"{stream.resolution} - {stream.filesize // (1024 * 1024)} MB" for stream in streams]
        quality_combobox['values'] = quality_options

        if quality_options:
            quality_combobox.current(0)
        else:
            raise ValueError("No quality options available.")

    except Exception as e:
        messagebox.showerror("Error", str(e))


def download():
    global selected_video_url, path, quality_combobox, progress_bar, root

    try:
        selected_quality = quality_combobox.get()
        if not selected_quality:
            raise ValueError("No quality selected.")

        resolution = selected_quality.split(" - ")[0]
        url = selected_video_url 

        if not url:
            raise ValueError("No video URL selected.")

        if progress_bar is None:
            progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
            progress_bar.pack(pady=10)
        else:
            progress_bar['value'] = 0

        yt = YouTube(url, on_progress_callback=on_progress)

        # Find the stream that matches the selected resolution
        stream = yt.streams.filter(res=resolution, progressive=True, file_extension='mp4').first()
        if not stream:
            raise ValueError(f"No stream found for resolution {resolution}.")

        path = download_folder_entry.get()
        if path:
            download_path = str(path)
        stream.download(output_path=download_path)

        messagebox.showinfo("Success", f"Video downloaded successfully to {download_path}")
        
        progress_bar['value'] = 0

    except Exception as e:
        messagebox.showerror("Error", f"Failed to download video: {e}")
        progress_bar['value'] = 0 
        progress_label.config(text=f"{0:.2f}% downloaded")


def select_save_location():
    global save_path, download_folder_entry, path 
    save_path = filedialog.askdirectory()
    download_folder_entry.config(state="normal")
    path.set("")
    path.set(save_path)
    download_folder_entry.config(state='readonly')
    return path

def on_progress(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage = (bytes_downloaded / total_size) * 100

    progress_bar['value'] = percentage
    progress_label.config(text=f"{percentage:.2f}% downloaded")
    root.update_idletasks()


def add_placeholder(entry, placeholder_text):
    entry.insert(0, placeholder_text)
    entry.config(fg='grey') 

    def on_focus_in(event):
        if entry.get() == placeholder_text:
            entry.delete(0, tk.END)
            entry.config(fg='black')

    def on_focus_out(event):
        if not entry.get().strip():  
            entry.insert(0, placeholder_text)
            entry.config(fg='grey')

    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)


def create_back_button(parent, command):
    back_button = tk.Button(parent, text="⬅ Back", command=command)
    back_button.pack(anchor="nw", padx=10, pady=10)
    return back_button

def create_gui():
    global root
    root = tk.Tk()
    root.geometry(f"{window_width}x{window_height}")
    root.title("Zigla's YouTube Downloader")

    global download_folder_entry, canvas,status_label,canvas, theme_var, select_video,progress_bar, path,canvas, quality_combobox, search_entry
 
    
    search_frame = tk.Frame(root)
    search_frame.pack(fill="x", padx=10, pady=10)

    search_frame.columnconfigure(0, weight=1)  
    search_frame.columnconfigure(1, weight=0)

    search_button = tk.Button(search_frame, text="Search", command=update_suggestions)
    search_button.grid(row=0, column=0, sticky="w")

    search_entry = tk.Entry(search_frame, width=80)
    search_entry.grid(row=0, column=0, sticky="ew", padx=(50, 0))  # Adjust padding for alignment

    settings_button = tk.Button(search_frame, text="⚙️", command=openSettings)
    settings_button.grid(row=0, column=1, sticky="e", padx=5)

    mode_frame = tk.Frame(root, width=2)
    mode_frame.pack(side="left")

    status_label = tk.Label(root, text="No connection available...", font=('Helvetica', 12))
    status_label.pack(side="bottom")

    theme_frame = tk.Frame(root)
    theme_frame.pack(side="right")

    theme_var = tk.BooleanVar()

    theme_label = tk.Label(theme_frame, text="Dark")
    theme_label.pack(side="left")

    theme_checkbutton = tk.Checkbutton(theme_frame, variable=theme_var)
    theme_checkbutton.pack(side="left")
        



    add_placeholder(search_entry, "Input video url or title...")


    def select_video(event = None):
        global url
        selection = "canvas.curselection()"
        if selection:
            index = selection[0]
            url = video_urls[index]
            
        return url
        
    
    root.mainloop()


def openSettings():
    for widget in root.winfo_children():
        widget.destroy()

    global download_folder_entry, download_path, path

    def returnToMain():
        print("Returning to main page...")

    create_back_button(root, returnToMain)

    header_label = tk.Label(root, text="Settings")
    header_label.pack()

    theme_label = tk.Label(root, text="Theme:")
    theme_label.pack(anchor="w")

    theme_var = tk.StringVar(value="Light")
    theme_frame = tk.Frame(root)
    theme_frame.pack(anchor="w")

    light_theme = tk.Radiobutton(theme_frame, text="Light", variable=theme_var, value="Light")
    dark_theme = tk.Radiobutton(theme_frame, text="Dark", variable=theme_var, value="Dark")
    light_theme.pack(side="left")
    dark_theme.pack(side="left")

    directory_label = tk.Label(root, text="Default Directory:")
    directory_label.pack(anchor="w")

    download_frame = tk.Frame(root)
    download_frame.pack(anchor="w")

    path = tk.StringVar()
    path.set(download_path)

    download_folder_button = tk.Button(download_frame, text="Save", command=select_save_location)
    download_folder_button.pack(side="left")

    download_folder_entry = tk.Entry(download_frame, textvariable=path, width=40, state='readonly')
    download_folder_entry.pack(side="left")

    about_label = tk.Label(root, text="About the Author:")
    about_label.pack(anchor="w")

    about_text = tk.Label(
        root,
        text="Zigla City\nA passionate developer exploring tech, programming, and AI.",
        justify="left"
    )
    about_text.pack(anchor="w")

    def save_settings():
        print(f"Theme: {theme_var.get()}")
        print(f"Default Directory: {download_folder_entry.get()}")

    save_button = tk.Button(root, text="Save Settings", command=save_settings)
    save_button.pack()




def openSearchedResults(searched):
    for widget in root.winfo_children():
        widget.destroy()

    global download_folder_entry, progress_label, canvas,status_label,canvas, theme_var, select_video,progress_bar, path,canvas, quality_combobox, search_entry

    def select_video(event = None):
        global url
        selection = "canvas.curselection()"
        if selection:
            index = selection[0]
            url = video_urls[index]
            
        return url
    
    searched_label = tk.Label(text=f"Searched result for: {searched}")
    searched_label.pack()

    suggestion_frame = tk.Frame(root, height=450, width=window_width)
    suggestion_frame.pack(pady=10, fill=None, expand=False)
    suggestion_frame.pack_propagate(False)

    canvas = tk.Canvas(suggestion_frame, height=300, width=window_width - 20)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(suggestion_frame, orient=tk.VERTICAL, command=canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    inner_frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=inner_frame, anchor='nw')


    download_frame = tk.Frame(root)
    download_frame.pack(pady=5)

    resolution_frame = tk.Frame(download_frame)
    resolution_frame.pack(side="left", padx=20)

    resolution_label = tk.Label(resolution_frame, text="Quality")
    resolution_label.pack(side="left")
    
    quality_combobox = ttk.Combobox(resolution_frame, width=20)
    quality_combobox.pack(side='right')

    download_settings_frame = tk.Frame(download_frame)
    download_settings_frame.pack(side="right", padx=25)

    download_folder_button = tk.Button(download_settings_frame, text="💾 SAVE")
    download_folder_button.pack(side="left")

    path = tk.StringVar()
    path.set(download_path)

    download_folder_entry = tk.Entry(download_settings_frame, textvariable=path, width=25, state='readonly') 
    download_folder_entry.pack(side="right")

    download_button = tk.Button(root, text="DOWNLOAD", command=download)
    download_button.pack(pady=20)

    progress_bar = ttk.Progressbar(root, orient='horizontal', length=300, mode='determinate')
    progress_bar.pack(pady=10)

    progress_label = tk.Label(root, text="0.00% downloaded")
    progress_label.pack()

create_gui()
