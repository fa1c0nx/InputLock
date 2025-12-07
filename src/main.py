import subprocess
import os
import atexit
import tkinter as tk
from tkinter import ttk, messagebox
import psutil
import keyboard
import pystray
from PIL import ImageGrab, Image

root = tk.Tk()
root.title("InputLock v1.0.0 by fa1c0n")
root.geometry("600x500")
root.option_add("*Font", ("Segoe UI", 12))

combos = []
hook_active = False
hook_proc = None
tray_icon = None

# Process selection dropdown
processes = [f"{p.info['pid']} - {p.info['name']}" for p in psutil.process_iter(['name', 'pid'])]
process_var = tk.StringVar()
process_dropdown = ttk.Combobox(root, textvariable=process_var, values=processes, state='normal')
process_dropdown.pack(pady=10, padx=10, fill='x')

def update_process_dropdown(*args):
    typed = process_var.get().lower()
    filtered = [p for p in processes if typed in p.lower()]
    process_dropdown['values'] = filtered

process_var.trace_add("write", update_process_dropdown)

# Combo list
combo_tree = ttk.Treeview(root, columns=("Combo", "Action"), show='headings', height=10)
combo_tree.heading("Combo", text="Keys")
combo_tree.heading("Action", text="Action")
combo_tree.pack(padx=10, pady=10, fill='both', expand=True)

def update_combo_tree():
    combo_tree.delete(*combo_tree.get_children())
    for c in combos:
        combo_tree.insert("", "end", values=(c['keys'], c['action']))

def delete_combo():
    selected = combo_tree.selection()
    if not selected:
        return
    for item in selected:
        combos.pop(combo_tree.index(item))
    update_combo_tree()

# Capture + manual key selection
KEYS = ["Left Alt", "Esc", "Ctrl", "Left Win"]

def capture_combo():
    selected_keys = set()
    cap = tk.Toplevel(root)
    cap.title("Capture Key Combo")
    cap.geometry("500x300")

    label = ttk.Label(cap, text="", font=("Segoe UI", 12, "bold"))
    label.pack(pady=10)

    frame = ttk.Frame(cap)
    frame.pack(pady=10)

    for key in KEYS:
        ttk.Button(frame, text=key, width=10,
                   command=lambda k=key: toggle_key(k, selected_keys, label)).pack(side=tk.LEFT, padx=5)

    def on_press(e):
        name = e.name.lower()
        mapping = {
            "alt": "Left Alt", "left alt": "Left Alt", "lalt": "Left Alt",
            "ctrl": "Ctrl", "left ctrl": "Ctrl", "esc": "Esc",
            "win": "Left Win", "left windows": "Left Win", "left win": "Left Win",
        }
        selected_keys.add(mapping.get(name, name.upper()))
        label.config(text=" + ".join(sorted(selected_keys)))

    keyboard.hook(on_press)

    def save():
        if not selected_keys:
            messagebox.showwarning("No keys", "Select at least one key!")
            return
        combos.append({"keys": " + ".join(sorted(selected_keys)), "action": "Block"})
        update_combo_tree()
        keyboard.unhook_all()
        cap.destroy()

    ttk.Button(cap, text="Save Combo", command=save).pack(pady=15)

def toggle_key(key, selected_keys, label):
    if key in selected_keys:
        selected_keys.remove(key)
    else:
        selected_keys.add(key)
    label.config(text=" + ".join(sorted(selected_keys)))

# Hooks with Go subprocess
def apply_hooks():
    global hook_active, hook_proc
    if hook_active:
        messagebox.showwarning("Already active", "Hooks already active!")
        return

    hook_path = os.path.join(os.getcwd(), "hook.exe")
    if not os.path.isfile(hook_path):
        messagebox.showerror("hook.exe missing", "Go hook executable not found!")
        return

    hook_proc = subprocess.Popen([hook_path], creationflags=subprocess.CREATE_NO_WINDOW)
    hook_active = True
    messagebox.showinfo("Hooks Applied", "Go hook launched.")

def remove_hooks():
    global hook_active, hook_proc
    if not hook_active:
        return

    if hook_proc:
        try: hook_proc.terminate()
        except: pass
        hook_proc = None

    keyboard.unhook_all_hotkeys()
    hook_active = False
    messagebox.showinfo("Hooks Removed", "Hooks stopped.")

# Cleanup hook on exit
def cleanup_hook():
    global hook_proc
    if hook_proc:
        try: hook_proc.terminate()
        except: pass

atexit.register(cleanup_hook)

# System tray integration using Tk default icon
def get_tk_icon():
    root.update()
    x = root.winfo_rootx()
    y = root.winfo_rooty()
    w = x + 64
    h = y + 64
    return ImageGrab.grab(bbox=(x, y, w, h)).convert("RGBA")

def minimize_to_tray():
    global tray_icon
    root.withdraw()
    tray_icon = pystray.Icon(
        "InputLock",
        get_tk_icon(),
        "InputLock",
        menu=pystray.Menu(
            pystray.MenuItem("Restore", lambda: (root.deiconify(), tray_icon.stop())),
            pystray.MenuItem("Exit", lambda: (cleanup_hook(), tray_icon.stop(), root.destroy()))
        )
    )
    tray_icon.run()

root.protocol("WM_DELETE_WINDOW", minimize_to_tray)

# Buttons
btn_frame = ttk.Frame(root)
btn_frame.pack(pady=10)

ttk.Button(btn_frame, text="Add Combo (Capture + Manual)", command=capture_combo).pack(side=tk.LEFT, padx=5)
ttk.Button(btn_frame, text="Delete Combo", command=delete_combo).pack(side=tk.LEFT, padx=5)
ttk.Button(btn_frame, text="Apply Hooks", command=apply_hooks).pack(side=tk.LEFT, padx=5)
ttk.Button(btn_frame, text="Remove Hooks", command=remove_hooks).pack(side=tk.LEFT, padx=5)

root.mainloop()
