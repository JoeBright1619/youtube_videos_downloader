import tkinter as tk

from controller import DownloadController
from platform_utils import apply_tk_scaling, enable_high_dpi
from ui import DownloaderUI


def main():
    enable_high_dpi()

    root = tk.Tk()
    apply_tk_scaling(root)

    ui = DownloaderUI(root)
    controller = DownloadController(ui)
    ui.bind_actions(controller.choose_folder, controller.start_download)

    root.mainloop()


if __name__ == "__main__":
    main()