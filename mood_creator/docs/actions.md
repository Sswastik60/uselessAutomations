# Actions Specification & Reference

Every action implements `BaseAction` and returns an `ActionResult(success, message, duration, data, error)`.

## Built-In Action Types

| Action Type | Category | Parameters | Description |
| :--- | :--- | :--- | :--- |
| `process.launch` | Process | `application`, `arguments`, `working_dir` | Launch application executable |
| `process.close` | Process | `process_name`, `force` | Terminate process |
| `process.restart` | Process | `process_name`, `application_path` | Restart process |
| `process.wait_for` | Process | `application`, `timeout` | Wait until process appears |
| `process.check` | Process | `process_name` | Check if process running |
| `file.open` | File | `file_path` | Open file with default handler |
| `file.create_dir` | File | `directory_path` | Create directory tree |
| `file.copy` | File | `source`, `destination` | Copy file |
| `file.move` | File | `source`, `destination` | Move file |
| `file.delete` | File | `file_path`, `confirm` | Delete file/folder |
| `file.exists` | File | `path` | Check if path exists |
| `window.focus` | Window | `title` | Focus matching window |
| `window.minimize` | Window | `title` | Minimize window |
| `window.maximize` | Window | `title` | Maximize window |
| `window.move` | Window | `title`, `x`, `y`, `width`, `height` | Move / resize window |
| `audio.detect_device` | Audio | `device` | Verify audio device connected |
| `audio.set_input` | Audio | `device` | Set default input device |
| `audio.set_output` | Audio | `device` | Set default output device |
| `midi.detect_device` | MIDI | `device` | Verify MIDI device connected |
| `keyboard.press_key` | Keyboard | `key` | Press single key |
| `keyboard.type_text` | Keyboard | `text`, `delay` | Type string of text |
| `keyboard.hotkey` | Keyboard | `hotkey` | Trigger key combination |
| `mouse.click` | Mouse | `x`, `y`, `button`, `clicks` | Click mouse button |
| `mouse.move` | Mouse | `x`, `y` | Move cursor |
| `mouse.scroll` | Mouse | `amount` | Scroll mouse wheel |
| `wait.duration` | Wait | `seconds` | Wait duration in seconds |
| `wait.for_window` | Wait | `title`, `timeout` | Wait for window title |
| `wait.for_file` | Wait | `file_path`, `timeout` | Wait for file path |
| `condition.device_exists` | Condition | `device`, `then_actions`, `else_actions` | IF device connected |
| `condition.process_running` | Condition | `process_name` | IF process running |
| `condition.file_exists` | Condition | `file_path` | IF file exists |
| `condition.env_exists` | Condition | `variable_name` | IF env var exists |
| `notification.show` | Notification | `title`, `message` | Show desktop notification |
