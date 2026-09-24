# ⚡ Windows 11 Automation Hub (Mood Creator) — Beta Version 1.0

[![Version](https://img.shields.io/badge/version-1.0--beta-blue.svg)](https://github.com/Sswastik60/uselessAutomations)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A production-quality **personal Windows 11 automation hub** inspired by the simplicity of Steam Deck shortcuts.

The core idea:

> **Press one button or hotkey system-wide, and your entire computer reconfigures into your desired "Mode".**

---

## 🌟 Key Features

* **Mode Automation Recipes**: Single-button / single-hotkey trigger for complex computer setups (🎸 Guitar Mode, 🎮 Gaming Mode, 💻 Coding Mode, 🎹 Music Production Mode, 📚 Study Mode).
* **Polished Windows 11 Dark Mode GUI**: Built natively with PySide6 (Qt 6), featuring rounded cards, status indicators, and live execution views.
* **Extensible Action System**: Built-in actions for process management, file operations, audio input/output device switching, window control, keyboard & mouse macro simulation, wait/polling timers, conditional branching, and desktop notifications.
* **Global System Hotkeys**: Non-blocking background Windows API hotkey monitoring (e.g., `CTRL+ALT+G`).
* **Application Adapters Plugin Architecture**: First-party adapters for **FL Studio**, **Steam**, **Spotify**, and **Discord**.
* **Background System Tray Integration**: Minimize to tray with quick-run mode submenus and toast notifications.
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
