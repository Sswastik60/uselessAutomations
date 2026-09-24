# System Architecture & Threading Model

## Layered Architecture

```text
UI Layer (PySide6)
 ├── MainWindow / DashboardView / ModeEditorView / LogsPanelView
 │
Application Services Layer
 ├── ModeManager / HotkeyService / DeviceService / NotificationService
 │
Core Automation Engine
 ├── AutomationEngine / AutomationWorker (QThread)
 ├── ActionRegistry / EventBus / AutomationContext
 │
Actions & Adapters Layer
 ├── Process / Filesystem / Windows / Audio / MIDI / Keyboard / Mouse Actions
 └── FLStudioAdapter / SteamAdapter / SpotifyAdapter / DiscordAdapter
 │
Infrastructure Layer
 └── Windows APIs (Win32, Core Audio, psutil, RegisterHotKey, Registry)
```

## Threading & Responsiveness

To ensure the PySide6 UI thread remains 100% smooth and responsive during long-running automations:

1. **Automation Worker Thread (`AutomationWorker`)**:
   - Each Mode execution runs inside an isolated `QThread` instance.
   - Sleep / wait actions poll cancellation tokens (`context.is_cancelled()`) every 100ms.
   - UI updates are emitted safely across thread boundaries via Qt Signals (`action_started`, `action_completed`, `mode_progress`, `mode_completed`).

2. **Global Hotkey Thread (`HotkeyThread`)**:
   - Runs a native Windows message loop (`GetMessageW` / `DispatchMessageW`) in a dedicated QThread.
   - Listens for `WM_HOTKEY` events and dispatches triggered mode IDs to the main UI thread via Qt Signals.

3. **Event Bus (`EventBus`)**:
   - Pub/sub singleton allowing decoupled logging, database persistence, and UI status updates.
