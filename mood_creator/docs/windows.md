# Windows OS Integration & API Guide

## Windows APIs Used

1. **Win32 User32 (`ctypes.windll.user32`, `pywin32`)**:
   - `RegisterHotKey` / `UnregisterHotKey` for system-wide non-blocking global hotkeys.
   - `EnumWindows`, `SetForegroundWindow`, `ShowWindow`, `MoveWindow`, `GetWindowText` for window manipulation.
   - `AttachThreadInput` to bypass Windows `SetForegroundWindow` focus stealing restrictions.

2. **Windows Process Management (`psutil`, `subprocess`)**:
   - Process enumeration, active state checking, graceful termination (`proc.terminate()`), and force termination (`proc.kill()`).
   - Executable path auto-discovery across standard locations (`Program Files`, `Program Files (x86)`, `LOCALAPPDATA`, `APPDATA`).

3. **Windows Audio & Multimedia API (`comtypes`, `winmm`, WMI/PowerShell)**:
   - Audio endpoint enumeration (input capture and output playback devices).
   - MIDI controller enumeration via `winmm.midiInGetDevCapsW` and `winmm.midiOutGetDevCapsW`.

4. **Windows Autostart Registry (`winreg`)**:
   - Registry path: `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`.
   - Entry name: `AutomationHub`.
