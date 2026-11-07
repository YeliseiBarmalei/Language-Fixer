# Language Fixer

Language Fixer keeps the keyboard input languages you choose in Windows. It checks your list at sign-in and once a minute while you are signed in. Checks run without a console window.

## Requirements

- Windows with Windows PowerShell 5.1, Windows Script Host, and Task Scheduler
- Python 3.10 or newer for Windows with Tkinter and a working `pyw.exe` or `pythonw.exe` launcher

The panel uses the Python standard library. There are no packages to install with pip.

## Get started

1. Download the ZIP from GitHub and extract it, or clone the repository. Keep all the files together in a folder you plan to keep.
2. Double-click **Language Fixer.vbs**. On first launch, the panel lists your current Windows input languages under **Languages to keep**.
3. Search by language name or code, such as `Polish` or `pl`. Select a result and click **Add language**. Use **Remove selected** to take a language off the keep list.
4. Click **Save and enable**. This saves your selection and starts the first check. Task Scheduler runs subsequent checks for your Windows account.

You can also open **Language Fixer.pyw** directly if Windows associates it with Python, or run `pythonw.exe "Language Fixer.pyw"` from the project folder.

## How it works

Each check removes input languages outside your saved list and adds any missing languages from that list. The app preserves existing keyboard layouts for languages you keep. Windows may keep an extra layout visible while it is in use, even after the app tries to unload it.

Your selection is stored in `%LOCALAPPDATA%\Language Fixer\languages.json`. If you move the project folder, open the panel from the new location and click **Save and enable** again so the scheduled task points to the new location.

## Disable or uninstall

Click **Disable** to stop automatic checks. To uninstall, delete the **Language Fixer** task from the Task Scheduler Library, then delete the project folder. To clear your saved selection as well, remove `%LOCALAPPDATA%\Language Fixer\languages.json`.
