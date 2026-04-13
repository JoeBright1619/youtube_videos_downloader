import tkinter as tk


class DownloaderUI:
    FONT_UI = "Segoe UI"

    def __init__(self, root: tk.Tk):
        self.root = root
        self._build()

    def _build(self):
        self.root.title("YouTube to MP3")
        self.root.geometry("520x360")
        self.root.minsize(520, 360)
        self.root.configure(bg="#0f172a")

        container = tk.Frame(self.root, bg="#0f172a")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(
            container,
            text="YouTube -> MP3 Downloader",
            bg="#0f172a",
            fg="#e5e5e5",
            font=(self.FONT_UI, 16, "bold"),
        ).pack(anchor="w")

        tk.Label(
            container,
            text="Paste one or multiple links (one URL per line).",
            bg="#0f172a",
            fg="#9ca3af",
            font=(self.FONT_UI, 9),
        ).pack(anchor="w", pady=(2, 10))

        entry_frame = tk.Frame(container, bg="#0f172a")
        entry_frame.pack(fill="x")

        self.entry = tk.Text(
            entry_frame,
            width=60,
            height=5,
            bg="#020617",
            fg="#e5e5e5",
            insertbackground="#e5e5e5",
            relief="flat",
            font=("Consolas", 10),
        )
        self.entry.pack(fill="x", pady=(0, 4))

        tk.Label(
            entry_frame,
            text="Example: https://www.youtube.com/watch?v=... or playlist URL",
            bg="#0f172a",
            fg="#6b7280",
            font=(self.FONT_UI, 8),
        ).pack(anchor="w")

        actions = tk.Frame(container, bg="#0f172a")
        actions.pack(fill="x", pady=(16, 8))

        self.choose_button = tk.Button(
            actions,
            text="Choose Folder",
            bg="#1f2933",
            fg="#e5e5e5",
            activebackground="#111827",
            activeforeground="#ffffff",
            relief="flat",
            padx=16,
            pady=6,
        )
        self.choose_button.pack(side="left")

        self.download_button = tk.Button(
            actions,
            text="Download",
            bg="#2563eb",
            fg="#f9fafb",
            activebackground="#1d4ed8",
            activeforeground="#f9fafb",
            relief="flat",
            padx=20,
            pady=6,
        )
        self.download_button.pack(side="right")

        self.folder_label = tk.Label(
            container,
            text="No folder selected",
            bg="#0f172a",
            fg="#6b7280",
            anchor="w",
            font=(self.FONT_UI, 9),
        )
        self.folder_label.pack(fill="x", pady=(4, 12))

        self.status_label = tk.Label(
            container,
            text="",
            bg="#0f172a",
            fg="#e5e5e5",
            justify="left",
            anchor="w",
            font=(self.FONT_UI, 9),
        )
        self.status_label.pack(fill="x", pady=(4, 0))

    def bind_actions(self, on_choose_folder, on_download):
        self.choose_button.config(command=on_choose_folder)
        self.download_button.config(command=on_download)

    def get_urls(self):
        return self.entry.get("1.0", tk.END).strip().split("\n")

    def set_folder_text(self, text: str, fg: str = "#e5e5e5"):
        self.folder_label.config(text=text, fg=fg)

    def set_status(self, text: str, fg: str = "#e5e5e5"):
        self.status_label.config(text=text, fg=fg)

    def set_download_enabled(self, enabled: bool):
        self.download_button.config(state="normal" if enabled else "disabled")
