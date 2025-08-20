# YouTube Download Playlists

## Project Setup and Usage Guide

This project manages a CSV of YouTube playlists/channels and batch-downloads them using yt-dlp. It supports Windows and Linux and is configured by default to download to a NAS mapped as drive `Z:` on Windows.

### Table of Contents
1. Project Overview
2. Prerequisites (Windows and Linux)
3. Installation (step-by-step)
4. ffmpeg installation
5. Authentication with .netrc
6. Configuration (`config.json`)
7. Using NAS drives as target directory (Windows and Linux)
8. Running the scripts
9. CSV schema
10. Troubleshooting
11. License

### 1) Project Overview
- `add.py`: Add YouTube playlists or channel uploads to `data.csv`.
- `download.py`: Download entries listed in the CSV using yt-dlp, sorted by priority and last update.

### 2) Prerequisites
- Python 3.9+
- Internet connectivity
- `ffmpeg` installed and available on PATH (details below)
- Optional auth: `.netrc` for YouTube/Google login if needed by yt-dlp

### 3) Installation (step-by-step)
Windows PowerShell:
```powershell
# 1) Clone the repository
git clone https://github.com/yourusername/yourproject.git
cd yourproject

# 2) Create a virtual environment
python -m venv .venv

# 3) Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# 4) Upgrade pip
python -m pip install --upgrade pip

# 5) Install Python dependencies
pip install -r requirements.txt

# 6) Verify installations
python --version
pip --version
yt-dlp --version
ffmpeg -version
```

Linux (Ubuntu/Mint) Bash:
```bash
# 1) Clone the repository
git clone https://github.com/dross1-dross1/ytdlp.git
cd ytdlp

# 2) Create a virtual environment
python3 -m venv .venv

# 3) Activate the virtual environment
source .venv/bin/activate

# 4) Upgrade pip
python -m pip install --upgrade pip

# 5) Install Python dependencies
pip install -r requirements.txt

# 6) Verify installations
python --version
pip --version
yt-dlp --version
ffmpeg -version
```

### 4) ffmpeg installation
- Windows (option A: winget):
```powershell
winget install --id=Gyan.FFmpeg -e --source winget
```
- Windows (option B: chocolatey):
```powershell
choco install ffmpeg -y
```
- Windows (option C: manual): Download a static build from `https://ffmpeg.org/download.html`, unzip, and add the `bin` folder to your PATH. Reopen your shell and run `ffmpeg -version`.
- Linux (Ubuntu/Mint):
```bash
sudo apt update && sudo apt install -y ffmpeg
```

### 5) Authentication with .netrc
If authentication is required, use a `.netrc` file (no credentials in the repo). Ensure the config has `"usenetrc": true` under `ytdlp`.

Format:
```text
machine youtube.com
  login YOUR_EMAIL
  password YOUR_APP_PASSWORD
machine google.com
  login YOUR_EMAIL
  password YOUR_APP_PASSWORD
```

Location and permissions:
- Windows: `%USERPROFILE%\.netrc` (recommended for yt-dlp). Example to create via PowerShell:
```powershell
notepad $env:USERPROFILE\.netrc
# Paste the entries, save the file, then close Notepad.
```
  Alternative: `%USERPROFILE%\_netrc`. If you use `_netrc`, you can point tools to it via the `NETRC` environment variable:
```powershell
setx NETRC "$env:USERPROFILE\_netrc"
```
- Linux: `~/.netrc`
```bash
nano ~/.netrc
# Paste the entries, save, exit
chmod 600 ~/.netrc
```

### 6) Configuration (config.json)
All settings live in `config.json` with two sections:
```json
{
  "app": {
    "csv_file": "data.csv",
    "save_path": "Z:/scraped_youtube_videos"
  },
  "ytdlp": {
    "outtmpl": "%(playlist_title)s/%(title)s.%(ext)s",
    "format": "bestvideo+bestaudio/best",
    "merge_output_format": "mp4",
    "usenetrc": true,
    "writethumbnail": true,
    "writeinfojson": true,
    "ignoreerrors": true
  }
}
```
- `app.csv_file`: CSV path (relative to repo or absolute).
- `app.save_path`: Download directory. Default is your NAS on Windows: `Z:/scraped_youtube_videos`.
- `ytdlp`: Options are passed directly to yt-dlp; `outtmpl` is resolved under `save_path`.

