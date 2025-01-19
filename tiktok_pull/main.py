import os
import re
import json
import tkinter as tk

from tqdm import tqdm

from tiktok_pull import consts
from tiktok_pull.gui import (
    ErrorDialog,
    FileDownloaderApp,
    DownloadStatusWindow,
)


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


def main():
    root = tk.Tk()
    app = FileDownloaderApp(root=root)
    root.mainloop()
    """ dialog = TTPullGui(def_path=os.path.abspath(consts.DEFAULT_DATA_PATH))
    dialog.run()

    path = dialog.selected_path
    if path is None:
        return

    if not path or not os.path.exists(path):
        ErrorDialog(message=f"Error, invalid path provided:\n{path}").run()
        return

    user_data = get_tiktok_data(path)
    video_list = get_video_list(user_data)
    dl_data = [get_link(v) for v in video_list]

    urls = [f"{d[0]},{d[1]}" for d in dl_data[:4]]
    with open("urls.txt", "w", encoding="UTF-8") as fs:
        fs.write("\n".join(urls)) """


if __name__ == "__main__":
    main()
