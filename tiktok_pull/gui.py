import json
import os
import re
import queue
import tkinter as tk

from dataclasses import dataclass
from threading import Thread
from tkinter import filedialog, ttk

import requests


from . import consts


def get_tiktok_data(path: str = consts.DEFAULT_DATA_PATH) -> dict:
    with open(path, "r", encoding="UTF-8") as fs:
        return json.load(fs)


def get_video_list(data: dict) -> list[dict]:
    video_list = data.get("Video", {}).get("Videos", {}).get("VideoList", [])
    return video_list


def convert_str(text: str) -> str:
    fix_re = re.compile(r"[ \-\(\)\"'_]+")
    fixed = fix_re.sub("_", text)

    return fixed.replace(":", "-")


def get_link(video_obj: dict) -> list[tuple[str, str]]:
    url = video_obj["Link"]
    date = convert_str(video_obj["Date"])
    sound = convert_str(video_obj["Sound"])
    name = f"{date}-{sound}.mp4"
    return url, name


@dataclass
class ErrorDialog:
    message: str
    root: tk.Tk = None
    message_label: tk.Label = None
    ok_button: tk.Button = None

    def __post_init__(self) -> None:
        # Create the main window
        self.root = tk.Tk()
        self.root.title("Error")
        self.root.geometry("300x150")  # Set size of the window

        # Create a Label to display the error message
        self.message_label = tk.Label(self.root, text=self.message, wraplength=280)
        self.message_label.pack(padx=10, pady=10)

        # Create an OK button to close the dialog
        self.ok_button = tk.Button(self.root, text="OK", command=self.ok)
        self.ok_button.pack(pady=10)

    def run(self) -> None:
        # Start the main event loop
        self.root.mainloop()

    def ok(self):
        # Close the dialog
        self.root.destroy()


class DownloadStatusWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Download Status")
        self.geometry("400x200")

        tk.Label(self, text="Current File Progress:").pack(pady=5)
        self.current_progress = ttk.Progressbar(
            self, orient="horizontal", length=300, mode="determinate"
        )
        self.current_progress.pack(pady=5)

        tk.Label(self, text="Overall Progress:").pack(pady=5)
        self.overall_progress = ttk.Progressbar(
            self, orient="horizontal", length=300, mode="determinate"
        )
        self.overall_progress.pack(pady=5)

    def update_current(self, value, max_value):
        self.current_progress["value"] = value
        self.current_progress["maximum"] = max_value

    def update_overall(self, value, max_value):
        self.overall_progress["value"] = value
        self.overall_progress["maximum"] = max_value


@dataclass
class _DownloadStatusWindow:
    root: tk.Tk = None

    overall_label: tk.Label = None
    overall_progress: ttk.Progressbar = None

    current_label: tk.Label = None
    current_progress: ttk.Progressbar = None
    url_data: list[tuple[str, str]] = None

    def __post_init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Download Status")
        self.root.geometry("400x200")

        self.current_label = tk.Label(text="Current File Progress:")
        self.current_label.pack(pady=5)

        self.current_progress = ttk.Progressbar(
            self, orient="horizontal", length=300, mode="determinate"
        )
        self.current_progress.pack(pady=5)

        self.overall_label = tk.Label(text="Overall Progress:")
        self.overall_label.pack(pady=5)

        self.overall_progress = ttk.Progressbar(
            self, orient="horizontal", length=300, mode="determinate"
        )
        self.overall_progress.pack(pady=5)

    def run(self) -> None:
        self.root.mainloop()

    def update_current(self, value, max_value):
        self.current_progress["value"] = value
        self.current_progress["maximum"] = max_value

    def update_overall(self, value, max_value):
        self.overall_progress["value"] = value
        self.overall_progress["maximum"] = max_value

    def download_files(self):
        if not self.url_data:
            return
        num_files = len(self.url_data)
        i = 1
        for url, name in self.url_data:
            # Placeholder for download logic

            response = requests.get(url, stream=True)
            total_size = int(response.headers.get("content-length", 0))
            block_size = 1024

            with open(name, "wb") as f:
                for data in response.iter_content(block_size):
                    f.write(data)
                    self.update_current(f.tell(), total_size)

            self.update_overall(i, num_files)
            i += 1


