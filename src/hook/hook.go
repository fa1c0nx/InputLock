package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"os/signal"
	"strings"
	"sync"
	"syscall"
	"time"
	"unsafe"
)

var (
	user32                       = syscall.NewLazyDLL("user32.dll")
	procSetWindowsHookEx         = user32.NewProc("SetWindowsHookExW")
	procUnhookWindowsHookEx      = user32.NewProc("UnhookWindowsHookEx")
	procCallNextHookEx           = user32.NewProc("CallNextHookEx")
	procGetAsyncKeyState         = user32.NewProc("GetAsyncKeyState")
	procGetForegroundWindow      = user32.NewProc("GetForegroundWindow")
	procGetWindowThreadProcessId = user32.NewProc("GetWindowThreadProcessId")
	procGetMessageW              = user32.NewProc("GetMessageW")
)

const (
	WH_KEYBOARD_LL  = 13
	WM_KEYDOWN      = 0x0100
	WM_SYSKEYDOWN   = 0x0104
)

type KBDLLHOOKSTRUCT struct {
	VkCode      uint32
	ScanCode    uint32
	Flags       uint32
	Time        uint32
	DwExtraInfo uintptr
}

type MSG struct {
	Hwnd    uintptr
	Message uint32
	WParam  uintptr
	LParam  uintptr
	Time    uint32
	Pt      struct{ X, Y int32 }
}

type Combo struct {
	Keys   string   `json:"keys"`
	Action string   `json:"action"`
	VKKeys []uint32 `json:"-"`
}

var (
	combos     []Combo
	comboFile  = "combos.json"
	comboMutex sync.RWMutex
	targetPID  uint32
	hookHandle uintptr
)

var vkMap = map[string]uint32{
	"ESC": 0x1B, "ESCAPE": 0x1B,
	"TAB": 0x09,
	"CAPSLOCK": 0x14,
	"SHIFT": 0x10, "LSHIFT": 0xA0, "RSHIFT": 0xA1,
	"CTRL": 0x11, "CONTROL": 0x11, "LCTRL": 0xA2, "RCTRL": 0xA3,
	"ALT": 0x12, "MENU": 0x12, "LALT": 0xA4, "RALT": 0xA5,
	"WIN": 0x5B, "LWIN": 0x5B, "RWIN": 0x5C,
	"SPACE": 0x20,
	"ENTER": 0x0D, "RETURN": 0x0D,
	"BACKSPACE": 0x08,
	"DELETE": 0x2E, "DEL": 0x2E,
	"INSERT": 0x2D, "INS": 0x2D,
	"HOME": 0x24, "END": 0x23,
	"PAGEUP": 0x21, "PGUP": 0x21,
	"PAGEDOWN": 0x22, "PGDN": 0x22,
	"UP": 0x26, "DOWN": 0x28, "LEFT": 0x25, "RIGHT": 0x27,
	"PRINTSCREEN": 0x2C, "PRTSC": 0x2C,
	"SCROLLLOCK": 0x91, "NUMLOCK": 0x90,
	"PAUSE": 0x13,
	"F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73,
	"F5": 0x74, "F6": 0x75, "F7": 0x76, "F8": 0x77,
	"F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
	"0": 0x30, "1": 0x31, "2": 0x32, "3": 0x33, "4": 0x34,
	"5": 0x35, "6": 0x36, "7": 0x37, "8": 0x38, "9": 0x39,
}

func keyToVK(key string) uint32 {
	key = strings.TrimSpace(strings.ToUpper(key))
	if vk, ok := vkMap[key]; ok {
		return vk
	}
	if len(key) == 1 {
		c := key[0]
		if c >= 'A' && c <= 'Z' {
			return uint32(c)
		}
		if c >= '0' && c <= '9' {
			return uint32(c)
		}
	}
	if strings.HasPrefix(key, "F") && len(key) <= 3 {
		var n int
		if _, err := fmt.Sscanf(key, "F%d", &n); err == nil && n >= 1 && n <= 24 {
			return 0x70 + uint32(n-1)
		}
	}
	return 0
}

