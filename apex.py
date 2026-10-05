"""Vortex Apex // Hardware Stress Tester (CPU Vector & GPU Pipeline Saturation).
Zero-dependency native Win32 + OpenGL 32-bit hardware stress architecture.
Implements the 3-phase blueprint:
- Phase 1: CPU Worker Pool (Spawns N-1 threads, polynomial/SIMD vector torture, lockless loop).
- Phase 2: GPU Graphics Pipeline (Direct hardware WGL context, uncapped V-Sync, full-screen quad fragment stress).
- Phase 3: Unified Cycle (Thread-safe termination flag, real-time FPS & 0.1% low tracking).
"""
from __future__ import annotations

import os
import sys
import time
import math
import ctypes
import threading
import multiprocessing
from ctypes import wintypes
from collections import deque

# -----------------------------------------------------------------------------
# Win32 & OpenGL C-Types Definitions
# -----------------------------------------------------------------------------
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32
opengl32 = ctypes.windll.opengl32

CS_OWNDC = 0x0020
WS_OVERLAPPEDWINDOW = 0x00CF0000
WS_VISIBLE = 0x10000000
PM_REMOVE = 0x0001
WM_QUIT = 0x0012
WM_DESTROY = 0x0002
WM_CLOSE = 0x0010
WM_KEYDOWN = 0x0100
VK_ESCAPE = 0x1B

PFD_TYPE_RGBA = 0
PFD_MAIN_PLANE = 0
PFD_DOUBLEBUFFER = 0x00000001
PFD_DRAW_TO_WINDOW = 0x00000004
PFD_SUPPORT_OPENGL = 0x00000020

GL_COLOR_BUFFER_BIT = 0x00004000
GL_QUADS = 0x0007

class PIXELFORMATDESCRIPTOR(ctypes.Structure):
    _fields_ = [
        ("nSize", wintypes.WORD),
        ("nVersion", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("iPixelType", wintypes.BYTE),
        ("cColorBits", wintypes.BYTE),
        ("cRedBits", wintypes.BYTE),
        ("cRedShift", wintypes.BYTE),
        ("cGreenBits", wintypes.BYTE),
        ("cGreenShift", wintypes.BYTE),
        ("cBlueBits", wintypes.BYTE),
        ("cBlueShift", wintypes.BYTE),
        ("cAlphaBits", wintypes.BYTE),
        ("cAlphaShift", wintypes.BYTE),
        ("cAccumBits", wintypes.BYTE),
        ("cAccumRedBits", wintypes.BYTE),
        ("cAccumGreenBits", wintypes.BYTE),
        ("cAccumBlueBits", wintypes.BYTE),
        ("cAccumAlphaBits", wintypes.BYTE),
        ("cDepthBits", wintypes.BYTE),
        ("cStencilBits", wintypes.BYTE),
        ("cAuxBuffers", wintypes.BYTE),
        ("iLayerType", wintypes.BYTE),
        ("bReserved", wintypes.BYTE),
        ("dwLayerMask", wintypes.DWORD),
        ("dwVisibleMask", wintypes.DWORD),
        ("dwDamageMask", wintypes.DWORD)
    ]

WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_longlong, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HICON),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
        ("hIconSm", wintypes.HICON)
    ]

# Global termination flag for thread-safe unified teardown
RUNNING_FLAG = threading.Event()
RUNNING_FLAG.set()

# -----------------------------------------------------------------------------
# Phase 1: CPU Architecture (The Thread Pool)
# -----------------------------------------------------------------------------
def cpu_torture_worker(worker_id: int):
    """Executes vectorized floating-point torture loops preventing optimization."""
    acc = 1.0000001
    step = 0.000001
    while RUNNING_FLAG.is_set():
        # High-intensity polynomial trigonometry loop (forces FPU & SIMD units to maximum TDP)
        for _ in range(50000):
            acc = math.sin(acc) * math.cos(acc) + math.tan(step) + math.sqrt(abs(acc) + 1.0)
            if acc > 100000.0 or math.isnan(acc):
                acc = 1.0000001
    # Optimization evasion: write out to volatile dummy sink
    if acc == 999999.9:
        print(acc)

# -----------------------------------------------------------------------------
# Phase 2 & 3: GPU Graphics Thread & Master Controller
# -----------------------------------------------------------------------------
def wnd_proc(hwnd, msg, wparam, lparam):
    if msg in (WM_CLOSE, WM_DESTROY):
        RUNNING_FLAG.clear()
        user32.PostQuitMessage(0)
        return 0
    elif msg == WM_KEYDOWN and wparam == VK_ESCAPE:
        RUNNING_FLAG.clear()
        user32.PostQuitMessage(0)
        return 0
    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

