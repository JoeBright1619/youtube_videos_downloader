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


def _resolve_cookies_browser():
    """
    Read the COOKIES_FROM_BROWSER environment variable, if set, to let yt-dlp
    reuse a logged-in browser session. This can surface age-restricted or
    region-locked videos that YouTube hides from anonymous requests.

    Returns a tuple suitable for yt-dlp's 'cookiesfrombrowser' option
    (e.g. ('chrome',)), or None if not configured.
    Accepted values: chrome, edge, firefox, brave, opera, vivaldi, chromium, safari.
    """
    browser = (os.environ.get("COOKIES_FROM_BROWSER") or "").strip().lower()
    if not browser:
        return None
    return (browser,)


def _resolve_cookie_file():
    """
    Read the COOKIES_FILE environment variable: a path to a cookies.txt file
    (Netscape format) exported from a logged-in browser. This is the most
    reliable way to pass cookies on modern Chrome/Edge, which encrypt their
    cookie stores so yt-dlp can't read them directly.

    Returns the path if set and the file exists, otherwise None.
    """
    path = (os.environ.get("COOKIES_FILE") or "").strip()
    if path and Path(path).is_file():
        return path
    return None


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


def _build_ydl_opts(folder, progress_callback=None, error_callback=None, match_filter=None) -> dict:
    """Build the yt-dlp options dict shared by single-video and playlist paths."""
    archive_file = str(Path(folder) / ".yt_dlp_downloaded_archive.txt")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{folder}/%(title)s.%(ext)s',
        # Continue playlists even if some items are unavailable/private/blocked.
        'ignoreerrors': True,
        # Keep a per-folder archive of downloaded video IDs.
        # If a video is already in this archive, yt-dlp skips it.
        'download_archive': archive_file,
        # YouTube gates audio/video formats behind JavaScript "signature"/"n"
        # challenges. yt-dlp fetches its EJS solver script from GitHub to solve
        # them; without this, only thumbnails resolve and downloads fail with
        # "Requested format is not available".
        'remote_components': ['ejs:github'],
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

    # A cookies.txt file takes precedence over reading the browser directly,
    # since browser cookie stores are often encrypted/locked.
    cookie_file = _resolve_cookie_file()
    if cookie_file:
        ydl_opts['cookiefile'] = cookie_file
    else:
        cookies_browser = _resolve_cookies_browser()
        if cookies_browser:
            ydl_opts['cookiesfrombrowser'] = cookies_browser

    # Called by yt-dlp for every item before downloading. Returning a string
    # skips that item (with the string as the reason); returning None downloads.
    if match_filter:
        ydl_opts['match_filter'] = match_filter

    if progress_callback:
        ydl_opts['progress_hooks'] = [progress_callback]

    return ydl_opts


def download(
    url,
    folder,
    progress_callback=None,
    error_callback=None,
    match_filter=None,
    before_item_callback=None,
):
    """
    Download a single video (or all tracks of a playlist) to MP3 files.

    If `before_item_callback` is provided, it is invoked before the second
    and subsequent playlist items start downloading, so the caller can
    pause/resume the batch between tracks.
    """
    opts = _build_ydl_opts(folder, progress_callback, error_callback, match_filter)

    if before_item_callback:
        # Wrap the progress hook so that, for playlists, we can pause between
        # individual tracks. yt-dlp fires a progress callback with status
        # 'downloading' once per item (repeatedly while data streams). The
        # first event for a given video_id marks the start of that item's
        # download. We block on the callback before the second+ items.
        seen_ids = set()
        first_item = True

        def _pause_aware_progress(data):
            nonlocal first_item
            status = data.get("status")
            info = data.get("info_dict") or {}
            video_id = info.get("id") or ""

            if status == "downloading" and video_id and video_id not in seen_ids:
                seen_ids.add(video_id)
                if not first_item:
                    before_item_callback()
                first_item = False

            if progress_callback:
                progress_callback(data)

        hooks = list(opts.get("progress_hooks") or [])
        hooks.append(_pause_aware_progress)
        opts["progress_hooks"] = hooks

    with yt_dlp.YoutubeDL(opts) as ydl:  # type: ignore[arg-type]
        ydl.download([url])
