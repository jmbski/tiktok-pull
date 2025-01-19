import os
import re
import json

from tqdm import tqdm

from tiktok_pull.tiktok_pull import consts

def get_tiktok_data(path: str = ) -> dict:
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
    user_data = get_tiktok_data()
    dl_data = [get_link(v) for v in videolist]

    for url, name in tqdm(dl_data):
        os.system(f'curl "{url}" -o "{name}"')


if __name__ == "__main__":
    main()
