"""
Instagram Reel Auto-Forwarder to "Study Material" (High Speed & Continuous)
===========================================================================
Hotkeys:
  F8  -> Forward current Reel to "Study Material" & move to next
  F9  -> Move to next Reel (Skip)
  ESC -> Quit script

Requirements:
    pip install pyautogui pynput

Usage:
  1. Open Instagram (web browser or desktop app) to Reels.
  2. Run script:  python instagram_reel_forwarder.py
     (Use 'python instagram_reel_forwarder.py --recalibrate' to reset coordinates)
  3. Press F8 to forward & next, or F9 to just skip to next Reel.
  4. Press ESC to stop the script.
"""

import sys
import time
import json
import random
import argparse
import threading
from pathlib import Path

# Enable DPI Awareness on Windows for accurate screen mouse coordinates
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
    except Exception:
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

try:
    import pyautogui
    from pynput import keyboard
except ImportError:
    print("[X] Missing required packages! Please install with:")
    print("    pip install pyautogui pynput")
    sys.exit(1)

# -------------------------------------------------
# CONFIG & DELAYS (OPTIMIZED FOR HIGH SPEED)
# -------------------------------------------------
CONFIG_FILE = Path(__file__).parent / "instagram_coords.json"

# Speed optimized delays (seconds)
DELAY_AFTER_SHARE_CLICK = 0.4    # Wait for share modal to pop up
DELAY_AFTER_SELECT      = 0.15   # Wait after selecting "Study Material"
DELAY_AFTER_SEND        = 0.35   # Wait after clicking Send
DELAY_BEFORE_NEXT       = 0.2    # Wait before pressing next Reel key

# Next Reel Method: "key" (recommended) or "click"
NEXT_REEL_METHOD = "key"          # "key" uses 'down' or 'j'
NEXT_REEL_KEY    = "down"         # Down arrow for next Reel

# PyAutoGUI Performance Settings
pyautogui.FAILSAFE = False        # Disabled so mouse resting at corner doesn't trigger crash (use ESC to quit)
pyautogui.PAUSE = 0.01            # Minimal pause between pyautogui actions

# Thread Control Flags
is_busy = False
busy_lock = threading.Lock()
suppress_esc = False              # Prevents synthetic Escape keys from stopping listener


def log(msg: str):
    """Print with instant stdout flush."""
    print(msg, flush=True)


def human_delay(min_s=0.02, max_s=0.05):
    """Add a micro delay to ensure UI registers input fast."""
    time.sleep(random.uniform(min_s, max_s))


def get_mouse_pos(prompt: str) -> tuple[int, int]:
    """Prompt user to position mouse and press Enter in terminal."""
    log("")
    log(f"-> {prompt}")
    log("  Move mouse cursor over the target, then press ENTER in this terminal...")
    input()
    x, y = pyautogui.position()
    log(f"  [+] Saved coordinates: ({x}, {y})")
    return int(x), int(y)


def load_or_calibrate(force_recalibrate: bool = False) -> dict:
    """Load coordinates from JSON file or run calibration wizard."""
    required_keys = ["share_button", "study_material", "send_button"]
    if NEXT_REEL_METHOD == "click":
        required_keys.append("next_reel")

    if not force_recalibrate and CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                coords = json.load(f)
            if isinstance(coords, dict) and all(k in coords for k in required_keys):
                log(f"[+] Loaded saved coordinates from: {CONFIG_FILE.name}")
                log("   (Run with --recalibrate if button positions changed)")
                log("")
                return coords
            else:
                log("[!] Saved configuration is invalid or missing keys. Starting recalibration...")
        except Exception as e:
            log(f"[!] Failed to read {CONFIG_FILE.name}: {e}. Starting recalibration...")

    log("")
    log("=" * 60)
    log("  FIRST-TIME / RE-CALIBRATION WIZARD")
    log("=" * 60)
    log("1. Open Instagram on your screen and open any Reel.")
    log("2. Ensure the Instagram window stays in the exact same position.")
    log("")

    coords = {}
    coords["share_button"] = get_mouse_pos(
        "Point to the SHARE (paper plane) button on the Reel"
    )
    coords["study_material"] = get_mouse_pos(
        "Open the Share dialog manually once, then point to 'Study Material' recipient"
    )
    coords["send_button"] = get_mouse_pos(
        "Point to the blue SEND button inside the Share dialog"
    )

    if NEXT_REEL_METHOD == "click":
        coords["next_reel"] = get_mouse_pos(
            "Point to the DOWN arrow button (Next Reel) on screen"
        )

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(coords, f, indent=2)
        log("")
        log(f"[+] Coordinates successfully saved to: {CONFIG_FILE.name}")
    except Exception as e:
        log(f"[!] Could not save configuration file: {e}")

    return coords


