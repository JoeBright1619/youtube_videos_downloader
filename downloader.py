import yt_dlp
from pathlib import Path


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


def download(url, folder, progress_callback=None, error_callback=None):
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
        'ffmpeg_location': r'D:\apps\ffmpeg\ffmpeg-2026-03-30-git-e54e117998-essentials_build\bin',
        'ffmpeg_opts': {
            'preset': 'ultrafast',
            'audio_bitrate': '192k',
            'audio_quality': 2,
        },
        'js_runtimes': {
    'node': {
        'path': r'C:\Program Files\nodejs\node.exe',
    }
},
        'logger': _YtDlpLogger(error_callback=error_callback),
    }

    if progress_callback:
        ydl_opts['progress_hooks'] = [progress_callback]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])