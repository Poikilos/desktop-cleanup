from __future__ import print_function
import json
import os
import shutil
import sys

from collections import OrderedDict
from datetime import datetime
from logging import getLogger
from tkinter import ttk

if sys.version_info.major >= 3:
    import tkinter as tk
    from tkinter import messagebox
else:
    import Tkinter as tk  # type:ignore
    import tkMessageBox as messagebox  # type:ignore

import tksheet

from elevate import elevate

logger = getLogger(__name__)

if __name__ == "__main__":
    MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
    REPO_DIR = os.path.dirname(MODULE_DIR)
    sys.path.insert(0, REPO_DIR)  # manually emulate relative import


from desktopcleanup import (
    emit_cast,
)


class ShortcutFile:
    timestamp_keys = set()
    timestamp_keys.add("accessed")

    def __init__(self, name, path, parent, caption, accessed):
        self.name = name
        self.path = path
        self.parent = parent
        self.caption = caption
        self.accessed = accessed
        self.mark = False  # marked for cleanup
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                ShortcutFile.timestamp_keys.add(key)

    @classmethod
    def from_dict(cls, meta):
        if meta is None:
            raise ValueError("from_dict got None")
        item = ShortcutFile(None, None, None, None, None)
        for key, value in meta.items():
            if key.startswith("_"):
                continue
            if key in cls.timestamp_keys:
                value = datetime.fromtimestamp(value)
            setattr(item, key, value)
        return item

    def to_dict(self):
        result = {}
        for key, value in self.__dict__.items():
            if key.startswith("_"):
                continue
            if isinstance(value, datetime):
                value = value.timestamp()
            result[key] = value
        return result


class ShortcutCleaner:
    CLEANUP_ROOTS = {
        os.path.split(os.path.expanduser("~"))[1]:
            os.path.join(os.path.expanduser("~"), "Desktop"),
        "Public": os.path.join("C:\\", "Users", "Public", "Desktop"),
        # '\' required after ':' on Windows or join will result in a bad path
    }
    if not os.path.isdir(CLEANUP_ROOTS["Public"]):
        print("Ignoring missing {}".format(repr(CLEANUP_ROOTS["Public"])))
        del CLEANUP_ROOTS["Public"]  # probably not Windows, so skip
        # NOTE: May actually be:
        # from gi.repository import GLib
        # public_profile = \
        # GLib.get_user_special_dir(GLib.USER_DIRECTORY_PUBLIC_SHARE)

    def get_known_tmp(self):
        return os.path.join(os.path.expanduser("~"), "desktopcleanup.tmp")

    def __init__(self):
        self.shortcuts = OrderedDict()

    def scan(self):
        self.shortcuts.clear()
        for caption, parent in ShortcutCleaner.CLEANUP_ROOTS.items():
            self._scan_dir(parent, caption)
        self.shortcuts = OrderedDict(
            sorted(self.shortcuts.items(), key=lambda item: item[1].accessed)
        )

    def _scan_dir(self, parent, caption):
        for sub in os.listdir(parent):
            sub_path = os.path.join(parent, sub)
            if os.path.isdir(sub_path):
                continue
            if os.path.splitext(sub)[1].lower() in (".ini", ):
                continue
            if sub.startswith("."):
                continue
            accessed = datetime.fromtimestamp(os.path.getatime(sub_path))
            shortcut = ShortcutFile(sub, sub_path, parent, caption, accessed)
            self.shortcuts[sub_path] = shortcut

    def __getitem__(self, path):
        if not isinstance(path, str):
            raise KeyError("Expected str, got {}".format(emit_cast))
        return self.shortcuts[path]

    def clean_item(self, path):
        shortcut = self[path]  # get or raise KeyError
        dest_dir = os.path.join(ShortcutCleaner.CLEANUP_ROOTS[shortcut.caption], "Unused")
        if shortcut.caption == "Public":
            dest_dir += " Public Shortcuts"
        else:
            dest_dir += " Shortcuts"
        os.makedirs(dest_dir, exist_ok=True)
        dst_path = os.path.join(dest_dir, shortcut.name)
        print("mv {} {}".format(repr(shortcut.path), repr(dst_path)))
        shutil.move(shortcut.path, dst_path)
        del self.shortcuts[path]

# class FormatError(json.decoder.JSONDecodeError):
# ^ requires 2 positional arguments, doc and pos.
class FormatError(ValueError):
    pass

