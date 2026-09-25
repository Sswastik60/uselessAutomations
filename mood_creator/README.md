# ⚡ Windows 11 Automation Hub (Mood Creator) — Version 2.0

[![Version](https://img.shields.io/badge/version-2.0.0-blueviolet.svg)](https://github.com/Sswastik60/uselessAutomations)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%2011-0078d4.svg)](https://microsoft.com/windows)

A world-class, premium **personal Windows 11 automation hub and mode controller** inspired by the speed, polish, and minimalism of Linear, Raycast, and Steam Deck.

The core idea:

> **Press one button or global hotkey system-wide, and your entire workstation transforms into your desired "Mode" instantly with non-blocking feedback.**

---

## 🌟 What's New in Version 2.0

* **Robust Multi-Strategy Window Control**: Auto-polling window resolver that monitors for newly launched application handles across Windows desktop stations, matching both window titles and executable process names (e.g. `vlc`, `brave`, `chrome`, `notepad`).
* **Hardware Scan Code Keyboard Simulation**: Function keys (like `F11` for full screen), navigation keys, and Windows Key (`WIN`/`SUPER`) combinations simulated with genuine hardware scan codes (`MapVirtualKey`) and window pre-focusing.
* **Interactive Window Picker**: Action Editor now includes a **"🪟 Select Window..."** helper that enumerates active desktop windows in real-time.
* **Dedicated Browser & Fullscreen Actions**: First-class `browser.open_url` and `window.fullscreen` actions for one-click browser automations and fullscreen toggling.
* **AMOLED True-Black Theme**: Designed with an ultra-sleek `#000000` / `#040405` / `#09090b` palette, subtle 1px border glows, fluid hover physics, and zero-distraction focus.
* **Non-Blocking HUD Overlay & Toasts**: Ambient floating HUD overlay and sleek corner toast notifications displayed above the taskbar even when minimized to the system tray.
* **Self-Healing Windows Shortcuts**: Intelligent shortcut resolver automatically detects version changes in auto-updating apps (e.g., Discord `app-1.0.xxxx`), resolves broken targets, and dynamically heals `.lnk` files on the fly.
* **Multi-Directory App Picker**: Effortlessly browse and attach executables from `DEDICATED_MODES`, system directories, Start Menu, or custom paths with instant file validation.
* **Command Palette (`Ctrl+K` / `⌘K`)**: Instant fuzzy search across all modes, action controls, and application settings.
* **Graceful Single-Instance IPC**: Clean application termination on window close with local socket communication to prevent orphaned background processes.
* **Pre-Packaged Standalone Executable**: Native single-file `AutomationHub.exe` built with PyInstaller, custom high-DPI icon assets, and zero external runtime dependencies.

---

## 🚀 Key Features

* **Mode Automation Recipes**: Single-button / single-hotkey trigger for complex computer setups (🎸 Guitar Mode, 🎮 Gaming Mode, 💻 Coding Mode, 🎹 Music Production Mode, 📚 Study Mode).
* **Polished PySide6 GUI**: High-performance Qt 6 desktop application with smooth easing curves, micro-interactions, and collapsible sidebar.
* **Extensible Action System**: Built-in actions for process management, file operations, audio input/output device switching, window control, keyboard & mouse macro simulation, wait/polling timers, conditional branching, and desktop notifications.
* **Global System Hotkeys**: Non-blocking background Windows API hotkey monitoring (e.g., `CTRL+ALT+G`).
* **Application Adapters Plugin Architecture**: First-party adapters for **FL Studio**, **Steam**, **Spotify**, and **Discord**.
* **System Tray & Toast Integration**: Background tray support with quick-run context menus and native status toasts.
* **JSON Mode Definitions & Schema Versioning**: User-editable, exportable, and importable JSON mode files with pydantic schema validation.
* **Persistent Activity Logs**: Built-in SQLite database logging every action duration, status, message, and diagnostic error trace.
* **Windows Autostart Integration**: Built-in Windows Registry autostart toggle (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`).

---

## 📁 Architecture Overview

```text
automation_hub/
│
├── app/
│   ├── main.py                  # Application entry point & QApplication lifecycle
│   ├── core/                    # Automation Engine, ActionRegistry, EventBus, ModeManager
│   ├── models/                  # Pydantic domain models (Mode, ActionConfig, ActionResult, AppSettings)
│   ├── actions/                 # Extensible Actions (Process, File, Window, Audio, MIDI, Keyboard, Mouse, Wait, Condition, Notification)
│   ├── integrations/            # Application Adapters (FLStudioAdapter, SteamAdapter, SpotifyAdapter, DiscordAdapter)
│   ├── windows/                 # Windows OS APIs (processes, windows, hotkeys, audio, devices)
│   ├── persistence/             # JSON Mode Store, Settings Store, SQLite Logger
│   ├── services/                # HotkeyService, DeviceService, NotificationService, StartupService
│   └── ui/                      # PySide6 Views (Dashboard, Mode Editor, Action Editor, Device Panel, Logs, Settings)
├── modes/                       # First-party JSON mode definitions (guitar, gaming, coding, study)
├── tests/                       # Pytest automated test suite
├── pyproject.toml               # Build configuration
├── run.py                       # Root application launcher
└── README.md
```

---

## 🚀 Quick Start Guide

### Prerequisites

* Windows 11 64-bit
* Python 3.12+

### Installation & Setup

1. **Clone or navigate to repository**:
   ```powershell
   cd c:\Users\91700\Desktop\PROJECT\uselessAutomations\mood_creator
   ```

2. **Create virtual environment and install dependencies**:
   ```powershell
   python -m venv .venv
   .venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

3. **Run the Application**:
   ```powershell
   .venv\Scripts\python.exe run.py
   ```

4. **Run Unit Tests**:
   ```powershell
   .venv\Scripts\pytest.exe
   ```

---

## 🎸 Example Mode Specification (`modes/guitar.json`)

```json
{
    "schema_version": 1,
    "id": "guitar_mode",
    "name": "Guitar Mode",
    "description": "Detect audio interface, configure input/output, and launch FL Studio for practice.",
    "icon": "🎸",
    "hotkey": "CTRL+ALT+G",
    "enabled": true,
    "actions": [
        {
            "type": "audio.detect_device",
            "name": "Detect Audio Interface",
            "params": { "device": "Scarlett 2i2" }
        },
        {
            "type": "audio.set_input",
            "name": "Set Audio Input",
            "params": { "device": "Scarlett 2i2" }
        },
        {
            "type": "audio.set_output",
            "name": "Set Audio Output",
            "params": { "device": "Headphones" }
        },
        {
            "type": "process.launch",
            "name": "Launch FL Studio",
            "params": { "application": "FL Studio" }
        },
        {
            "type": "process.wait_for",
            "name": "Wait for FL Studio",
            "params": { "application": "FL Studio", "timeout": 15 }
        },
        {
            "type": "notification.show",
            "name": "Notify Ready",
            "params": {
                "title": "🎸 Guitar Mode Ready",
                "message": "Audio interface configured & FL Studio ready!"
            }
        }
    ]
}
```

---

## 🛠 Adding Custom Actions

Creating a new action type requires subclassing `BaseAction` and registering it with `action_registry`:

```python
from app.actions.base import BaseAction
from app.core.action_registry import action_registry
from app.models.action_result import ActionResult

class CustomAction(BaseAction):
    PARAM_SCHEMA = {
        "setting": {"type": "string", "label": "Setting Value", "required": True}
    }

    def execute(self, context) -> ActionResult:
        setting = self.params.get("setting")
        # Perform automation...
        return ActionResult(success=True, message=f"Applied {setting}")

action_registry.register("custom.setting", CustomAction, category="Custom", display_name="Apply Setting")
```

---

## 📦 Packaging for Production

To compile into a standalone `AutomationHub.exe` single executable without requiring a local Python installation:

```powershell
.venv\Scripts\pyinstaller.exe --noconsole --onefile --name "AutomationHub" run.py
```

The resulting binary will be output in `dist/AutomationHub.exe`.

---

## 📄 Documentation

For deep technical details, see the `docs/` directory:
* [`docs/architecture.md`](file:///c:/Users/91700/Desktop/PROJECT/uselessAutomations/mood_creator/docs/architecture.md) — System design & threading architecture
* [`docs/actions.md`](file:///c:/Users/91700/Desktop/PROJECT/uselessAutomations/mood_creator/docs/actions.md) — Complete Action reference guide
* [`docs/modes.md`](file:///c:/Users/91700/Desktop/PROJECT/uselessAutomations/mood_creator/docs/modes.md) — Mode JSON schema specification
* [`docs/windows.md`](file:///c:/Users/91700/Desktop/PROJECT/uselessAutomations/mood_creator/docs/windows.md) — Windows OS APIs integration details
* [`docs/integrations.md`](file:///c:/Users/91700/Desktop/PROJECT/uselessAutomations/mood_creator/docs/integrations.md) — Application Adapters plugin guide
