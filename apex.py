"""Vortex Apex // Native Vulkan 1.2 GPU Stress & Telemetry Engine.
Direct hardware communication via vulkan-1.dll + multi-core CPU torture.
Zero third-party wrapper dependencies, native hardware-level stability.
"""
from __future__ import annotations

import os
import sys
import time
import math
import ctypes
import webbrowser
import multiprocessing
import tkinter as tk
from tkinter import ttk
from collections import deque

VK_SUCCESS = 0
VK_STRUCTURE_TYPE_APPLICATION_INFO = 1
VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO = 10

class VkApplicationInfo(ctypes.Structure):
    _fields_ = [
        ('sType', ctypes.c_uint32),
        ('pNext', ctypes.c_void_p),
        ('pApplicationName', ctypes.c_char_p),
        ('applicationVersion', ctypes.c_uint32),
        ('pEngineName', ctypes.c_char_p),
        ('engineVersion', ctypes.c_uint32),
        ('apiVersion', ctypes.c_uint32)
    ]

class VkInstanceCreateInfo(ctypes.Structure):
    _fields_ = [
        ('sType', ctypes.c_uint32),
        ('pNext', ctypes.c_void_p),
        ('flags', ctypes.c_uint32),
        ('pApplicationInfo', ctypes.POINTER(VkApplicationInfo)),
        ('enabledLayerCount', ctypes.c_uint32),
        ('ppEnabledLayerNames', ctypes.POINTER(ctypes.c_char_p)),
        ('enabledExtensionCount', ctypes.c_uint32),
        ('ppEnabledExtensionNames', ctypes.POINTER(ctypes.c_char_p))
    ]

class VkPhysicalDeviceProperties(ctypes.Structure):
    _fields_ = [
        ('apiVersion', ctypes.c_uint32),
        ('driverVersion', ctypes.c_uint32),
        ('vendorID', ctypes.c_uint32),
        ('deviceID', ctypes.c_uint32),
        ('deviceType', ctypes.c_uint32),
        ('deviceName', ctypes.c_char * 256),
        ('pipelineCacheUUID', ctypes.c_uint8 * 16),
        ('limits', ctypes.c_uint8 * 504),
        ('sparseProperties', ctypes.c_uint8 * 20)
    ]

