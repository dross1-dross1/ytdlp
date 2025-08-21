import os
import re
from typing import Optional
import json

import pandas as pd
import requests
from bs4 import BeautifulSoup

from common import project_root, load_config, get_app_config, ensure_csv

# Minimal network hygiene
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}
DEFAULT_TIMEOUT = 15


def _load_app_config() -> dict:
    cfg = load_config()
    return get_app_config(cfg)


def _ensure_csv(file_path: str) -> None:
    ensure_csv(file_path)


def extract_playlist_code(url: str) -> Optional[str]:
    """Return the value of the list parameter from a YouTube URL, if present."""
    match = re.search(r"list=([\w-]+)", url)
    return match.group(1) if match else None


def get_page_title(url: str) -> str:
    """Fetch page title and strip the standard YouTube suffix when present."""
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.text.replace(" - YouTube", "").strip()
            return title
    except requests.RequestException as e:
        return f"Error: {e}"
    return ""


def get_channel_id_from_url(url: str, return_plid: bool = False) -> str:
    """Extract the channel ID (or its uploads playlist ID when requested) from a channel page.

    Note: For uploads playlist ID, YouTube uses the pattern 'UU' + channel_id[2:].
    """
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        scripts = soup.find_all("script")
        for script in scripts:
            if "externalId" not in script.text:
                continue
            match = re.search(r'"externalId":"(.*?)"', script.text)
            if not match:
                continue
            channel_id = match.group(1)
            if return_plid:
                return channel_id[0] + "U" + channel_id[2:]
            return channel_id
        return "Channel ID not found"
    except requests.RequestException as e:
        return f"Error: {e}"


def append_to_playlist_data(file_path: str, url: str) -> str:
    """Append a playlist or uploads playlist by URL into the managed CSV."""
    _ensure_csv(file_path)
    if "playlist?list=" in url:
        id_code = extract_playlist_code(url)
    elif "/@" in url:
        id_code = get_channel_id_from_url(url, True)
    elif "--forceid" in url:
        url_raw = url.replace("--forceid", "")
        id_code = get_channel_id_from_url(url_raw, True)
    else:
        return "Error: Invalid URL"

    title = get_page_title(f"https://www.youtube.com/playlist?list={id_code}")
    if "Error" in title:
        return title

    df = pd.read_csv(file_path)
    if id_code in df["id"].values:
        return f"The playlist '{title}' ({id_code}) already exists in '{file_path}'"

    new_row = pd.DataFrame([
        {"last_updated": None, "priority": 5, "id": id_code, "title": title}
    ])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(file_path, index=False)
    return f"Added '{title}' to '{file_path}'"


if __name__ == "__main__":
    app_cfg = _load_app_config()
    csv_cfg = app_cfg.get("csv_file", "data.csv")
    csv_path = os.path.join(project_root(), csv_cfg) if not os.path.isabs(csv_cfg) else csv_cfg
    _ensure_csv(csv_path)

    while True:
        url_in = input("Enter YouTube playlist/channel URL (or 'exit' to quit): ")
        if url_in.lower() == "exit":
            break
        result = append_to_playlist_data(csv_path, url_in)
        print(result)