def click_pos(pos: tuple[int, int], clicks=1):
    """Move rapidly to position and click."""
    x, y = pos
    pyautogui.moveTo(x, y, duration=random.uniform(0.04, 0.08))
    human_delay(0.02, 0.05)
    pyautogui.click(clicks=clicks)


def move_to_next_reel(coords: dict):
    """Move to the next Reel (triggered by F9 or after forward)."""
    if NEXT_REEL_METHOD == "key":
        pyautogui.press(NEXT_REEL_KEY)
    else:
        click_pos(coords["next_reel"])


def next_reel_standalone(coords: dict):
    """Handler for F9 hotkey (Skip to next Reel)."""
    global is_busy

    with busy_lock:
        if is_busy:
            return
        is_busy = True

    try:
        log("")
        log("[>] [F9 Pressed] Moving to next Reel...")
        move_to_next_reel(coords)
        log("  [+] Next Reel!")
    except Exception as e:
        log(f"  [X] Error during next reel: {e}")
    finally:
        with busy_lock:
            is_busy = False


def forward_current_reel(coords: dict):
    """Execute the auto-forward routine for the currently active Reel (F8)."""
    global is_busy

    with busy_lock:
        if is_busy:
            log("[!] Action in progress... please wait.")
            return
        is_busy = True

    try:
        log("")
        log("[>] [F8 Pressed] Forwarding Reel to Study Material...")

        # 1. Open Share dialog
        log("  1/4 Opening Share dialog...")
        click_pos(coords["share_button"])
        time.sleep(DELAY_AFTER_SHARE_CLICK)

        # 2. Select Study Material
        log("  2/4 Selecting 'Study Material'...")
        click_pos(coords["study_material"])
        time.sleep(DELAY_AFTER_SELECT)

        # 3. Click Send
        log("  3/4 Clicking Send...")
        click_pos(coords["send_button"])
        time.sleep(DELAY_AFTER_SEND)

        # 4. Next Reel
        log("  4/4 Moving to next Reel...")
        time.sleep(DELAY_BEFORE_NEXT)
        move_to_next_reel(coords)

        log("  [+] Done in ~1s! Ready for next Reel (F8 = Forward, F9 = Skip, ESC = Exit).")

    except Exception as e:
        log(f"  [X] Error during execution: {e}")
    finally:
        with busy_lock:
            is_busy = False


def main():
    global suppress_esc
    parser = argparse.ArgumentParser(description="Instagram Reel Auto-Forwarder (High Speed)")
    parser.add_argument(
        "-r", "--recalibrate",
        action="store_true",
        help="Force recalibration of screen coordinates"
    )
    args = parser.parse_args()

    log("=" * 60)
    log("  Instagram Reel Auto-Forwarder [HIGH SPEED MODE]")
    log("=" * 60)
    log("  Hotkeys:")
    log("    F8  : Forward Reel to Study Material & Next")
    log("    F9  : Skip to Next Reel without forwarding")
    log("    ESC : Quit script")
    log("=" * 60)
    log("")

    coords = load_or_calibrate(force_recalibrate=args.recalibrate)

    log("")
    log("[*] High-Speed Listener active!")
    log("[*] Switch to Instagram Reels in your browser.")
    log("[*] Press F8 to forward & next, F9 to skip, ESC to quit.")
    log("")

    def on_press(key):
        global suppress_esc
        try:
            if key == keyboard.Key.f8:
                t = threading.Thread(target=forward_current_reel, args=(coords,), daemon=True)
                t.start()
            elif key == keyboard.Key.f9:
                t = threading.Thread(target=next_reel_standalone, args=(coords,), daemon=True)
                t.start()
            elif key == keyboard.Key.esc:
                if suppress_esc:
                    return
                log("")
                log("[*] ESC pressed - Stopping listener. Exiting...")
                return False  # Stops listener
        except Exception as e:
            log(f"Listener exception: {e}")

    try:
        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()
    except KeyboardInterrupt:
        log("")
        log("[*] Interrupted by user (Ctrl+C). Exiting cleanly.")


if __name__ == "__main__":
    main()
