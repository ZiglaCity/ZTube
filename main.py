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
default_theme_bool = False
download_path = str(Path.home() / "Downloads")
root = tk.Tk()
root.geometry(f"{window_width}x{window_height}")
root.title("Zigla's YouTube Downloader")

with open("api_key.txt", 'r') as key:
    API_KEY = key.read()


def check_connection():
    global status_label
    try:
        response = requests.get('https://www.google.com', timeout=3)
        response.raise_for_status()
        if response.status_code == 200:
            status_label.config(text="Online", fg="green")           
        else:
            status_label.config(text="Offline", fg="red")

    except requests.exceptions.RequestException:
        status_label.config(text="No connection available...", fg="red")

    root.after(5000, check_connection)


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

        stream.download(output_path=download_path)

        messagebox.showinfo("Success", f"Video downloaded successfully to {download_path}")
        
        progress_bar['value'] = 0

    except Exception as e:
        messagebox.showerror("Error", f"Failed to download video: {e}")
        progress_bar['value'] = 0 
        progress_label.config(text=f"{0:.2f}% downloaded")


def select_save_location():
    global save_path, download_folder_entry, path, download_path
    save_path = filedialog.askdirectory()
    download_folder_entry.config(state="normal")
    path.set("")
    path.set(save_path)
    download_path  = save_path
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


def create_back_button(parent):
    back_button = tk.Button(parent, text="⬅", command=backToMain)
    back_button.pack(anchor="nw" , side='left')
    # return back_button


def set_theme():
    global theme_var, default_theme_bool
    print(theme_var.get())
    if theme_var.get():
        default_theme_bool = True
        root.config(bg='#333333')
        print("Dark set_theme applied")
        # apply_dark_theme()
    else:
        default_theme_bool = False
        root.config(bg="#f0f0f0")
        print("Light set_theme applied")
        # apply_light_theme()
    return     


def save_settings():
    pass


def create_gui():
    global search_entry, status_label, root

    search_frame = tk.Frame(root, pady=20)
    search_frame.pack(fill="x", padx=20)

    search_frame.columnconfigure(0, weight=0) 
    search_frame.columnconfigure(1, weight=1) 
    search_frame.columnconfigure(2, weight=0)

    search_button = tk.Button(
        search_frame,
        text="Search",
        command=update_suggestions
    )
    search_button.grid(row=0, column=0, ipadx=10)

    search_entry = tk.Entry(search_frame, width=50)
    search_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0), ipady=5)
    add_placeholder(search_entry, "Input video URL or title...")

    settings_button = tk.Button(
        search_frame,
        text="⚙️",
        command=openSettings
    )
    settings_button.grid(row=0, column=2, padx=(10, 0), ipadx=5)

    status_label = tk.Label(
        root,
        text="Checking connection..."
    )
    status_label.pack(side="bottom", pady=10)
        


