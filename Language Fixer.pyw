"""Language Fixer settings window for Windows."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import tkinter as tk
from tkinter import messagebox, ttk


FOLDER = Path(__file__).resolve().parent
CONFIG = Path(os.environ["LOCALAPPDATA"]) / "Language Fixer" / "languages.json"
POWERSHELL = Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"


def windows_action(action, *arguments):
    result = subprocess.run(
        [str(POWERSHELL), "-NoProfile", "-NonInteractive", "-ExecutionPolicy",
         "Bypass", "-File", str(FOLDER / "Language-Fixer.ps1"), "-Action",
         action, *arguments],
        capture_output=True, encoding="utf-8", errors="replace",
        creationflags=subprocess.CREATE_NO_WINDOW, timeout=30,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"Windows returned {result.returncode}.")
    return result.stdout.strip()


def save_languages(tags):
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=CONFIG.parent, delete=False
    ) as stream:
        temporary = Path(stream.name)
        json.dump(tags, stream)
    try:
        temporary.replace(CONFIG)
    finally:
        temporary.unlink(missing_ok=True)


class LanguagePanel:
    def __init__(self, root, state):
        self.root = root
        self.catalog = sorted(state["catalog"], key=lambda entry: entry["name"].casefold())
        self.entries = {entry["tag"]: entry for entry in self.catalog}
        self.tags = (
            json.loads(CONFIG.read_text(encoding="utf-8-sig"))
            if CONFIG.exists() else state["languages"]
        )
        self.matches = []
        self.query = tk.StringVar()
        self.status = tk.StringVar(value=(
            "Automatic checks are on · every minute"
            if state["enabled"] else "Automatic checks are off"
        ))

        root.title("Language Fixer")
        root.geometry("820x545")
        root.minsize(650, 420)
        root.configure(background="#eef3fb")
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TFrame", background="#eef3fb")
        style.configure("TLabel", background="#eef3fb", foreground="#17263d",
                        font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 25, "bold"))
        style.configure("Section.TLabel", font=("Segoe UI", 11, "bold"))
        style.configure("TButton", padding=(12, 7), font=("Segoe UI", 10))
        style.configure("Accent.TButton", background="#2458c5", foreground="white")
        style.map("Accent.TButton", background=[("active", "#1947ac")])

        content = ttk.Frame(root, padding=24)
        content.pack(fill="both", expand=True)
        ttk.Label(content, text="Language Fixer", style="Title.TLabel").pack(anchor="w")
        ttk.Label(content, text="Choose which keyboard languages Windows should keep.").pack(
            anchor="w", pady=(3, 18)
        )
        columns = ttk.Frame(content)
        columns.pack(fill="both", expand=True)
        columns.columnconfigure((0, 1), weight=1, uniform="languages")
        columns.rowconfigure(0, weight=1)
        left = ttk.Frame(columns)
        right = ttk.Frame(columns)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        ttk.Label(left, text="Find a language", style="Section.TLabel").pack(anchor="w")
        search = ttk.Entry(left, textvariable=self.query, font=("Segoe UI", 11))
        search.pack(fill="x", pady=(7, 5), ipady=4)
        self.hint = ttk.Label(left)
        self.hint.pack(anchor="w", pady=(0, 5))
        self.results = self.make_list(left)
        self.add_button = ttk.Button(left, text="Add language", command=self.add)
        self.add_button.pack(anchor="w", pady=(8, 0))

        ttk.Label(right, text="Languages to keep", style="Section.TLabel").pack(anchor="w")
        ttk.Label(right, text="These languages stay in your keyboard menu.").pack(
            anchor="w", pady=(12, 15)
        )
        self.selected = self.make_list(right)
        ttk.Button(right, text="Remove selected", command=self.remove).pack(
            anchor="w", pady=(8, 0)
        )

        footer = ttk.Frame(content)
        footer.pack(fill="x", pady=(18, 0))
        ttk.Label(footer, textvariable=self.status).pack(side="left")
        ttk.Button(footer, text="Save and enable", style="Accent.TButton",
                   command=self.save).pack(side="right")
        ttk.Button(footer, text="Disable", command=self.disable).pack(side="right", padx=8)
        self.query.trace_add("write", self.filter)
        self.results.bind("<Double-Button-1>", self.add)
        self.results.bind("<Return>", self.add)
        search.bind("<Return>", self.add)
        self.selected.bind("<Delete>", self.remove)
        self.refresh_selected()
        self.filter()
        search.focus_set()

    @staticmethod
    def make_list(parent):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")
        listing = tk.Listbox(
            frame, height=8, borderwidth=0, highlightthickness=1,
            highlightbackground="#cbd7e8", highlightcolor="#2458c5",
            background="white", foreground="#17263d", selectbackground="#2458c5",
            font=("Segoe UI", 11), exportselection=False, yscrollcommand=scrollbar.set,
        )
        listing.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=listing.yview)
        return listing

    def filter(self, *_):
        query = self.query.get().strip().casefold()
        self.matches = [
            entry for entry in self.catalog
            if any(query in entry[field].casefold() for field in ("tag", "name", "native"))
        ]
        self.results.delete(0, tk.END)
        for entry in self.matches:
            self.results.insert(tk.END, f'{entry["name"]}  ·  {entry["tag"]}')
        if self.matches:
            self.results.selection_set(0)
        self.add_button.configure(state="normal" if self.matches else "disabled")
        self.hint.configure(text=f"{len(self.matches)} languages" if self.matches else "No matches")

    def refresh_selected(self):
        self.selected.delete(0, tk.END)
        for tag in self.tags:
            name = self.entries.get(tag, {}).get("name", tag)
            self.selected.insert(tk.END, f"{name}  ·  {tag}")

    def add(self, _event=None):
        selection = self.results.curselection()
        if not selection:
            return
        try:
            tag = windows_action("Resolve", "-LanguageTag", self.matches[selection[0]]["tag"])
            if not tag:
                raise ValueError("Windows did not recognize this input language.")
            if tag not in self.tags:
                self.tags.append(tag)
                self.refresh_selected()
            self.selected.selection_clear(0, tk.END)
            index = self.tags.index(tag)
            self.selected.selection_set(index)
            self.selected.see(index)
        except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
            self.show_error(error)

    def remove(self, _event=None):
        selection = self.selected.curselection()
        if selection:
            del self.tags[selection[0]]
            self.refresh_selected()

    def save(self):
        try:
            if not self.tags:
                raise ValueError("Keep at least one language.")
            save_languages(self.tags)
            windows_action("Enable")
            self.status.set("Applied · automatic checks are on")
        except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
            self.show_error(error)

    def disable(self):
        try:
            windows_action("Disable")
            self.status.set("Automatic checks are off")
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
            self.show_error(error)

    def show_error(self, error):
        messagebox.showerror("Language Fixer", str(error), parent=self.root)


def main():
    root = tk.Tk()
    root.withdraw()
    try:
        LanguagePanel(root, json.loads(windows_action("Read")))
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        messagebox.showerror("Language Fixer", str(error), parent=root)
        root.destroy()
        return
    root.deiconify()
    root.mainloop()


if __name__ == "__main__":
    main()