func loadCombos() {
	data, err := ioutil.ReadFile(comboFile)
	if err != nil {
		fmt.Println("Error reading combos:", err)
		return
	}
	var list []Combo
	if err := json.Unmarshal(data, &list); err != nil {
		fmt.Println("Error parsing combos:", err)
		return
	}
	for i := range list {
		parts := strings.Split(list[i].Keys, " + ")
		list[i].VKKeys = nil
		for _, p := range parts {
			vk := keyToVK(p)
			if vk != 0 {
				list[i].VKKeys = append(list[i].VKKeys, vk)
			}
		}
	}
	comboMutex.Lock()
	combos = list
	comboMutex.Unlock()
	fmt.Printf("Loaded %d combos\n", len(list))
	for _, c := range list {
		fmt.Printf("  %s (VKs: %v)\n", c.Keys, c.VKKeys)
	}
}

func watchFile() {
	var lastMod int64
	for {
		info, err := os.Stat(comboFile)
		if err == nil {
			ts := info.ModTime().Unix()
			if ts != lastMod {
				lastMod = ts
				loadCombos()
			}
		}
		time.Sleep(time.Second)
	}
}

func getForegroundPID() uint32 {
	hwnd, _, _ := procGetForegroundWindow.Call()
	if hwnd == 0 {
		return 0
	}
	var pid uint32
	procGetWindowThreadProcessId.Call(hwnd, uintptr(unsafe.Pointer(&pid)))
	return pid
}

func isKeyPressed(vk uint32) bool {
	ret, _, _ := procGetAsyncKeyState.Call(uintptr(vk))
	return (ret & 0x8000) != 0
}

func isModifierPressed(vk uint32) bool {
	switch vk {
	case 0x10:
		return isKeyPressed(0xA0) || isKeyPressed(0xA1)
	case 0x11:
		return isKeyPressed(0xA2) || isKeyPressed(0xA3)
	case 0x12:
		return isKeyPressed(0xA4) || isKeyPressed(0xA5)
	case 0x5B:
		return isKeyPressed(0x5B) || isKeyPressed(0x5C)
	default:
		return isKeyPressed(vk)
	}
}

func comboMatches(c *Combo, currentVK uint32) bool {
	hasCurrentKey := false
	for _, vk := range c.VKKeys {
		if vk == currentVK {
			hasCurrentKey = true
			break
		}
	}
	if !hasCurrentKey {
		return false
	}
	for _, vk := range c.VKKeys {
		if vk == currentVK {
			continue
		}
		if !isModifierPressed(vk) {
			return false
		}
	}
	return true
}

func LowLevelKeyboardProc(nCode int, wParam uintptr, lParam uintptr) uintptr {
	if nCode >= 0 {
		kbStruct := (*KBDLLHOOKSTRUCT)(unsafe.Pointer(lParam))
		currentVK := kbStruct.VkCode
		isKeyDown := wParam == WM_KEYDOWN || wParam == WM_SYSKEYDOWN

		if isKeyDown && getForegroundPID() == targetPID {
			comboMutex.RLock()
			for i := range combos {
				c := &combos[i]
				if len(c.VKKeys) == 0 {
					continue
				}
				if comboMatches(c, currentVK) {
					comboMutex.RUnlock()
					fmt.Printf("Blocked: %s\n", c.Keys)
					return 1
				}
			}
			comboMutex.RUnlock()
		}
	}
	ret, _, _ := procCallNextHookEx.Call(hookHandle, uintptr(nCode), wParam, lParam)
	return ret
}

func cleanup() {
	if hookHandle != 0 {
		procUnhookWindowsHookEx.Call(hookHandle)
		fmt.Println("Hook uninstalled")
	}
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: hook.exe <PID>")
		os.Exit(1)
	}

	if _, err := fmt.Sscanf(os.Args[1], "%d", &targetPID); err != nil {
		fmt.Println("Invalid PID:", os.Args[1])
		os.Exit(1)
	}

	fmt.Printf("Starting hook for PID: %d\n", targetPID)

	loadCombos()
	go watchFile()

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-sigChan
		cleanup()
		os.Exit(0)
	}()

	handle, _, err := procSetWindowsHookEx.Call(
		uintptr(WH_KEYBOARD_LL),
		syscall.NewCallback(LowLevelKeyboardProc),
		0,
		0,
	)

	if handle == 0 {
		fmt.Println("Failed to set hook:", err)
		os.Exit(1)
	}

	hookHandle = handle
	fmt.Println("Hook installed successfully")

	var msg MSG
	for {
		ret, _, _ := procGetMessageW.Call(uintptr(unsafe.Pointer(&msg)), 0, 0, 0)
		if ret == 0 {
			break
		}
	}

	cleanup()
}
