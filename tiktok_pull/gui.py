import json
import os
import re
import tkinter as tk

from dataclasses import dataclass
from threading import Thread
from tkinter import filedialog, ttk

import requests

from tiktok_pull import consts


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
class TTPullGui:
    root: tk.Tk = None
    data_path_var: tk.StringVar = None
    output_path_var: tk.StringVar = None

    data_entry: tk.Entry = None
    output_entry: tk.Entry = None

    browse_data_button: tk.Button = None
    browse_output_button: tk.Button = None

    submit_button: tk.Button = None
    cancel_button: tk.Button = None
    selected_data_path: str = None
    def_data_path: str = None

    def __post_init__(self) -> None:
        # Create the main window
        self.root = tk.Tk()
        self.root.title("Filepath Browser")
        self.root.geometry("400x100")  # Set size of the window

        # Create a StringVar to hold the file path

        if not os.path.exists(self.def_data_path):
            self.def_data_path = ""

        self.data_path_var = tk.StringVar(value=self.def_data_path)

        # Create an Entry widget for displaying the file path
        self.data_entry = tk.Entry(
            self.root, textvariable=self.data_path_var, width=40
        )
        self.data_entry.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

        # Create a Button to open the file dialog
        self.browse_data_button = tk.Button(
            self.root, text="Browse", command=self.browse_file
        )
        self.browse_data_button.grid(row=0, column=2, padx=10, pady=10)

        # Create submit and cancel buttons
        self.submit_button = tk.Button(
            self.root, text="Submit", command=self.submit
        )
        self.submit_button.grid(row=1, column=0, padx=10, pady=10)

        self.cancel_button = tk.Button(
            self.root, text="Cancel", command=self.cancel
        )
        self.cancel_button.grid(row=1, column=2, padx=10, pady=10)

    def run(self) -> str:
        # Start the main event loop
        self.root.mainloop()
        return self.selected_data_path

    def browse_file(self):
        # Open a file dialog and store the selected file path in the entry widget
        filepath = filedialog.askopenfilename()
        self.data_path_var.set(filepath)  # Set the retrieved file path

    def submit(self):
        # Store the file path and close the window
        self.selected_data_path = self.data_path_var.get()
        self.root.destroy()

    def cancel(self):
        # Close the window without storing the file path
        self.selected_data_path = None
        self.root.destroy()


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
        self.root.geometry("300x100")  # Set size of the window

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
class FileDownloaderApp:

    root: tk.Tk = None

    def_data_path: str = ""
    selected_data_path: str = None
    data_path_var: tk.StringVar = None
    data_entry: tk.Entry = None

    def_output_path: str = ""
    selected_output_path: str = None
    output_path_var: tk.StringVar = None
    output_entry: tk.Entry = None

    browse_data_button: tk.Button = None
    browse_output_button: tk.Button = None

    submit_button: tk.Button = None
    cancel_button: tk.Button = None
    selected_path: str = None

    # download_status_window: DownloadStatusWindow = None

    def __post_init__(self):
        # Create the main window
        self.root = tk.Tk()
        self.root.title("TikTok Content Downloader")
        self.root.geometry("400x100")  # Set size of the window

        if not os.path.exists(self.def_data_path):
            self.def_data_path = ""

        if not os.path.exists(self.def_output_path):
            self.def_output_path = ""

        self.data_path_var = tk.StringVar(value=self.def_data_path)
        self.output_path_var = tk.StringVar(value=self.def_output_path)

        self.entry_frame = tk.Frame(self.root)
        # Create an Entry widget for displaying the file path
        """ self.data_entry = tk.Entry(
            self.root, textvariable=self.data_path_var, width=40
        )
        self.data_entry.grid(row=0, column=0, columnspan=2, padx=10, pady=10) """

        """ # Create an Entry widget for displaying the file path
        self.output_entry = tk.Entry(
            self.root, textvariable=self.output_path_var, width=40
        )
        self.output_entry.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(pady=10)

        self.browse_data_button = tk.Button(
            self.button_frame, text="Browse File", command=self.browse_file
        )
        self.browse_data_button.pack(side=tk.LEFT, padx=5)

        self.download_button = tk.Button(
            self.button_frame, text="Start Download", command=self.start_downloads
        )
        self.download_button.pack(side=tk.LEFT, padx=5) """

    def run(self) -> None:
        # Start the main event loop
        self.root.mainloop()

    def browse_file(self):
        self.def_data_path = filedialog.askopenfilename()

    def start_downloads(self):
        if not self.def_data_path:
            return

        with open(self.def_data_path, "r") as file:
            urls = file.read().splitlines()

        urls = [tuple(l.split(",")) for l in urls]

        self.download_status_window = DownloadStatusWindow(self.root)
        thread = Thread(target=self.download_files, args=(urls,))
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
