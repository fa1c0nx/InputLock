package main

import (
	"syscall"
	"unsafe"
)

var (
	user32             = syscall.NewLazyDLL("user32.dll")
	procSetWindowsHook = user32.NewProc("SetWindowsHookExW")
	procCallNextHook   = user32.NewProc("CallNextHookEx")
	procGetAsync       = user32.NewProc("GetAsyncKeyState")
	procGetMessage     = user32.NewProc("GetMessageW")

	WH_KEYBOARD_LL = 13
	VK_ESCAPE      = uint32(0x1B)
	VK_MENU        = uint32(0x12) // ALT
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

func LowLevelKeyboardProc(nCode int, wParam uintptr, lParam uintptr) uintptr {
	if nCode >= 0 {
		kb := (*KBDLLHOOKSTRUCT)(unsafe.Pointer(lParam))

		if kb.VkCode == VK_ESCAPE {
			state, _, _ := procGetAsync.Call(uintptr(VK_MENU))
			if state&0x8000 != 0 {
				// Block Alt+Esc instantly
				return 1
			}
		}
	}

	ret, _, _ := procCallNextHook.Call(0, uintptr(nCode), wParam, lParam)
	return ret
}

func main() {
	hook, _, _ := procSetWindowsHook.Call(
		uintptr(WH_KEYBOARD_LL),
		syscall.NewCallback(LowLevelKeyboardProc),
		0,
		0,
	)

	var msg MSG
	for {
		procGetMessage.Call(uintptr(unsafe.Pointer(&msg)), 0, 0, 0)
	}

	_ = hook
}