def openSettings():
    for widget in root.winfo_children():
        widget.destroy()

    root.title("ZTube - Settings")

    global download_folder_entry, download_path, path, theme_var

    main_frame = tk.Frame(root, bg="#f7f7f7")
    main_frame.pack(fill=tk.BOTH, padx=20, pady=20)

    top_frame = tk.Frame(main_frame, bg="#f7f7f7")
    top_frame.pack(fill=tk.X)
    create_back_button(top_frame)

    header_label = tk.Label(top_frame, text="Settings", font=("Arial", 18, "bold"), bg="#f7f7f7", fg="#333")
    header_label.pack(side='top', pady=8)

    theme_frame = tk.LabelFrame(main_frame, text="Theme", font=("Arial", 12, "bold"), padx=10, pady=10, bg="#f7f7f7")
    theme_frame.pack(fill=tk.X, pady=(13, 8))

    theme_var = tk.BooleanVar()
    theme_var.set(default_theme_bool)

    dark_label = tk.Label(theme_frame, text="Dark Mode", font=("Arial", 12), bg="#f7f7f7")
    dark_label.pack(side="left", padx=10)

    theme_checkbutton = tk.Checkbutton(theme_frame, variable=theme_var, command=set_theme, bg="#f7f7f7")
    theme_checkbutton.pack(side="right")

    directory_frame = tk.LabelFrame(main_frame, text="Default Directory", font=("Arial", 12, "bold"), padx=10, pady=10, bg="#f7f7f7")
    directory_frame.pack(fill=tk.X, pady=(13, 8))

    path = tk.StringVar()
    path.set(download_path)

    download_folder_button = tk.Button(directory_frame, text="Select Folder", command=select_save_location, font=("Arial", 10), bg="#4CAF50", fg="white")
    download_folder_button.pack(side="left", padx=5)

    download_folder_entry = tk.Entry(directory_frame, textvariable=path, width=40, state='readonly', font=("Arial", 10))
    download_folder_entry.pack(side="left", padx=5)

    about_frame = tk.LabelFrame(main_frame, text="About the App", font=("Arial", 12, "bold"), padx=10, pady=10, bg="#f7f7f7")
    about_frame.pack(fill=tk.X, pady=(15, 10))

    about_app_text = tk.Label(
        about_frame,
        text="ZTube is a simple and intuitive YouTube video downloader. It allows users to search, preview, and download videos directly from YouTube. "
             "With features like quality selection, progress tracking, and more, ZTube makes downloading content seamless and efficient.",
        justify="left", wraplength=400, font=("Arial", 10), bg="#f7f7f7"
    )
    about_app_text.pack(anchor="w")

    author_frame = tk.LabelFrame(main_frame, text="About the Author", font=("Arial", 12, "bold"), padx=10, pady=10, bg="#f7f7f7")
    author_frame.pack(fill=tk.X, pady=(15, 10))

    about_author_text = tk.Label(
        author_frame,
        text="Zigla City\nA passionate developer exploring tech, Programming, Cybersecurity and AI. Zigla is enthusiastic about creating innovative solutions that simplify everyday tasks. "
             "My expertise spans Python development, GUI design, and AI integration.",
        justify="left", wraplength=400, font=("Arial", 10), bg="#f7f7f7"
    )
    about_author_text.pack(anchor="w")

    contact_frame = tk.LabelFrame(main_frame, text="Contact the Developer", font=("Arial", 12, "bold"), padx=10, pady=10, bg="#f7f7f7")
    contact_frame.pack(fill=tk.X, pady=(15, 10))

    def open_link(url):
        import webbrowser
        webbrowser.open_new(url)

    github_link = tk.Label(contact_frame, text="GitHub", fg="blue", cursor="hand2", font=("Arial", 10), bg="#f7f7f7")
    github_link.pack(side="left", padx=10)
    github_link.bind("<Button-1>", lambda e: open_link("https://github.com/ziglacity"))

    linkedin_link = tk.Label(contact_frame, text="LinkedIn", fg="blue", cursor="hand2", font=("Arial", 10), bg="#f7f7f7")
    linkedin_link.pack(side="left", padx=10)
    linkedin_link.bind("<Button-1>", lambda e: open_link("https://linkedin.com/in/ziglacity"))

    email_link = tk.Label(contact_frame, text="Email", fg="blue", cursor="hand2", font=("Arial", 10), bg="#f7f7f7")
    email_link.pack(side="left", padx=10)
    email_link.bind("<Button-1>", lambda e: open_link("mailto:ziglacity@gmail.com"))

    save_button = tk.Button(main_frame, text="Save Settings", command=save_settings, font=("Arial", 12), bg="#4CAF50", fg="white")
    save_button.pack(side="bottom", pady=10)



def openSearchedResults(searched):
    for widget in root.winfo_children():
        widget.destroy()
    
    root.title("Ztube-Search Result")

    global download_folder_entry, progress_label, canvas,status_label,canvas, theme_var, select_video,progress_bar, path,canvas, quality_combobox, search_entry

    def select_video(event = None):
        global url
        selection = "canvas.curselection()"
        if selection:
            index = selection[0]
            url = video_urls[index]
            
        return url

    top_frame = tk.Frame(root)
    top_frame.pack(fill=tk.BOTH)

    create_back_button(top_frame)

    searched_label = tk.Label(top_frame,text=f"Searched result for: {searched}")
    searched_label.pack(side='top')

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
    download_frame.pack(pady=5, fill=tk.BOTH)

    resolution_frame = tk.Frame(download_frame)
    resolution_frame.pack(side="top", padx=20)

    resolution_label = tk.Label(resolution_frame, text="Quality")
    resolution_label.pack(side="left")
    
    quality_combobox = ttk.Combobox(resolution_frame, width=20)
    quality_combobox.pack(side='right')

    download_button = tk.Button(download_frame, text="DOWNLOAD", command=download)
    download_button.pack(side="top", padx=50)

    progress_bar = ttk.Progressbar(root, orient='horizontal', length=300, mode='determinate')
    progress_bar.pack(pady=10)

    progress_label = tk.Label(root, text="0.00% downloaded")
    progress_label.pack()



def backToMain():
    for widget in root.winfo_children():
        widget.destroy()      
    create_gui()




create_gui()
root.mainloop()
check_connection()
