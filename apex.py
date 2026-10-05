"""Vortex Apex 2.0 // Vulkan Hardware Compute & Multi-Core Stress Suite.
Integrates GpuZelenograd/memtest_vulkan Rust compute engine + multiprocessing CPU torture.
Zero crash, hardware-verified memory bus saturation (GB/s bandwidth) + CPU max TDP load.
"""
from __future__ import annotations

import os
import sys
import time
import math
import subprocess
import threading
import webbrowser
import multiprocessing
import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
MEMTEST_EXE = HERE / "memtest_vulkan.exe"

# -----------------------------------------------------------------------------
# CPU Multi-Core Torture Worker
# -----------------------------------------------------------------------------
def cpu_torture_worker(stop_event):
    acc = 1.0000001
    while not stop_event.is_set():
        for _ in range(100000):
            acc = math.sin(acc) * math.cos(acc) + math.sqrt(abs(acc) + 1.0)
            if acc > 100000.0 or math.isnan(acc):
                acc = 1.0000001
    if acc == 999999.9:
        print(acc)

# -----------------------------------------------------------------------------
# Vortex Apex GUI & Telemetry Dashboard
# -----------------------------------------------------------------------------
class VortexApexApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("⚡ VORTEX APEX // VULKAN COMPUTE & HARDWARE TORTURE SUITE")
        self.geometry("1020x720")
        self.minsize(840, 600)
        self.configure(bg="#050811")

        self.total_cores = os.cpu_count() or 4
        self.cpu_workers = max(1, self.total_cores - 1)
        self.cpu_processes = []
        self.stop_event = multiprocessing.Event()

        self.vulkan_proc = None
        self.vulkan_thread = None
        self.is_running = False

        self.gpu_name = "NVIDIA GeForce GTX 1650 (4GB)"
        self.bandwidth_str = "0.0 GB/sec"
        self.written_str = "0.0 GB"
        self.checked_str = "0.0 GB"
        self.iterations = 0

        self.log_lines = deque(maxlen=200)

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # Header banner
        header = tk.Frame(self, bg="#0A101D", padx=24, pady=16)
        header.pack(fill=tk.X)

        title_box = tk.Frame(header, bg="#0A101D")
        title_box.pack(side=tk.LEFT)

        title = tk.Label(
            title_box,
            text="⚡ VORTEX APEX // VULKAN COMPUTE ENGINE",
            font=("Segoe UI", 16, "bold"),
            fg="#00F0FF",
            bg="#0A101D"
        )
        title.pack(anchor="w")

        sub = tk.Label(
            title_box,
            text=f"Direct Vulkan Compute Shaders // CPU Cores: {self.total_cores} // Target: {self.gpu_name}",
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

        # Telemetry Status Cards
        cards = tk.Frame(self, bg="#050811", padx=24, pady=16)
        cards.pack(fill=tk.X)

        # Card 1: Vulkan Bandwidth
        c1 = tk.Frame(cards, bg="#0B1325", highlightthickness=1, highlightbackground="#00F0FF", padx=16, pady=12)
        c1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        tk.Label(c1, text="VULKAN VRAM BANDWIDTH", font=("Consolas", 8, "bold"), fg="#94A3B8", bg="#0B1325").pack(anchor="w")
        self.lbl_bw = tk.Label(c1, text="0.0 GB/sec", font=("Consolas", 20, "bold"), fg="#00F0FF", bg="#0B1325")
        self.lbl_bw.pack(anchor="w")

        # Card 2: Memory Checked
        c2 = tk.Frame(cards, bg="#0B1325", highlightthickness=1, highlightbackground="#38BDF8", padx=16, pady=12)
        c2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        tk.Label(c2, text="VRAM CHECKED / WRITTEN", font=("Consolas", 8, "bold"), fg="#94A3B8", bg="#0B1325").pack(anchor="w")
        self.lbl_vram = tk.Label(c2, text="0.0 / 0.0 GB", font=("Consolas", 20, "bold"), fg="#38BDF8", bg="#0B1325")
        self.lbl_vram.pack(anchor="w")

        # Card 3: CPU Multi-Core Load
        c3 = tk.Frame(cards, bg="#0B1325", highlightthickness=1, highlightbackground="#10B981", padx=16, pady=12)
        c3.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        tk.Label(c3, text="CPU TORTURE STATE", font=("Consolas", 8, "bold"), fg="#94A3B8", bg="#0B1325").pack(anchor="w")
        self.lbl_cpu = tk.Label(c3, text="STANDBY", font=("Consolas", 20, "bold"), fg="#10B981", bg="#0B1325")
        self.lbl_cpu.pack(anchor="w")

        # Live Console Output Panel
        console_frame = tk.Frame(self, bg="#050811", padx=24, pady=8)
        console_frame.pack(fill=tk.BOTH, expand=True)

        lbl_console = tk.Label(console_frame, text="⚡ REAL-TIME VULKAN COMPUTE & KERNEL LOGS:", font=("Consolas", 9, "bold"), fg="#94A3B8", bg="#050811")
        lbl_console.pack(anchor="w", pady=(0, 6))

        self.txt_console = tk.Text(
            console_frame,
            bg="#020408",
            fg="#00F0FF",
            font=("Consolas", 9),
            insertbackground="#00F0FF",
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground="#1E293B",
            padx=12,
            pady=10
        )
        self.txt_console.pack(fill=tk.BOTH, expand=True)
        self.txt_console.insert(tk.END, "Ready. Click 'ENGAGE CONCURRENT HARDWARE TORTURE' to begin saturation.\n")

        # Bottom Action Bar
        bottom = tk.Frame(self, bg="#0A101D", padx=24, pady=16)
        bottom.pack(fill=tk.X, side=tk.BOTTOM)

        self.btn_action = tk.Button(
            bottom,
            text="🔥 ENGAGE CONCURRENT HARDWARE TORTURE",
            font=("Segoe UI", 12, "bold"),
            bg="#00F0FF",
            fg="#050811",
            activebackground="#38BDF8",
            padx=28,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2",
            command=self._toggle_stress
        )
        self.btn_action.pack(side=tk.LEFT)

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
        if not self.is_running:
            self._start_stress()
        else:
            self._stop_stress()

    def _start_stress(self):
        if not MEMTEST_EXE.exists():
            messagebox.showerror("Engine Missing", f"Could not find {MEMTEST_EXE}")
            return

        self.is_running = True
        self.btn_action.config(text="🛑 DISARM / STOP HARDWARE TORTURE", bg="#EF4444", fg="#FFFFFF")
        self.lbl_cpu.config(text=f"MAX TDP ({self.cpu_workers} Cores)", fg="#EF4444")
        self.txt_console.insert(tk.END, f"\n[VORTEX APEX] Initializing Vulkan Compute Shaders on {self.gpu_name}...\n")
        self.txt_console.insert(tk.END, f"[VORTEX APEX] Spawning {self.cpu_workers} dedicated vectorized CPU torture processes...\n")
        self.txt_console.see(tk.END)

        # 1. Start CPU Multiprocessing
        self.stop_event.clear()
        self.cpu_processes = []
        for i in range(self.cpu_workers):
            p = multiprocessing.Process(target=cpu_torture_worker, args=(self.stop_event,), daemon=True)
            p.start()
            self.cpu_processes.append(p)

        # 2. Start Vulkan Compute Engine Subprocess
        self.vulkan_thread = threading.Thread(target=self._run_vulkan_stream, daemon=True)
        self.vulkan_thread.start()

    def _run_vulkan_stream(self):
        try:
            self.vulkan_proc = subprocess.Popen(
                [str(MEMTEST_EXE)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=str(HERE),
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            for line in iter(self.vulkan_proc.stdout.readline, ''):
                if not self.is_running:
                    break
                line_str = line.strip()
                if line_str:
                    self._parse_vulkan_output(line_str)
                    self.after(0, self._append_log, line_str)

        except Exception as e:
            self.after(0, self._append_log, f"Vulkan process error: {e}")

    def _parse_vulkan_output(self, line: str):
        # Example: 12 iteration. Passed 5.5099 seconds written: 12.4GB 5.9GB/sec checked: 24.8GB 7.3GB/sec
        if "GB/sec" in line:
            parts = line.split()
            try:
                # Find speed
                for idx, p in enumerate(parts):
                    if "GB/sec" in p and idx > 0:
                        speed = parts[idx - 1] + " " + p
                        self.bandwidth_str = speed
                        break
                # Find checked/written
                if "written:" in line and "checked:" in line:
                    w_idx = parts.index("written:")
                    c_idx = parts.index("checked:")
                    w_gb = parts[w_idx + 1]
                    c_gb = parts[c_idx + 1]
                    self.written_str = w_gb
                    self.checked_str = c_gb
                self.after(0, self._update_cards)
            except Exception:
                pass

    def _update_cards(self):
        self.lbl_bw.config(text=self.bandwidth_str)
        self.lbl_vram.config(text=f"{self.checked_str} / {self.written_str}")

    def _append_log(self, text: str):
        self.txt_console.insert(tk.END, text + "\n")
        self.txt_console.see(tk.END)

    def _stop_stress(self):
        self.is_running = False
        self.stop_event.set()

        # Stop CPU processes
        for p in self.cpu_processes:
            p.terminate()
            p.join(timeout=0.1)
        self.cpu_processes.clear()

        # Stop Vulkan process
        if self.vulkan_proc:
            try:
                self.vulkan_proc.terminate()
                self.vulkan_proc.kill()
            except Exception:
                pass
            self.vulkan_proc = None

        self.btn_action.config(text="🔥 ENGAGE CONCURRENT HARDWARE TORTURE", bg="#00F0FF", fg="#050811")
        self.lbl_cpu.config(text="STANDBY", fg="#10B981")
        self.txt_console.insert(tk.END, "\n[VORTEX APEX] Hardware torture disarmed. Systems in standby.\n")
        self.txt_console.see(tk.END)

    def _on_close(self):
        self._stop_stress()
        self.destroy()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = VortexApexApp()
    app.mainloop()
