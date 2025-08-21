import os
from datetime import datetime
from typing import Dict, Any

import pandas as pd
from pandas import Timestamp
from yt_dlp import YoutubeDL

from common import (
    project_root,
    load_config,
    get_app_config,
    get_ytdlp_config,
    resolve_csv_path,
    ensure_csv,
    resolve_save_path,
)


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
    cfg = load_config()
    app_cfg = get_app_config(cfg)
    ytdlp_cfg = get_ytdlp_config(cfg)

    csv_file_name = resolve_csv_path(app_cfg)
    save_path = resolve_save_path(app_cfg)

    # Ensure CSV exists with headers to avoid first-run crashes
    if not os.path.exists(csv_file_name):
        ensure_csv(csv_file_name)
    loaded_playlist_data = pd.read_csv(csv_file_name, encoding="utf-8")
    for _, pl_entry in sort_playlists_by_date_and_priority(loaded_playlist_data).iterrows():
        if pl_entry["priority"] != -1:
            print(f"[PLDL] Downloading '{pl_entry['title']}'...")
            download_playlist_videos(pl_entry["id"], save_path=save_path, csv_file=csv_file_name, ytdlp_cfg=ytdlp_cfg)
        else:
            print(f"[PLDL] Skipping '{pl_entry['title']}' due to priority setting.")


