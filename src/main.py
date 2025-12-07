import subprocess
import os
import atexit
import tkinter as tk
from tkinter import ttk, messagebox
import psutil
import keyboard
import json

root = tk.Tk()
root.title("InputLock v1.0.1 by fa1c0n")
root.geometry("650x550")
root.option_add("*Font", ("Segoe UI", 11))

COMBO_FILE = "combos.json"
combos = []
hook_active = False
hook_proc = None

if os.path.isfile(COMBO_FILE):
    with open(COMBO_FILE, "r") as f:
        try:
            combos = json.load(f)
        except:
            combos = []

def normalize_key(name):
    name = name.lower().strip()
    mapping = {
        "alt": "Alt", "left alt": "Alt", "right alt": "Alt", "lalt": "Alt", "ralt": "Alt",
        "ctrl": "Ctrl", "left ctrl": "Ctrl", "right ctrl": "Ctrl", "lctrl": "Ctrl", "rctrl": "Ctrl",
        "control": "Ctrl", "left control": "Ctrl", "right control": "Ctrl",
        "shift": "Shift", "left shift": "Shift", "right shift": "Shift", "lshift": "Shift", "rshift": "Shift",
        "esc": "Esc", "escape": "Esc",
        "win": "Win", "left win": "Win", "right win": "Win", "left windows": "Win", "right windows": "Win",
        "windows": "Win", "super": "Win",
        "tab": "Tab", "space": "Space", "enter": "Enter", "return": "Enter",
        "backspace": "Backspace", "delete": "Delete", "insert": "Insert",
        "home": "Home", "end": "End", "pageup": "PageUp", "pagedown": "PageDown",
        "up": "Up", "down": "Down", "left": "Left", "right": "Right",
        "capslock": "CapsLock", "caps lock": "CapsLock", "numlock": "NumLock", "scrolllock": "ScrollLock",
        "printscreen": "PrintScreen", "print screen": "PrintScreen", "prtsc": "PrintScreen",
        "pause": "Pause", "break": "Break",
    }
    if name in mapping:
        return mapping[name]
    if name.startswith("f") and name[1:].isdigit():
        return name.upper()
    if len(name) == 1 and name.isalnum():
        return name.upper()
    return name.upper()

processes = []

def refresh_processes():
    global processes
    processes = [f"{p.info['pid']} - {p.info['name']}" for p in psutil.process_iter(['name', 'pid'])]
    process_dropdown['values'] = processes

process_var = tk.StringVar()
process_frame = ttk.Frame(root)
process_frame.pack(pady=10, padx=10, fill='x')

process_dropdown = ttk.Combobox(process_frame, textvariable=process_var, width=50)
process_dropdown.pack(side=tk.LEFT, fill='x', expand=True)

ttk.Button(process_frame, text="↻", width=3, command=refresh_processes).pack(side=tk.LEFT, padx=5)

def update_process_dropdown(*args):
    typed = process_var.get().lower()
    filtered = [p for p in processes if typed in p.lower()]
    process_dropdown['values'] = filtered

process_var.trace_add("write", update_process_dropdown)
refresh_processes()

combo_tree = ttk.Treeview(root, columns=("Keys", "Delete"), show='headings', height=12)
combo_tree.heading("Keys", text="Key Combo")
combo_tree.heading("Delete", text="")
combo_tree.column("Keys", width=350)
combo_tree.column("Delete", width=50, anchor='center')
combo_tree.pack(padx=10, pady=10, fill='both', expand=True)

def save_combos():
    with open(COMBO_FILE, "w") as f:
        json.dump(combos, f, indent=2)

def update_combo_tree():
    combo_tree.delete(*combo_tree.get_children())
    for i, c in enumerate(combos):
        combo_tree.insert("", "end", iid=str(i), values=(c['keys'], "🗑"))
    save_combos()

def on_tree_click(event):
    region = combo_tree.identify_region(event.x, event.y)
    if region == "cell":
        col = combo_tree.identify_column(event.x)
        row = combo_tree.identify_row(event.y)
        if col == "#2" and row:
            idx = int(row)
            if 0 <= idx < len(combos):
                combos.pop(idx)
                update_combo_tree()

combo_tree.bind("<Button-1>", on_tree_click)
update_combo_tree()

QUICK_KEYS = ["Alt", "Esc", "Ctrl", "Shift", "Win", "Tab", "Space", "Enter"]

