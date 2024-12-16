import tkinter as tk
from tkinter import filedialog
from tkinter import ttk, messagebox
from googleapiclient.discovery import build


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