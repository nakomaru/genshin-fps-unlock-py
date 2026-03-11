# Genshin FPS Unlocker (Python)

A lightweight, transparent Python script to unlock FPS in Genshin Impact. 

### Why Python?
DLL injection can be flagged as malware by Windows Defender and other antivirus software. This script uses a single memory edit done with `pymem` and a "race" strategy during process startup to gain access before the anti-cheat driver locks the process. It is written in readable Python so users can verify exactly what the code is doing.

**Credit:** Memory pattern from [34736384/genshin-fps-unlock](https://github.com/34736384/genshin-fps-unlock).

---

### Configuration (`fps_config.json`)

The script automatically generates this file in its directory on first run.

| Option | Description |
| :--- | :--- |
| `GamePath` | Absolute path to `GenshinImpact.exe`. |
| `FPSTarget` | The desired framerate. |
| `UsePowerSave` | If true, drops FPS to 10 when the game is out of focus. |
| `PopupWindow` | Enables "Borderless Windowed" mode. |
| `Fullscreen` | Sets the game to Fullscreen mode if true. |
| `UseCustomRes` | If true, applies `CustomResX` and `CustomResY` on launch. |
| `CustomResX/Y` | Width and Height for custom resolution. |
| `PopupPosX/Y` | The top-left corner coordinates for the window (used with `PopupWindow`). |
| `MonitorNum` | The index of the monitor to launch on. |
| `AdditionalCommandLine` | Extra Unity launch arguments. |
| `Logging` | If true, records events and edits to `fps_unlocker.log`. |

---

### Usage
1. Close the game completely.
2. Run the script directly using Python:
   ```bash
   python fps_unlocker.py
   ```
3. **Self-Bootstrapping**: The script will automatically:
   - Request **Administrator privileges** (required for memory access).
   - Create a local **virtual environment** (`.venv_fps_unlocker/`) if it doesn't exist.
   - Install required dependencies (`pymem`) silently.
   - Launch the game and run the unlocker service invisibly in the background.
4. The service exits automatically when the game is closed.

*Note: All files (logs, config, venv) are maintained relative to the script's directory, so it can be called from anywhere or via a shortcut.*
