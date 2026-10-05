# ⚡ Vortex Apex // Hardware Torture Architecture

> **Concurrent CPU & GPU Maximum Thermal & Power Saturation Engine with Zero External Dependencies!**

Implements the low-level concurrent hardware stress testing blueprint using native Win32 `kernel32`/`user32`/`gdi32` bindings and direct `opengl32.dll` hardware context creation.

---

## 🌟 Architecture Blueprint Implementation

### 1. CPU Architecture (Thread Pool)
- **Hardware Topology**: Automatically detects logical core count (SMT/Hyper-Threading).
- **Background Spawning**: Spawns $N - 1$ dedicated execution threads, cleanly reserving 1 logical core to feed the GPU pipeline without bottlenecks.
- **Lockless Vectorized Loops**: High-intensity polynomial trigonometry routines that force SIMD/AVX units into continuous maximum TDP power draw.
- **Optimization Evasion**: Volatile sink references preventing compiler dead-code elimination.

### 2. GPU Graphics Pipeline (Uncapped Saturation)
- **Direct WGL Hardware Context**: Bypasses heavy wrapper overhead.
- **V-Sync Override**: Disables vertical sync via `wglSwapIntervalEXT(0)` for uncapped, maximum physical frame rates.
- **ALU Screen-Space Overdraw**: Draws continuous multi-pass full-screen quads with dynamic time uniforms to stress rasterizers and shader ALUs.

### 3. Unified Safe Teardown
- Global thread-safe atomic signal joining all background threads cleanly the moment the user closes the window or presses **ESC**.

---

## 🚀 Quick Start
```bash
# Double-click launcher:
START_APEX.bat

# Or run directly via terminal:
python apex.py
```

---

## 💬 Community
Join the Vortex Discord server:
👉 **[discord.gg/QtyBucygQ6](https://discord.gg/QtyBucygQ6)**
