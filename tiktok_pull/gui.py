import os
import tkinter as tk

from dataclasses import dataclass
from threading import Thread
from tkinter import filedialog, ttk

import requests

from tiktok_pull import consts


@dataclass
class TTPullGui:
    root: tk.Tk = None
    entry_var: tk.StringVar = None
    entry: tk.Entry = None
    browse_button: tk.Button = None
    submit_button: tk.Button = None
    cancel_button: tk.Button = None
    selected_path: str = None
    def_path: str = None

    def __post_init__(self) -> None:
        # Create the main window
        self.root = tk.Tk()
        self.root.title("Filepath Browser")
        self.root.geometry("400x100")  # Set size of the window

        # Create a StringVar to hold the file path

        if not os.path.exists(self.def_path):
            self.def_path = ""

        self.entry_var = tk.StringVar(value=self.def_path)

        # Create an Entry widget for displaying the file path
        self.entry = tk.Entry(self.root, textvariable=self.entry_var, width=40)
        self.entry.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

        # Create a Button to open the file dialog
        self.browse_button = tk.Button(
            self.root, text="Browse", command=self.browse_file
        )
        self.browse_button.grid(row=0, column=2, padx=10, pady=10)

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
        return self.selected_path

    def browse_file(self):
        # Open a file dialog and store the selected file path in the entry widget
        filepath = filedialog.askopenfilename()
        self.entry_var.set(filepath)  # Set the retrieved file path

    def submit(self):
        # Store the file path and close the window
        self.selected_path = self.entry_var.get()
        self.root.destroy()

    def cancel(self):
        # Close the window without storing the file path
        self.selected_path = None
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


class FileDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Downloader")
        self.filepath = None
        self.download_status_window: DownloadStatusWindow = None

        self.button_frame = tk.Frame(root)
        self.button_frame.pack(pady=10)

        self.browse_button = tk.Button(
            self.button_frame, text="Browse File", command=self.browse_file
        )
        self.browse_button.pack(side=tk.LEFT, padx=5)

        self.download_button = tk.Button(
            self.button_frame, text="Start Download", command=self.start_downloads
        )
        self.download_button.pack(side=tk.LEFT, padx=5)

    def browse_file(self):
        self.filepath = filedialog.askopenfilename()

    def start_downloads(self):
        if not self.filepath:
            return

        with open(self.filepath, "r") as file:
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
