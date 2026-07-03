import os
import shutil

import yt_dlp
from dotenv import load_dotenv
from pathlib import Path

# Load variables from a local .env file (if present) into the environment.
load_dotenv()


def _resolve_ffmpeg_location():
    """
    Locate ffmpeg. Priority:
      1. FFMPEG_LOCATION environment variable (path to the ffmpeg bin directory).
      2. ffmpeg found on the system PATH.
    Returns None if neither is set, letting yt-dlp fall back to its own lookup.
    """
    env_location = os.environ.get("FFMPEG_LOCATION")
    if env_location:
        return env_location

    ffmpeg_on_path = shutil.which("ffmpeg")
    if ffmpeg_on_path:
        return str(Path(ffmpeg_on_path).parent)

    return None


def _resolve_node_path():
    """
    Locate the Node.js executable. Priority:
      1. NODE_PATH environment variable (full path to node executable).
      2. node found on the system PATH.
    Returns None if neither is available.
    """
    env_path = os.environ.get("NODE_PATH")
    if env_path:
        return env_path

    return shutil.which("node")


def is_playlist(url: str) -> bool:
    """
    Treat any URL that has a playlist id (list=...) as a playlist,
    including watch URLs like:
      https://www.youtube.com/watch?v=...&list=...
    so yt_dlp will download the whole playlist instead of a single video.
    """
    return "list=" in url


class _YtDlpLogger:
    def __init__(self, error_callback=None):
        self._error_callback = error_callback

    def debug(self, msg):
        print(msg)

    def warning(self, msg):
        print(f"WARNING: {msg}")

    def error(self, msg):
        print(f"ERROR: {msg}")
        if self._error_callback:
            self._error_callback(msg)


def download(url, folder, progress_callback=None, error_callback=None, match_filter=None):
    archive_file = str(Path(folder) / ".yt_dlp_downloaded_archive.txt")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{folder}/%(title)s.%(ext)s',
        # Continue playlists even if some items are unavailable/private/blocked.
        'ignoreerrors': True,
        # Keep a per-folder archive of downloaded video IDs.
        # If a video is already in this archive, yt-dlp skips it.
        'download_archive': archive_file,
        # If this URL looks like it belongs to a playlist (has list=),
        # allow yt_dlp to process the full playlist instead of forcing
        # single‑video mode.
        'noplaylist': not is_playlist(url),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'ffmpeg_opts': {
            'preset': 'ultrafast',
            'audio_bitrate': '192k',
            'audio_quality': 2,
        },
        'logger': _YtDlpLogger(error_callback=error_callback),
    }

    ffmpeg_location = _resolve_ffmpeg_location()
    if ffmpeg_location:
        ydl_opts['ffmpeg_location'] = ffmpeg_location

    node_path = _resolve_node_path()
    if node_path:
        ydl_opts['js_runtimes'] = {'node': {'path': node_path}}

    # Called by yt-dlp for every item before downloading. Returning a string
    # skips that item (with the string as the reason); returning None downloads.
    if match_filter:
        ydl_opts['match_filter'] = match_filter

    if progress_callback:
        ydl_opts['progress_hooks'] = [progress_callback]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])