Linux users targeting a NAS mount (see section 7) can set:
```json
{
  "app": {
    "csv_file": "data.csv",
    "save_path": "/mnt/nas/scraped_youtube_videos"
  }
}
```

### 7) Using NAS drives as target directory
Windows (Map NAS to Z: drive):
1. Open File Explorer → This PC → Map network drive.
2. Select drive letter `Z:`.
3. Folder: `\\NAS_HOST\Share` (replace with your NAS hostname/IP and share name).
4. Check “Reconnect at sign-in”. Click Finish.
5. If prompted, enter NAS credentials. Confirm you can browse `Z:` in Explorer.
6. Ensure `config_opts.json` `app.save_path` is set to `Z:/scraped_youtube_videos`.
7. Optional: Command-line mapping (persistent):
```powershell
net use Z: \\NAS_HOST\Share /user:YOUR_USER YOUR_PASSWORD /persistent:yes
```

Linux (mount NAS via CIFS):
1. Install CIFS utilities:
```bash
sudo apt update && sudo apt install -y cifs-utils
```
2. Create a mount point:
```bash
sudo mkdir -p /mnt/nas
```
3. (Recommended) Store NAS credentials securely:
```bash
sudo bash -c 'cat > /etc/cifs-credentials <<EOF
username=YOUR_USER
password=YOUR_PASSWORD
domain=YOUR_DOMAIN_OR_LEAVE_EMPTY
EOF'
sudo chmod 600 /etc/cifs-credentials
```
4. Mount once to test:
```bash
sudo mount -t cifs //NAS_HOST/Share /mnt/nas -o credentials=/etc/cifs-credentials,iocharset=utf8,file_mode=0775,dir_mode=0775
```
5. Make it persistent at boot (fstab):
```bash
sudo bash -c 'echo "//NAS_HOST/Share /mnt/nas cifs credentials=/etc/cifs-credentials,iocharset=utf8,file_mode=0775,dir_mode=0775 0 0" >> /etc/fstab'
sudo mount -a
```
6. Verify access:
```bash
df -h | grep /mnt/nas || ls -la /mnt/nas
```
7. Set `config_opts.json` `app.save_path` to `/mnt/nas/scraped_youtube_videos` and ensure the directory exists:
```bash
mkdir -p /mnt/nas/scraped_youtube_videos
```

Security notes:
- The `/etc/cifs-credentials` file contains secrets; keep permissions restrictive.
- For Windows `net use` with a plaintext password, prefer using the GUI method or stored credentials where possible.

### 8) Running the scripts
1. Add playlists/channels to CSV using the helper (accepts playlist URLs like `...playlist?list=...` or channel URLs like `https://www.youtube.com/@name`). Type `exit` to quit:
```bash
python add.py
```
2. Download all non-skipped entries, sorted by priority desc and oldest `last_updated` first. Successful downloads update `last_updated` in UTC:
```bash
python download.py
```
Notes:
- Set `priority` to `-1` in the CSV to skip an entry.
- The output directory is created automatically if missing.

### 9) CSV schema
`data.csv` columns:
- `last_updated`: ISO timestamp (UTC) or blank
- `priority`: higher values downloaded first; `-1` to skip
- `id`: playlist ID or channel uploads playlist ID (e.g., `UU...`)
- `title`: human-readable name

### 10) Troubleshooting
- `ffmpeg not found`: Ensure `ffmpeg -version` works in the same shell. Reopen the shell after changing PATH.
- `yt-dlp auth issues`: Check that Windows uses `%USERPROFILE%\\.netrc` (or set `NETRC` if using `%USERPROFILE%\\_netrc`), Linux uses `~/.netrc` with `chmod 600`, and ensure `"usenetrc": true` in config.
- `NAS not accessible`:
  - Windows: Confirm `Z:` is mapped and reachable in Explorer; re-map if needed.
  - Linux: Check `mount` output and credentials file permissions; run `sudo mount -a` after editing `/etc/fstab`.
- `Permission denied` on NAS: Verify user rights on the share; try different `file_mode`/`dir_mode` for Linux CIFS.

### 11) License
See `LICENSE`.