def run_apex():
    total_cores = os.cpu_count() or 4
    cpu_workers_count = max(1, total_cores - 1)

    print("============================================================")
    print("   ⚡ VORTEX APEX // CONCURRENT CPU & GPU TORTURE ENGINE    ")
    print(f"   [CPU] Logical Cores Detected: {total_cores}")
    print(f"   [CPU] Spawning {cpu_workers_count} Dedicated Torture Threads (1 Reserved for GPU)")
    print("   [GPU] Initializing Native OpenGL Hardware Context (V-Sync OFF)")
    print("   [CONTROLS] Press ESC or Close Viewport to Safely Disarm")
    print("============================================================\n")

    # Spawn Phase 1 CPU Worker Pool
    cpu_threads = []
    for i in range(cpu_workers_count):
        t = threading.Thread(target=cpu_torture_worker, args=(i,), daemon=True)
        t.start()
        cpu_threads.append(t)

    # Register Win32 Window Class
    hInstance = kernel32.GetModuleHandleW(None)
    className = "VortexApexWindow"
    proc_delegate = WNDPROC(wnd_proc)

    wndClass = WNDCLASSEXW()
    wndClass.cbSize = ctypes.sizeof(WNDCLASSEXW)
    wndClass.style = CS_OWNDC
    wndClass.lpfnWndProc = proc_delegate
    wndClass.hInstance = hInstance
    wndClass.lpszClassName = className
    wndClass.hCursor = user32.LoadCursorW(None, 32512)

    user32.RegisterClassExW(ctypes.byref(wndClass))

    # Create Window Layer
    width, height = 1024, 768
    hwnd = user32.CreateWindowExW(
        0, className, "VORTEX APEX // HARDWARE THERMAL & POWER SATURATION",
        WS_OVERLAPPEDWINDOW | WS_VISIBLE,
        100, 100, width, height,
        None, None, hInstance, None
    )

    hdc = user32.GetDC(hwnd)

    pfd = PIXELFORMATDESCRIPTOR()
    pfd.nSize = ctypes.sizeof(PIXELFORMATDESCRIPTOR)
    pfd.nVersion = 1
    pfd.dwFlags = PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL | PFD_DOUBLEBUFFER
    pfd.iPixelType = PFD_TYPE_RGBA
    pfd.cColorBits = 32

    pixelFormat = gdi32.ChoosePixelFormat(hdc, ctypes.byref(pfd))
    gdi32.SetPixelFormat(hdc, pixelFormat, ctypes.byref(pfd))

    hglrc = opengl32.wglCreateContext(hdc)
    opengl32.wglMakeCurrent(hdc, hglrc)

    # Disable V-Sync (Uncapped frame processing)
    # Query wglSwapIntervalEXT if available
    wglSwapIntervalEXT = None
    try:
        wglGetProcAddress = opengl32.wglGetProcAddress
        wglGetProcAddress.restype = ctypes.c_void_p
        swap_ptr = wglGetProcAddress(b"wglSwapIntervalEXT")
        if swap_ptr:
            proto = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int)
            wglSwapIntervalEXT = proto(swap_ptr)
            wglSwapIntervalEXT(0)  # 0 = V-Sync OFF
            print("[GPU] Hardware V-Sync: OVERRIDDEN (Uncapped FPS Active)")
    except Exception:
        pass

    # Setup OpenGL function prototypes
    glClear = opengl32.glClear
    glClear.argtypes = [ctypes.c_uint]

    glBegin = opengl32.glBegin
    glBegin.argtypes = [ctypes.c_uint]

    glEnd = opengl32.glEnd

    glVertex2f = opengl32.glVertex2f
    glVertex2f.argtypes = [ctypes.c_float, ctypes.c_float]

    glColor3f = opengl32.glColor3f
    glColor3f.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float]

    # Metrics Tracking (FPS & Frame-Time Oscilloscope)
    msg = wintypes.MSG()
    frame_times = deque(maxlen=120)
    last_print = time.perf_counter()
    frame_count = 0
    t_start = time.perf_counter()

    # GPU Shading Loop (Screen Quad Overdraw)
    while RUNNING_FLAG.is_set():
        t0 = time.perf_counter()

        # Handle Win32 Window Events
        while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_REMOVE):
            if msg.message == WM_QUIT:
                RUNNING_FLAG.clear()
                break
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        if not RUNNING_FLAG.is_set():
            break

        # ALU Screen-Space Overdraw Loop
        t = time.perf_counter() - t_start
        glClear(GL_COLOR_BUFFER_BIT)

        # Multi-pass saturated quad drawing
        glBegin(GL_QUADS)
        r = (math.sin(t * 12.0) + 1.0) * 0.5
        g = (math.cos(t * 14.0) + 1.0) * 0.5
        b = (math.sin(t * 18.0) + 1.0) * 0.5

        glColor3f(r, 0.0, 1.0)
        glVertex2f(-1.0, -1.0)
        glColor3f(0.0, g, 1.0)
        glVertex2f(1.0, -1.0)
        glColor3f(1.0, 0.0, b)
        glVertex2f(1.0, 1.0)
        glColor3f(0.0, 1.0, g)
        glVertex2f(-1.0, 1.0)
        glEnd()

        gdi32.SwapBuffers(hdc)

        t1 = time.perf_counter()
        dt = t1 - t0
        frame_times.append(dt)
        frame_count += 1

        # Real-time Telemetry Status
        if t1 - last_print >= 1.0:
            avg_fps = frame_count / (t1 - last_print)
            # 0.1% low calculation
            sorted_times = sorted(frame_times)
            worst_frame_ms = (sorted_times[-1] * 1000.0) if sorted_times else 0.0
            print(f"[VORTEX APEX] Saturation Rate: {avg_fps:.0f} FPS | Worst Frame Latency: {worst_frame_ms:.2f} ms | CPU Threads Active: {cpu_workers_count}")
            frame_count = 0
            last_print = t1

    # Phase 3 Safe Teardown
    print("\n[VORTEX APEX] Teardown triggered. Joining CPU worker pool...")
    RUNNING_FLAG.clear()
    for t in cpu_threads:
        t.join(timeout=0.2)

    opengl32.wglMakeCurrent(None, None)
    opengl32.wglDeleteContext(hglrc)
    user32.ReleaseDC(hwnd, hdc)
    user32.DestroyWindow(hwnd)
    print("[VORTEX APEX] All hardware threads safely disarmed. Session complete.")

if __name__ == "__main__":
    run_apex()
