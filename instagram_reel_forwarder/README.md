# Instagram Reel Auto-Forwarder 🚀

A fast, lightweight Python automation script to automatically forward Instagram Reels to a specified recipient (e.g., "Study Material") and advance to the next Reel using hotkeys.

## ⚡ Features
- **High-Speed Automation**: Forwards Reels in ~1 second.
- **Hotkeys**:
  - `F8`: Forward current Reel & move to next Reel.
  - `F9`: Skip to next Reel without forwarding.
  - `ESC`: Exit script cleanly.
- **DPI Aware & Smooth Controls**: Per-monitor DPI aware mouse capture and natural timing delays.
- **Recalibration Wizard**: Simple wizard to set or update screen button coordinates (`--recalibrate`).

## 📋 Requirements
- Python 3.8+
- `pyautogui`
- `pynput`

```bash
pip install pyautogui pynput
```

## 🚀 How to Use
1. Open Instagram Reels on your web browser or desktop app.
2. Run the script:
   ```bash
   python instagram_reel_forwarder.py
   ```
3. On first run, follow the terminal instructions to calibrate button positions (Share, Recipient, Send).
4. Switch to Instagram Reels and press `F8` to forward, or `F9` to skip!
5. Press `ESC` when finished.
