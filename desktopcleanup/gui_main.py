from __future__ import print_function
import os
import sys
import shutil
import tkinter as tk
from collections import OrderedDict
from datetime import datetime
from tkinter import ttk
import tksheet


class ShortcutFile:
    def __init__(self, name, path, parent, caption, accessed):
        self.name = name
        self.path = path
        self.parent = parent
        self.caption = caption
        self.accessed = accessed


class ShortcutCleaner:
    CLEANUP_ROOTS = {
        os.path.split(os.path.expanduser("~"))[1]: os.path.expanduser("~/Desktop"),
        "Public": "C:\\Users\\Public\\Desktop"
    }

    def __init__(self):
        self.shortcuts = OrderedDict()

    def scan(self):
        self.shortcuts.clear()
        for caption, parent in self.CLEANUP_ROOTS.items():
            self._scan_dir(parent, caption)
        self.shortcuts = OrderedDict(
            sorted(self.shortcuts.items(), key=lambda item: item[1].accessed)
        )

    def _scan_dir(self, parent, caption):
        for sub in os.listdir(parent):
            sub_path = os.path.join(parent, sub)
            if os.path.isdir(sub_path):
                continue
            accessed = datetime.fromtimestamp(os.path.getatime(sub_path))
            shortcut = ShortcutFile(sub, sub_path, parent, caption, accessed)
            self.shortcuts[sub_path] = shortcut

    def clean_item(self, path):
        shortcut = self.shortcuts.get(path)
        if not shortcut:
            return
        dest_dir = os.path.join(self.CLEANUP_ROOTS[shortcut.caption], "Unused")
        if shortcut.caption == "Public":
            dest_dir += " Public Shortcuts"
        else:
            dest_dir += " Shortcuts"
        os.makedirs(dest_dir, exist_ok=True)
        shutil.move(shortcut.path, os.path.join(dest_dir, shortcut.name))
        del self.shortcuts[path]


class ShortcutCleanerApp(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Shortcut Cleaner")
        self.geometry("600x400")
        self.cleaner = ShortcutCleaner()
        self._create_widgets()

    def _create_widgets(self):
        self.scan_button = ttk.Button(self, text="Scan", command=self.scan)
        self.scan_button.pack(fill=tk.X)

        self.sheet = tksheet.Sheet(self)
        self.sheet.pack(fill=tk.BOTH, expand=True)
        self.sheet.headers(["Name", "Location", "Path"])
        self.sheet.enable_bindings()
        self.sheet.set_checkboxes()

        self.clean_button = ttk.Button(self, text="Clean Up", command=self.clean_up)
        self.clean_button.pack(fill=tk.X)

    def scan(self):
        self.cleaner.scan()
        self.sheet.set_sheet_data([
            [s.name, s.parent, s.path] for s in self.cleaner.shortcuts.values()
        ])
        self.sheet.set_checked_rows([])

    def clean_up(self):
        checked_rows = self.sheet.get_checked_rows()
        data = self.sheet.get_sheet_data()
        for row in sorted(checked_rows, reverse=True):
            path = data[row][2]
            self.cleaner.clean_item(path)
            self.sheet.delete_row(row)


def main():
    app = ShortcutCleanerApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
