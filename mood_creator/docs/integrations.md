# Application Adapters Integration Guide

Application Adapters provide specialized plugin adapters for desktop applications.

## First-Party Adapters

### 1. `FLStudioAdapter` (`fl_studio`)
- Auto-discovers FL Studio installation path (`FL64.exe`).
- `open_project(project_path)`: Launches FL Studio opening specified `.flp` project or template file.
- `wait_until_ready(timeout)`: Waits for process and window handle to appear.
- `focus()`: Brings FL Studio main window to front.

### 2. `SteamAdapter` (`steam`)
- Auto-discovers `steam.exe`.
- `launch_game(game_app_id)`: Launches Steam game using URI protocol (`steam://run/<app_id>`).

### 3. `SpotifyAdapter` (`spotify`)
- Auto-discovers `Spotify.exe`.
- Controls application lifecycle and window focus.

### 4. `DiscordAdapter` (`discord`)
- Auto-discovers `Discord.exe` or update wrapper.
- Controls application lifecycle and window focus.

## Creating a New Application Adapter

Subclass `ApplicationAdapter`:

```python
from app.integrations.base import ApplicationAdapter
from app.models.action_result import ActionResult

class CustomAppAdapter(ApplicationAdapter):
    @property
    def app_key(self) -> str:
        return "custom_app"

    @property
    def display_name(self) -> str:
        return "Custom Application"

    def is_installed(self) -> bool:
        ...

    def is_running(self) -> bool:
        ...

    def launch(self, extra_args=None) -> ActionResult:
        ...

    def focus(self) -> ActionResult:
        ...

    def close(self, force=False) -> ActionResult:
        ...
```
