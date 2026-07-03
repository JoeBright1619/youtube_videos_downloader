# YouTube to MP3 Downloader

A simple desktop app for downloading YouTube videos (and full playlists) as MP3 audio files. It provides a small Tkinter GUI on top of [yt-dlp](https://github.com/yt-dlp/yt-dlp), with `ffmpeg` handling the audio extraction and MP3 conversion.

## Features

- **Batch downloads** — paste one or many URLs, one per line.
- **Playlist support** — any URL containing `list=` is treated as a playlist and downloaded in full; plain video URLs download only the single video.
- **MP3 conversion** — audio is extracted and encoded to MP3 at 192 kbps.
- **Resume-friendly** — a per-folder archive (`.yt_dlp_downloaded_archive.txt`) records already-downloaded videos so re-running skips them.
- **Failure reporting** — items that fail are skipped (the rest of the batch continues) and written to a timestamped `failed_downloads_*.txt` report in the output folder.
- **Live progress** — per-track status, download percentage, and conversion state shown in the window.
- **High-DPI aware** — crisp text and layout on scaled Windows displays.

## Requirements

- **Python 3.8+**
- **[yt-dlp](https://pypi.org/project/yt-dlp/)** (Python package)
- **[ffmpeg](https://ffmpeg.org/)** — required for MP3 conversion
- **[Node.js](https://nodejs.org/)** — used by yt-dlp as a JavaScript runtime for some YouTube URLs
- Windows (the app uses Windows-specific DPI APIs; the core download logic is cross-platform)

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd youtube_downloader

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows PowerShell/CMD
# source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

Install `ffmpeg` and `Node.js` separately if you don't already have them.

## Configuration

The app locates `ffmpeg` and `node` automatically. If both are on your system `PATH`, **no configuration is needed**.

To point at specific installations instead, set these two variables:

| Variable | Meaning |
| --- | --- |
| `FFMPEG_LOCATION` | Path to the directory containing the `ffmpeg` executable (its `bin` folder). |
| `NODE_PATH` | Full path to the `node` executable. |

### Using a `.env` file (recommended)

Copy the provided template and edit the paths:

```bash
cp .env.example .env
```

```ini
# .env
FFMPEG_LOCATION=D:\apps\ffmpeg\...\bin
NODE_PATH=C:\Program Files\nodejs\node.exe
```

The `.env` file is loaded automatically on startup and is git-ignored, so your machine-specific paths never get committed.

### Or use environment variables directly

```powershell
# Windows PowerShell
$env:FFMPEG_LOCATION = "D:\apps\ffmpeg\...\bin"
$env:NODE_PATH = "C:\Program Files\nodejs\node.exe"
python main.py
```

If a variable is unset, the app falls back to whatever it finds on `PATH`.

## Usage

```bash
python main.py
```

1. Paste one or more YouTube URLs into the text box (one URL per line).
2. Click **Choose Folder** and select where the MP3 files should be saved.
3. Click **Download**.

Progress is displayed in the window. When the batch finishes:
- If everything succeeded, you'll see "All downloads complete!"
- If some items failed, they are skipped and a `failed_downloads_<timestamp>.txt` report is saved to your chosen folder.

## Project structure

| File | Responsibility |
| --- | --- |
| [main.py](main.py) | Entry point — wires the UI and controller together and starts the Tk event loop. |
| [ui.py](ui.py) | `DownloaderUI` — builds the Tkinter window (inputs, buttons, status labels). |
| [controller.py](controller.py) | `DownloadController` — handles user actions, runs downloads on a background thread, tracks progress and failures, writes the failure report. |
| [downloader.py](downloader.py) | Thin wrapper around yt-dlp; configures format, playlist handling, download archive, and MP3 post-processing. |
| [platform_utils.py](platform_utils.py) | Windows high-DPI awareness and Tk scaling helpers. |

## Notes

- Downloads run on a background thread, so the UI stays responsive.
- The download archive is stored **per output folder**, so choosing a different folder starts a fresh archive.
- Only download content you have the rights to. Respect YouTube's Terms of Service and applicable copyright law.