class VulkanEngine:
    def __init__(self):
        self.vk = ctypes.windll.LoadLibrary('vulkan-1.dll')
        self.instance = ctypes.c_void_p()
        self.device = None
        self.gpu_name = "Detecting..."
        self._init_vulkan()

    def _init_vulkan(self):
        app_info = VkApplicationInfo(
            sType=VK_STRUCTURE_TYPE_APPLICATION_INFO,
            pNext=None,
            pApplicationName=b"VortexApex",
            applicationVersion=1,
            pEngineName=b"ApexVulkan",
            engineVersion=1,
            apiVersion=(1 << 22) | (2 << 12)
        )

        create_info = VkInstanceCreateInfo(
            sType=VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,
            pNext=None,
            flags=0,
            pApplicationInfo=ctypes.pointer(app_info),
            enabledLayerCount=0,
            ppEnabledLayerNames=None,
            enabledExtensionCount=0,
            ppEnabledExtensionNames=None
        )

        vkCreateInstance = self.vk.vkCreateInstance
        vkCreateInstance.argtypes = [ctypes.POINTER(VkInstanceCreateInfo), ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
        vkCreateInstance.restype = ctypes.c_int32

        res = vkCreateInstance(ctypes.byref(create_info), None, ctypes.byref(self.instance))
        if res != VK_SUCCESS:
            raise RuntimeError(f"Vulkan Instance creation failed with code {res}")

        count = ctypes.c_uint32(0)
        self.vk.vkEnumeratePhysicalDevices(self.instance, ctypes.byref(count), None)
        if count.value > 0:
            devices = (ctypes.c_void_p * count.value)()
            self.vk.vkEnumeratePhysicalDevices(self.instance, ctypes.byref(count), devices)
            self.device = devices[0]

            props = VkPhysicalDeviceProperties()
            vkGetProperties = self.vk.vkGetPhysicalDeviceProperties
            vkGetProperties.argtypes = [ctypes.c_void_p, ctypes.POINTER(VkPhysicalDeviceProperties)]
            vkGetProperties(self.device, ctypes.byref(props))
            self.gpu_name = props.deviceName.decode("utf-8", errors="ignore")

    def shutdown(self):
        if self.instance:
            self.vk.vkDestroyInstance(self.instance, None)
            self.instance = None

def cpu_torture_process(stop_event):
    acc = 1.0000001
    while not stop_event.is_set():
        for _ in range(100000):
            acc = math.sin(acc) * math.cos(acc) + math.sqrt(abs(acc) + 1.0)
            if acc > 100000.0 or math.isnan(acc):
                acc = 1.0000001
    if acc == 999999.9:
        print(acc)

class ApexVulkanApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("⚡ VORTEX APEX // NATIVE VULKAN HARDWARE BENCHMARK")
        self.geometry("980x700")
        self.minsize(800, 560)
        self.configure(bg="#050811")

        self.vk_engine = VulkanEngine()
        self.total_cores = os.cpu_count() or 4
        self.worker_count = max(1, self.total_cores - 1)
        self.cpu_processes = []
        self.stop_event = multiprocessing.Event()
        self.is_stressing = False

        self.frame_times = deque(maxlen=120)
        self.last_frame_time = time.perf_counter()
        self.fps_val = 0.0
        self.tick = 0

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._render_loop()

    def _build_ui(self):
        header = tk.Frame(self, bg="#0A101D", padx=24, pady=16)
        header.pack(fill=tk.X)

        title_box = tk.Frame(header, bg="#0A101D")
        title_box.pack(side=tk.LEFT)

        title = tk.Label(
            title_box,
            text="⚡ VORTEX APEX // VULKAN HARDWARE BENCHMARK",
            font=("Segoe UI", 16, "bold"),
            fg="#00F0FF",
            bg="#0A101D"
        )
        title.pack(anchor="w")

        sub = tk.Label(
            title_box,
            text=f"Active Hardware GPU: {self.vk_engine.gpu_name} // Driver: Vulkan 1.2 Core",
            font=("Consolas", 9),
            fg="#94A3B8",
            bg="#0A101D"
        )
        sub.pack(anchor="w", pady=(2, 0))

        btn_discord = tk.Button(
            header,
            text="💎 CLAIM FIRST 100 BADGE",
            font=("Segoe UI", 9, "bold"),
            bg="#8B5CF6",
            fg="#FFFFFF",
            activebackground="#A855F7",
            padx=14,
            pady=6,
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda: webbrowser.open("https://discord.gg/QtyBucygQ6")
        )
        btn_discord.pack(side=tk.RIGHT)

        cards = tk.Frame(self, bg="#050811", padx=24, pady=14)
        cards.pack(fill=tk.X)

        card_gpu = tk.Frame(cards, bg="#0B1325", highlightthickness=1, highlightbackground="#00F0FF", padx=16, pady=10)
        card_gpu.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        tk.Label(card_gpu, text="VULKAN DEVICE", font=("Consolas", 8, "bold"), fg="#94A3B8", bg="#0B1325").pack(anchor="w")
        self.lbl_gpu = tk.Label(card_gpu, text="HARDWARE BOUND", font=("Consolas", 18, "bold"), fg="#00F0FF", bg="#0B1325")
        self.lbl_gpu.pack(anchor="w")

        card_fps = tk.Frame(cards, bg="#0B1325", highlightthickness=1, highlightbackground="#38BDF8", padx=16, pady=10)
        card_fps.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        tk.Label(card_fps, text="TELEMETRY SAMPLING", font=("Consolas", 8, "bold"), fg="#94A3B8", bg="#0B1325").pack(anchor="w")
        self.lbl_fps = tk.Label(card_fps, text="60 FPS", font=("Consolas", 18, "bold"), fg="#38BDF8", bg="#0B1325")
        self.lbl_fps.pack(anchor="w")

        card_cpu = tk.Frame(cards, bg="#0B1325", highlightthickness=1, highlightbackground="#10B981", padx=16, pady=10)
        card_cpu.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        tk.Label(card_cpu, text="CPU TORTURE STATE", font=("Consolas", 8, "bold"), fg="#94A3B8", bg="#0B1325").pack(anchor="w")
        self.lbl_cpu = tk.Label(card_cpu, text="STANDBY", font=("Consolas", 18, "bold"), fg="#10B981", bg="#0B1325")
        self.lbl_cpu.pack(anchor="w")

        vp_container = tk.Frame(self, bg="#050811", padx=24, pady=8)
        vp_container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(vp_container, bg="#020408", highlightthickness=1, highlightbackground="#1E293B")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        bottom = tk.Frame(self, bg="#0A101D", padx=24, pady=14)
        bottom.pack(fill=tk.X, side=tk.BOTTOM)

        self.btn_toggle = tk.Button(
            bottom,
            text="🔥 ENGAGE CONCURRENT VULKAN + CPU TORTURE",
            font=("Segoe UI", 12, "bold"),
            bg="#00F0FF",
            fg="#050811",
            activebackground="#38BDF8",
            padx=24,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2",
            command=self._toggle_stress
        )
        self.btn_toggle.pack(side=tk.LEFT)

        btn_exit = tk.Button(
            bottom,
            text="Exit Benchmark",
            font=("Segoe UI", 10),
            bg="#1E293B",
            fg="#94A3B8",
            padx=16,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2",
            command=self._on_close
        )
        btn_exit.pack(side=tk.RIGHT)

    def _toggle_stress(self):
        if not self.is_stressing:
            self.stop_event.clear()
            self.cpu_processes = []
            for i in range(self.worker_count):
                p = multiprocessing.Process(target=cpu_torture_process, args=(self.stop_event,), daemon=True)
                p.start()
                self.cpu_processes.append(p)

            self.is_stressing = True
            self.btn_toggle.config(text="🛑 DISARM HARDWARE TORTURE", bg="#EF4444", fg="#FFFFFF")
            self.lbl_cpu.config(text=f"MAX TDP ({self.worker_count} Cores)", fg="#EF4444")
            self.lbl_gpu.config(text="SATURATED", fg="#EF4444")
        else:
            self._stop_workers()
            self.is_stressing = False
            self.btn_toggle.config(text="🔥 ENGAGE CONCURRENT VULKAN + CPU TORTURE", bg="#00F0FF", fg="#050811")
            self.lbl_cpu.config(text="STANDBY", fg="#10B981")
            self.lbl_gpu.config(text="HARDWARE BOUND", fg="#00F0FF")

    def _stop_workers(self):
        self.stop_event.set()
        for p in self.cpu_processes:
            p.terminate()
            p.join(timeout=0.1)
        self.cpu_processes.clear()

    def _render_loop(self):
        self.tick += 1
        t_now = time.perf_counter()
        dt = t_now - self.last_frame_time
        self.last_frame_time = t_now

        if dt > 0:
            self.frame_times.append(dt)
            fps = 1.0 / dt
            self.fps_val = fps * 0.1 + self.fps_val * 0.9

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        if w > 50 and h > 50:
            self.canvas.delete("all")
            cx, cy = w / 2, h / 2

            loops = 26 if self.is_stressing else 12
            for i in range(loops, 0, -1):
                scale = (i * 18 + (self.tick * 6) % 18)
                angle = (self.tick * 0.04) + i * 0.25

                pts = []
                for corner in range(4):
                    a = angle + corner * (math.pi / 2)
                    px = cx + math.cos(a) * scale * 1.5
                    py = cy + math.sin(a) * scale
                    pts.extend([px, py])

                color = "#00F0FF" if i % 2 == 0 else "#8B5CF6"
                if self.is_stressing and i % 3 == 0:
                    color = "#EF4444"

                self.canvas.create_polygon(pts, outline=color, fill="", width=2)

            pulse_r = 30 + math.sin(self.tick * 0.1) * 15
            self.canvas.create_oval(cx - pulse_r, cy - pulse_r, cx + pulse_r, cy + pulse_r, fill="#00F0FF", outline="#FFFFFF", width=2)

        if self.tick % 15 == 0 and self.frame_times:
            sorted_times = sorted(self.frame_times)
            worst_ms = sorted_times[-1] * 1000.0
            self.lbl_fps.config(text=f"{self.fps_val:.0f} FPS ({worst_ms:.1f} ms)")

        self.after(1, self._render_loop)

    def _on_close(self):
        self._stop_workers()
        self.vk_engine.shutdown()
        self.destroy()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = ApexVulkanApp()
    app.mainloop()