@dataclass
class FileDownloaderApp:

    root: tk.Tk = None

    entry_frame: tk.Frame = None

    data_frame: tk.Frame = None
    def_data_path: str = ""
    selected_data_path: str = None
    data_path_var: tk.StringVar = None
    data_label: tk.Label = None
    data_entry: tk.Entry = None

    output_frame: tk.Frame = None
    def_output_path: str = ""
    selected_output_path: str = None
    output_path_var: tk.StringVar = None
    output_label: tk.Label = None
    output_entry: tk.Entry = None

    browse_data_button: tk.Button = None
    browse_output_button: tk.Button = None

    submit_button: tk.Button = None
    cancel_button: tk.Button = None
    selected_path: str = None

    progress_queue: queue.Queue = queue.Queue()

    download_status_window: DownloadStatusWindow = None

    def __post_init__(self):
        # Create the main window
        # self.root = tk.Tk()
        self.root.title("TikTok Content Downloader")
        self.root.geometry("500x300")  # Set size of the window

        self.def_data_path = os.path.abspath(consts.DEFAULT_DATA_PATH)
        self.def_output_path = os.path.dirname(self.def_data_path)

        if not os.path.exists(self.def_data_path):
            self.def_data_path = ""

        if not os.path.exists(self.def_output_path):
            self.def_output_path = ""

        self.data_path_var = tk.StringVar(value=self.def_data_path)
        self.output_path_var = tk.StringVar(value=self.def_output_path)

        self.entry_frame = tk.Frame(self.root)
        self.entry_frame.pack(pady=10)

        # data path widgets
        self.data_frame = tk.Frame(self.entry_frame)
        self.data_frame.pack(side=tk.TOP, pady=5)

        self.data_label = tk.Label(self.data_frame, text="User Data Path")
        self.data_label.pack(side=tk.TOP, padx=5)

        self.data_entry = tk.Entry(
            self.data_frame, textvariable=self.data_path_var, width=60
        )
        self.data_entry.pack(side=tk.LEFT, padx=5)

        self.browse_data_button = tk.Button(
            self.data_frame, text="Browse", command=self.browse_data_file
        )
        self.browse_data_button.pack(side=tk.RIGHT, padx=5)

        # output path widget

        self.output_frame = tk.Frame(self.entry_frame)
        self.output_frame.pack(side=tk.BOTTOM, pady=5)

        self.output_label = tk.Label(self.output_frame, text="Video Output Folder")
        self.output_label.pack(side=tk.TOP, padx=5)

        self.output_entry = tk.Entry(
            self.output_frame, textvariable=self.output_path_var, width=60
        )
        self.output_entry.pack(side=tk.LEFT, padx=5)

        self.browse_output_button = tk.Button(
            self.output_frame, text="Browse", command=self.browse_output_folder
        )
        self.browse_output_button.pack(side=tk.RIGHT, padx=5)

        self.button_frame = tk.Frame(self.root)

        self.button_frame.pack(side=tk.RIGHT, padx=10)

        self.cancel_button = tk.Button(
            self.button_frame, text="Cancel", command=self.cancel
        )
        self.cancel_button.pack(side=tk.RIGHT, padx=10)

        self.submit_button = tk.Button(
            self.button_frame, text="Download Files", command=self.submit
        )
        self.submit_button.pack(side=tk.RIGHT, padx=5, pady=10)

    def run(self) -> None:
        # Start the main event loop
        self.root.mainloop()

    def browse_data_file(self):
        # Open a file dialog and store the selected file path in the entry widget
        filepath = filedialog.askopenfilename()
        self.data_path_var.set(filepath)  # Set the retrieved file path

    def browse_output_folder(self):
        filepath = filedialog.askdirectory()
        self.output_path_var.set(filepath)

    def start_downloads(self):
        if not self.def_data_path or not self.def_output_path:
            return

        user_data = get_tiktok_data(self.selected_data_path)
        video_list = get_video_list(user_data)
        dl_data = [get_link(v) for v in video_list]

        self.download_status_window = DownloadStatusWindow(self.root)
        thread = Thread(target=self.download_files, args=(dl_data[:4],))
        thread.start()

    def process_queue(self):
        try:
            while True:
                update_method, args = self.progress_queue.get_nowait()
                update_method(*args)
        except queue.Empty:
            self.root.after(100, self.process_queue)

    def _start_downloads(self):
        if not self.def_data_path or not self.def_output_path:
            return

        user_data = get_tiktok_data(self.selected_data_path)
        video_list = get_video_list(user_data)
        dl_data = [get_link(v) for v in video_list]

        self.download_status_window = DownloadStatusWindow(self.root)
        self.root.after(100, self.process_queue)  # Start processing the queue
        thread = Thread(target=self.download_files, args=(dl_data[:4],))
        thread.start()

    def download_files(self, url_data: list[tuple[str, str]]):
        num_files = len(url_data)
        i = 1
        for url, name in url_data:
            # Placeholder for download logic

            response = requests.get(url, stream=True)
            total_size = int(response.headers.get("content-length", 0))
            block_size = 1024

            with open(name, "wb") as f:
                for data in response.iter_content(block_size):
                    f.write(data)
                    self.download_status_window.update_current(f.tell(), total_size)

            self.download_status_window.update_overall(i, num_files)
            i += 1

    def _download_files(self, url_data: list[tuple[str, str]]):
        num_files = len(url_data)
        i = 1
        for url, name in url_data:
            response = requests.get(url, stream=True)
            total_size = int(response.headers.get("content-length", 0))
            block_size = 1024

            with open(name, "wb") as f:
                for data in response.iter_content(block_size):
                    f.write(data)
                    # Queue the updates instead of calling directly from the thread
                    self.progress_queue.put(
                        (
                            self.download_status_window.update_current,
                            (f.tell(), total_size),
                        )
                    )

            self.progress_queue.put(
                (self.download_status_window.update_overall, (i, num_files))
            )
            i += 1

    def _error(self, msg: str) -> None:
        ErrorDialog(msg).run()

    def error(self, msg: str) -> None:
        def show_error():
            ErrorDialog(msg).run()

        self.progress_queue.put((show_error, ()))

    def check_path(self, path: str) -> bool:
        if not os.path.exists(path):
            self.error(f"Invalid path: {path}")
            return False
        return True

    def submit(self):
        # Store the file path and close the window
        self.selected_data_path = self.data_path_var.get()
        self.selected_output_path = self.output_path_var.get()

        for path in [self.selected_data_path, self.selected_output_path]:
            if not self.check_path(path):
                return

        self.start_downloads()

        self.root.destroy()

    def cancel(self):
        # Close the window without storing the file path
        self.selected_data_path = None
        self.root.destroy()
