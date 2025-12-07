# InputLock v1.0.1

InputLock is a lightweight Windows utility for blocking custom key combinations in targeted applications. It integrates a Go-based low-level hook for reliable key blocking and a Python GUI for easy configuration. Key combinations can now be dynamically loaded from JSON, with targeted PID filtering and live updates.

---

## Features

* Select running processes to target, with PID dropdown and live refresh.
* Define custom key combinations to block, using `combos.json` for dynamic management.
* Supports manual selection, live key capture, and immediate combo persistence.
* Normalizes keys for consistent mapping across sessions.
* Delete combos directly from the GUI TreeView.
* Integrates a low-level Go hook (`hook.exe`) for reliable blocking.
* Dynamic combo engine replaces static Alt+Esc block.
* Minimizes to the system tray with restore and exit options (pystray removed for simplified lifecycle).
* Easy-to-use Python GUI built with Tkinter.
* Fully self-contained Python executable for easy distribution.

---

## Installation

### From Source

1. Clone this repository:

~~~
git clone git@github.com:fa1c0nx/InputLock.git
cd InputLock
~~~

2. Ensure PowerShell is running as Administrator if you want system-wide installations. Otherwise, user-local installations will be used.

3. Build the application using the provided PowerShell script:

~~~
.\build.ps1
~~~

This will automatically:

* Install Python 3.11+ if missing.
* Install Go if missing.
* Install Python dependencies.
* Build `InputLock.exe` and `hook.exe`.
* Place binaries in the `build/` folder.

---

### GitHub Release

For users who don’t want to build from source:

* Go to the [Releases](https://github.com/fa1c0nx/InputLock/releases) page.
* Download the latest `InputLock.zip`.
* Extract and run `InputLock.exe`. The required `hook.exe` will be included.

---

## Usage

1. Launch `InputLock.exe` as admin.
2. Select the target process from the PID dropdown.
3. Add, remove, or edit key combinations in the GUI.
4. Apply hooks to activate blocking.
5. Minimize to the system tray for background operation.
6. Restore or exit the application from the tray icon menu.

---

## Contributing

Contributions are welcome! Fork the repository, create a branch, and submit a pull request with your changes.

---

## License

This project is licensed under the **Do What The Fuck You Want To Public License (WTFPL)**. See `LICENSE.md` for details.
