import os
import json
from datetime import datetime
from typing import Dict, Any

import pandas as pd
from pandas import Timestamp
from yt_dlp import YoutubeDL


CONFIG_FILE_NAME = "config.json"


def _project_root() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _config_path() -> str:
    return os.path.join(_project_root(), CONFIG_FILE_NAME)


def _load_config() -> Dict[str, Any]:
    try:
        with open(_config_path(), "r", encoding="utf-8") as fp:
            return json.load(fp)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def get_ydl_opts(save_path: str, ytdlp_cfg: Dict[str, Any]) -> Dict[str, Any]:
    opts = dict(ytdlp_cfg or {})
    outtmpl = opts.get("outtmpl", "%(playlist_title)s/%(title)s.%(ext)s")
    opts["outtmpl"] = os.path.join(save_path, outtmpl)
    return opts


def update_last_updated(csv_file: str, playlist_id: str) -> None:
    df = pd.read_csv(csv_file, encoding="utf-8")
    df.loc[df["id"] == playlist_id, "last_updated"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    df.to_csv(csv_file, index=False, encoding="utf-8")


def download_playlist_videos(playlist_id: str, save_path: str, csv_file: str, ytdlp_cfg: Dict[str, Any]) -> None:
    playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
    ydl_opts = get_ydl_opts(save_path, ytdlp_cfg)
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)
        if info is None:
            print(f"[PLDL] Failed to download '{playlist_url}': Playlist not found.")
            return
        print(f"[PLDL] Downloading playlist '{info.get('title', 'Unknown Playlist')}'...")
        ydl.download([playlist_url])
        print(f"[PLDL] Finished downloading playlist '{info.get('title', 'Unknown Playlist')}' to '{save_path}'")
        update_last_updated(csv_file, playlist_id)


def sort_playlists_by_date_and_priority(df: pd.DataFrame) -> pd.DataFrame:
    safe_min_date = Timestamp('1678-01-01')
    df['last_updated'] = pd.to_datetime(df["last_updated"], errors="coerce").fillna(safe_min_date)
    df.sort_values(by=["priority", "last_updated"], ascending=[False, True], inplace=True)
    return df


if __name__ == "__main__":
    cfg = _load_config()
    app_cfg = cfg.get("app", {})
    ytdlp_cfg = cfg.get("ytdlp", {})

    csv_cfg = app_cfg.get("csv_file", "data.csv")
    if not os.path.isabs(csv_cfg):
        csv_file_name = os.path.join(_project_root(), csv_cfg)
    else:
        csv_file_name = csv_cfg

    save_cfg = app_cfg.get("save_path", os.path.join(_project_root(), "downloads"))
    save_path = os.path.abspath(os.path.expanduser(save_cfg))
    os.makedirs(save_path, exist_ok=True)

    loaded_playlist_data = pd.read_csv(csv_file_name, encoding="utf-8")
    for _, pl_entry in sort_playlists_by_date_and_priority(loaded_playlist_data).iterrows():
        if pl_entry["priority"] != -1:
            print(f"[PLDL] Downloading '{pl_entry['title']}'...")
            download_playlist_videos(pl_entry["id"], save_path=save_path, csv_file=csv_file_name, ytdlp_cfg=ytdlp_cfg)
        else:
            print(f"[PLDL] Skipping '{pl_entry['title']}' due to priority setting.")


