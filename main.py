import tkinter as tk
from tkinter import filedialog
from tkinter import ttk, messagebox
from googleapiclient.discovery import build


window_height = 730
window_width = 650
video_urls = []

with open("api_key.txt", 'r') as key:
    API_KEY = key.read()

def search_videos(query):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    request = youtube.search().list(
        q=query,
        part='snippet',
        type='video',
        maxResults=10
    )
    response = request.execute()
    return [{'title': item['snippet']['title'], 
             'videoId': item['id']['videoId'], 
             'thumbnail': item['snippet']['thumbnails']['default']['url']} 
            for item in response['items']]


def create_gui():
    global root
    root = tk.Tk()
    root.geometry(f"{window_width}x{window_height}")
    root.title("Zigla's YouTube Downloader")

    global download_folder_entry, canvas,status_label,canvas, theme_var, select_video,progress_bar, path,canvas, quality_combobox, search_entry
 
    info_frame = tk.Frame(root)
    info_frame.pack(pady=3)

    mode_frame = tk.Frame(info_frame, width=2)
    mode_frame.pack(side="left")

    status_label = tk.Label(mode_frame, text="Checking...", font=('Helvetica', 12))
    status_label.pack(side="left")


    info_label = tk.Label(info_frame, text="Input Video URL/Title")
    info_label.pack(side="left", padx=155)

    theme_frame = tk.Frame(info_frame)
    theme_frame.pack(side="right")

    theme_var = tk.BooleanVar()

    theme_label = tk.Label(theme_frame, text="Dark")
    theme_label.pack(side="left")

    theme_checkbutton = tk.Checkbutton(theme_frame, variable=theme_var)
    theme_checkbutton.pack(side="right")

    search_frame = tk.Frame(root)
    search_frame.pack(pady=5)

    search_button = tk.Button(search_frame, text="🔍")
    search_button.pack(side='left')
    search_entry = tk.Entry(search_frame, width=70)
    search_entry.pack(side="right")


    def select_video(event = None):
        global url
        selection = "canvas.curselection()"
        if selection:
            index = selection[0]
            url = video_urls[index]
            
        return url
        
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
    path.set("")

    download_folder_entry = tk.Entry(download_settings_frame, textvariable=path, width=25, state='readonly') 
    download_folder_entry.pack(side="right")

    download_button = tk.Button(root, text="DOWNLOAD")
    download_button.pack(pady=20)

    progress_bar = ttk.Progressbar(root, orient='horizontal', length=300, mode='determinate')
    progress_bar.pack(pady=10)

    

    root.mainloop()


create_gui()