class ShortcutCleanerApp(tk.Tk):
    PATH_IDX = 4
    CHECK_IDX = 0

    def __init__(self):
        tk.Tk.__init__(self)
        self.root = self
        self.title("Desktop Cleanup")
        self.geometry("600x400")
        self.cleaner = ShortcutCleaner()
        self._create_widgets()
        self.enable_elevate = True
        if self.load_tmp():
            self.title("Desktop Cleanup (elevated)")
            self.clean_up()
            self.delete_tmp()

    def _create_widgets(self):
        self.scan_button = ttk.Button(self, text="Scan", command=self.scan)
        self.scan_button.pack(fill=tk.X)

        self.sheet = tksheet.Sheet(self)
        self.sheet.pack(fill=tk.BOTH, expand=True)
        self.sheet.headers([" ", "Name", "Accessed", "Location", "Path"])
        self.sheet.enable_bindings()

        self.clean_button = ttk.Button(self, text="Clean Up", command=self.clean_up)
        self.clean_button.pack(fill=tk.X)

    def scan(self):
        self.cleaner.scan()
        self.sheet.set_sheet_data([
            ["", s.name, s.accessed, s.parent, s.path] for s in self.cleaner.shortcuts.values()
        ])
        for row_idx in range(self.sheet.total_rows()):
            self.sheet.create_checkbox(row_idx, ShortcutCleanerApp.CHECK_IDX)
            # If not accessed lately:
            #     self.sheet.set_cell_data(row_idx, ShortcutCleanerApp.CHECK_IDX, True)

    def save_tmp(self):
        items = {}
        for row_idx in range(self.sheet.total_rows()):
            checked = \
                self.sheet.get_cell_data(row_idx, ShortcutCleanerApp.CHECK_IDX)
            path = self.sheet.get_cell_data(
                row_idx, ShortcutCleanerApp.PATH_IDX)
            self.cleaner[path].mark = checked
            items[path] = self.cleaner[path].to_dict()
        with open(self.cleaner.get_known_tmp(), 'w') as stream:
            json.dump(items, stream)
        return items

    def delete_tmp(self):
        if not os.path.isfile(self.cleaner.get_known_tmp()):
            return False
        os.remove(self.cleaner.get_known_tmp())

    def load_tmp(self):
        if not os.path.isfile(self.cleaner.get_known_tmp()):
            return False
        self.enable_elevate = False  # prevent infinite loop on error.
        self.cleaner.shortcuts = OrderedDict()
        bad_file = None
        with open(self.cleaner.get_known_tmp(), 'r') as stream:
            try:
                data = json.load(stream)
                if not data:
                    raise FormatError("Got None for json.load")
                for path, meta in data.items():
                    if meta is None:
                        raise FormatError(
                            "Got None a meta in json.load for {}"
                            .format(self.cleaner.get_known_tmp()))
                    self.cleaner.shortcuts[path] = \
                        ShortcutFile.from_dict(meta)
            except (json.decoder.JSONDecodeError, FormatError):
                bad_file = self.cleaner.get_known_tmp()
        if bad_file:
            logger.warning(
                "Removing bad tmp file {}".format(repr(bad_file)))
            os.remove(bad_file)
            return False

        self.sheet.set_sheet_data([
            ["", s.name, s.accessed, s.parent, s.path] for s in self.cleaner.shortcuts.values()
        ])
        for row_idx in range(self.sheet.total_rows()):
            self.sheet.create_checkbox(row_idx, ShortcutCleanerApp.CHECK_IDX)
            path = self.sheet.get_cell_data(row_idx, ShortcutCleanerApp.PATH_IDX)
            checked = self.cleaner[path].mark
            self.sheet.set_cell_data(row_idx, ShortcutCleanerApp.CHECK_IDX, checked)
        return True

    def clean_up(self):
        for row_idx in range(self.sheet.total_rows()):
            if not self.sheet.get_cell_data(row_idx, ShortcutCleanerApp.CHECK_IDX):
                continue  # not checked, don't clean
            path = self.sheet.get_cell_data(row_idx, ShortcutCleanerApp.PATH_IDX)
            try:
                self.cleaner.clean_item(path)
            except PermissionError as ex:
                self.save_tmp()
                if not self.enable_elevate:
                    # Probably an old tmp from a failed elevated run.
                    #   Delete tmp to prevent thinking elevated when not.
                    self.delete_tmp()
                    messagebox.showerror(
                        "Run as Administrator",
                        "{}: {}".format(type(ex).__name__, ex)
                    )
                    return
                self.root.withdraw()
                elevate()
                self.root.deiconify()
                sys.exit(0)
                try:
                    self.cleaner.clean_item(path)
                except PermissionError as ex:
                    messagebox.showerror(
                        "Run as Administrator",
                        "{}: {}".format(type(ex).__name__, ex)
                    )
                    return
            self.sheet.delete_row(row_idx)
            self.delete_tmp()


def main():
    try:
        app = ShortcutCleanerApp()
        app.mainloop()
    except Exception as ex:
        messagebox.showerror(
            "Unhandled Exception",
            emit_cast(ex)
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