def capture_combo():
    selected_keys = set()
    keyboard_hooked = [True]
    
    cap = tk.Toplevel(root)
    cap.title("Capture Key Combo")
    cap.geometry("550x350")
    cap.transient(root)
    cap.grab_set()

    ttk.Label(cap, text="Press keys or click buttons below:", font=("Segoe UI", 10)).pack(pady=5)
    
    label = ttk.Label(cap, text="(none)", font=("Segoe UI", 14, "bold"), foreground="#0066cc")
    label.pack(pady=10)

    def update_label():
        if selected_keys:
            label.config(text=" + ".join(sorted(selected_keys)))
        else:
            label.config(text="(none)")

    frame = ttk.Frame(cap)
    frame.pack(pady=10)

    def toggle_key(key):
        if key in selected_keys:
            selected_keys.discard(key)
        else:
            selected_keys.add(key)
        update_label()

    for i, key in enumerate(QUICK_KEYS):
        row = i // 4
        col = i % 4
        btn = ttk.Button(frame, text=key, width=8, command=lambda k=key: toggle_key(k))
        btn.grid(row=row, column=col, padx=3, pady=3)

    def on_press(e):
        if not keyboard_hooked[0]:
            return
        key = normalize_key(e.name)
        if key and key not in selected_keys:
            selected_keys.add(key)
            update_label()

    keyboard.on_press(on_press)

    def clear_keys():
        selected_keys.clear()
        update_label()

    def save():
        if not selected_keys:
            messagebox.showwarning("No Keys", "Select at least one key!", parent=cap)
            return
        
        keyboard.unhook_all()
        keyboard_hooked[0] = False
        
        combo_str = " + ".join(sorted(selected_keys))
        combos.append({"keys": combo_str, "action": "Block"})
        update_combo_tree()
        cap.destroy()

    def cancel():
        keyboard.unhook_all()
        cap.destroy()

    btn_frame = ttk.Frame(cap)
    btn_frame.pack(pady=15)
    ttk.Button(btn_frame, text="Clear", command=clear_keys, width=10).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="Save", command=save, width=10).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="Cancel", command=cancel, width=10).pack(side=tk.LEFT, padx=5)

    cap.protocol("WM_DELETE_WINDOW", cancel)

def toggle_hooks():
    global hook_active, hook_proc
    hook_path = os.path.join(os.getcwd(), "hook.exe")
    
    if hook_active:
        if hook_proc:
            try:
                hook_proc.terminate()
                hook_proc.wait(timeout=2)
            except:
                try:
                    hook_proc.kill()
                except:
                    pass
            hook_proc = None
        hook_active = False
        hook_btn.config(text="Apply Hooks")
        status_label.config(text="Status: Inactive", foreground="gray")
        messagebox.showinfo("Hooks Stopped", "Keyboard hooks have been removed.")
    else:
        if not os.path.isfile(hook_path):
            messagebox.showerror("Missing File", "hook.exe not found!\nBuild it first using build.ps1")
            return
        
        try:
            pid = int(process_var.get().split(" - ")[0])
        except:
            messagebox.showerror("No Process", "Select a target process first!")
            return
        
        if not combos:
            messagebox.showwarning("No Combos", "Add at least one combo before applying hooks!")
            return
        
        save_combos()
        
        try:
            hook_proc = subprocess.Popen(
                [hook_path, str(pid)],
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
            )
            hook_active = True
            hook_btn.config(text="Stop Hooks")
            status_label.config(text=f"Status: Active (PID: {pid})", foreground="green")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start hook: {e}")

def cleanup_hook():
    global hook_proc
    if hook_proc:
        try:
            hook_proc.terminate()
            hook_proc.wait(timeout=1)
        except:
            try:
                hook_proc.kill()
            except:
                pass
        hook_proc = None

atexit.register(cleanup_hook)

def on_close():
    cleanup_hook()
    keyboard.unhook_all()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)

btn_frame = ttk.Frame(root)
btn_frame.pack(pady=10)

ttk.Button(btn_frame, text="Block Combo", command=capture_combo, width=15).pack(side=tk.LEFT, padx=5)
hook_btn = ttk.Button(btn_frame, text="Apply Hooks", command=toggle_hooks, width=15)
hook_btn.pack(side=tk.LEFT, padx=5)

status_label = ttk.Label(root, text="Status: Inactive", foreground="gray", font=("Segoe UI", 10))
status_label.pack(pady=5)

root.mainloop()
