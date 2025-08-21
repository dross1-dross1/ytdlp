import os
import json
from typing import Dict

import pandas as pd


CONFIG_FILE_NAME = "config.json"


def project_root() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _config_path() -> str:
    return os.path.join(project_root(), CONFIG_FILE_NAME)


def load_config() -> Dict:
    try:
        with open(_config_path(), "r", encoding="utf-8") as fp:
            return json.load(fp)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def get_app_config(cfg: Dict) -> Dict:
    return (cfg or {}).get("app", {})


def get_ytdlp_config(cfg: Dict) -> Dict:
    return (cfg or {}).get("ytdlp", {})


def resolve_csv_path(app_cfg: Dict) -> str:
    csv_cfg = (app_cfg or {}).get("csv_file", "data.csv")
    if not os.path.isabs(csv_cfg):
        return os.path.join(project_root(), csv_cfg)
    return csv_cfg


def ensure_csv(file_path: str) -> None:
    if not os.path.exists(file_path):
        os.makedirs(os.path.dirname(file_path) or project_root(), exist_ok=True)
        pd.DataFrame(columns=["last_updated", "priority", "id", "title"]).to_csv(
            file_path, index=False, encoding="utf-8"
        )


def resolve_save_path(app_cfg: Dict) -> str:
    save_cfg = (app_cfg or {}).get("save_path", os.path.join(project_root(), "downloads"))
    save_path = os.path.abspath(os.path.expanduser(save_cfg))
    os.makedirs(save_path, exist_ok=True)
    return save_path


