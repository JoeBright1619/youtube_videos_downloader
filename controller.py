import re
import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

from downloader import download


def _normalize_title(name: str) -> str:
    """Reduce a title/filename to lowercase alphanumerics for loose matching."""
    return re.sub(r"[^a-z0-9]+", "", (name or "").lower())


class DownloadController:
    def __init__(self, ui):
        self.ui = ui
        self.folder_path = ""
        self.failed_items = []
        self._failed_keys = set()
        # Duplicate handling: None = ask each time, else "skip_all"/"download_all".
        self._dup_policy = None
        # Normalized titles of audio files already on disk (snapshot, read-only).
        self._existing_titles = set()
        # Video ids already evaluated this run (yt-dlp calls the filter twice
        # per video, so we must only decide once).
        self._seen_ids = set()

    def _run_on_ui(self, fn):
        self.ui.root.after(0, fn)

    def _set_status(self, text: str, fg: str = "#e5e5e5"):
        self._run_on_ui(lambda: self.ui.set_status(text, fg))

    def _set_download_enabled(self, enabled: bool):
        self._run_on_ui(lambda: self.ui.set_download_enabled(enabled))

    def choose_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return
        self.folder_path = folder
        self.ui.set_folder_text(folder, fg="#e5e5e5")

    def _add_failed_item(self, title: str, url: str, reason: str):
        fail_key = f"{url}|{reason}"
        if fail_key in self._failed_keys:
            return
        self._failed_keys.add(fail_key)
        self.failed_items.append(
            {
                "title": title or "Unknown title",
                "url": url or "Unknown URL",
                "reason": reason or "Unknown download error",
            }
        )

    def _snapshot_existing_titles(self):
        """Record normalized names of audio files already in the folder."""
        self._existing_titles = set()
        audio_exts = {".mp3", ".m4a", ".webm", ".opus", ".wav", ".aac", ".flac"}
        try:
            for entry in Path(self.folder_path).iterdir():
                if entry.is_file() and entry.suffix.lower() in audio_exts:
                    self._existing_titles.add(_normalize_title(entry.stem))
        except OSError:
            pass

    def _ask_duplicate(self, title: str) -> str:
        """Ask the user how to handle a duplicate. Blocks the download thread."""
        result = {}
        done = threading.Event()

        def show():
            result["value"] = self.ui.ask_duplicate_dialog(title)
            done.set()

        self._run_on_ui(show)
        done.wait()
        return result.get("value", "skip")

    def _match_filter(self, info_dict, incomplete=False):
        """
        Called by yt-dlp before each item. Return None to download, or a
        string reason to skip. Detects tracks that already exist (same title)
        and applies the user's choice: skip this / skip all / download this /
        download all.
        """
        # yt-dlp calls this for the playlist container and flat "url" entries as
        # well as fully-resolved videos, and `incomplete` may be a truthy set of
        # field names rather than a bool — so gate on the entry type instead of
        # `incomplete`. Only act on a real video entry (type None or "video").
        if info_dict.get("_type") not in (None, "video"):
            return None

        title = info_dict.get("title") or ""
        norm = _normalize_title(title)
        if not norm:
            return None

        # yt-dlp invokes this filter about twice per video (once while
        # processing, once just before download). Decide only the first time we
        # see a given id, otherwise the second call would re-prompt.
        video_id = info_dict.get("id") or norm
        if video_id in self._seen_ids:
            return None
        self._seen_ids.add(video_id)

        if norm not in self._existing_titles:
            # Not already on disk — download it.
            return None

        # Duplicate detected — decide what to do.
        if self._dup_policy == "download_all":
            return None
        if self._dup_policy == "skip_all":
            self._set_status(f"Skipped duplicate: {title}", fg="#9ca3af")
            return f"Already exists: {title}"

        decision = self._ask_duplicate(title)
        if decision == "skip_all":
            self._dup_policy = "skip_all"
        elif decision == "download_all":
            self._dup_policy = "download_all"

        if decision in ("download", "download_all"):
            return None

        self._set_status(f"Skipped duplicate: {title}", fg="#9ca3af")
        return f"Already exists: {title}"

    def progress_hook(self, data):
        info = data.get("info_dict") or {}
        playlist_index = info.get("playlist_index") or info.get("playlist_autonumber")
        playlist_count = info.get("playlist_count") or info.get("n_entries")
        title = info.get("title") or ""
        video_id = info.get("id") or ""
        webpage_url = info.get("webpage_url") or info.get("original_url") or ""

        prefix = ""
        if playlist_index and playlist_count:
            prefix = f"Track {playlist_index}/{playlist_count} "
        elif playlist_index:
            prefix = f"Track {playlist_index} "

        status = data.get("status")
        if status == "downloading":
            pct = data.get("_percent_str", "").strip()
            self._set_status(f"{prefix}{title}\n{pct}", fg="#e5e5e5")
        elif status == "finished":
            self._set_status(f"{prefix}{title}\nConverting to MP3...", fg="#ffdd57")
        elif status == "error":
            reason = data.get("error", "Unknown download error")
            self._add_failed_item(title, webpage_url or video_id, reason)
            self._set_status(f"{prefix}{title}\nFailed: {reason}", fg="#fca5a5")

    def _write_failed_report(self):
        if not self.failed_items:
            return None

        report_name = f"failed_downloads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_path = Path(self.folder_path) / report_name

        lines = [
            f"Failed downloads report - {datetime.now().isoformat(timespec='seconds')}",
            "",
        ]
        for index, item in enumerate(self.failed_items, start=1):
            lines.extend(
                [
                    f"{index}. {item['title']}",
                    f"   URL: {item['url']}",
                    f"   Reason: {item['reason']}",
                    "",
                ]
            )

        report_path.write_text("\n".join(lines), encoding="utf-8")
        return report_path

    def start_download(self):
        self.ui.set_download_enabled(False)
        threading.Thread(target=self._run_download, daemon=True).start()

    def _run_download(self):
        urls = self.ui.get_urls()
        self.failed_items = []
        self._failed_keys = set()
        self._dup_policy = None
        self._seen_ids = set()

        if not urls or urls == [""]:
            self._run_on_ui(lambda: messagebox.showerror("Error", "Paste at least one link"))
            self._set_download_enabled(True)
            return

        if not self.folder_path:
            self._run_on_ui(lambda: messagebox.showerror("Error", "Choose a folder"))
            self._set_download_enabled(True)
            return

        self._snapshot_existing_titles()

        try:
            for i, raw_url in enumerate(urls, start=1):
                url = raw_url.strip()
                if not url:
                    continue

                self._set_status(f"Processing link ({i}/{len(urls)})...", fg="#ffdd57")
                download(
                    url,
                    self.folder_path,
                    progress_callback=self.progress_hook,
                    error_callback=lambda msg, item_url=url: self._add_failed_item(
                        "Unknown title",
                        item_url,
                        msg,
                    ),
                    match_filter=self._match_filter,
                )

            report_path = self._write_failed_report()
            if self.failed_items:
                self._set_status(
                    f"Completed with {len(self.failed_items)} failed item(s). See report file.",
                    fg="#ffdd57",
                )
                self._run_on_ui(
                    lambda path=str(report_path): messagebox.showwarning(
                        "Completed with failures",
                        f"Some items failed and were skipped.\n\nReport saved to:\n{path}",
                    )
                )
            else:
                self._set_status("All downloads complete !", fg="#6ee7b7")
        except Exception as exc:
            self._set_status("Error", fg="#fca5a5")
            error_text = str(exc)
            self._run_on_ui(lambda msg=error_text: messagebox.showerror("Error", msg))
        finally:
            self._set_download_enabled(True)
