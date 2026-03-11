import sys
import os
import subprocess
import ctypes
import struct
import time
import json
import traceback
from pathlib import Path

def ensure_bootstrap():
    """Ensures the script is running with Admin privileges and within a virtual environment."""
    # 1. Admin Elevation (Windows only)
    if os.name == 'nt':
        try:
            if not ctypes.windll.shell32.IsUserAnAdmin():
                # Relaunch with admin privileges
                # Use sys.executable to maintain the current interpreter (global or venv)
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{Path(__file__).resolve()}"', None, 1)
                sys.exit(0)
        except Exception as e:
            print(f"Failed to elevate: {e}")
            sys.exit(1)

    # 2. Virtual Environment Check
    if sys.prefix != sys.base_prefix:
        return

    script_dir = Path(__file__).parent.resolve()
    venv_dir = script_dir / ".venv_fps_unlocker"
    venv_python = venv_dir / "Scripts" / "python.exe" if os.name == "nt" else venv_dir / "bin" / "python"

    # Create venv if it doesn't exist
    if not venv_python.exists():
        import venv
        print("Creating virtual environment...")
        venv.create(venv_dir, with_pip=True)

    # Ensure dependencies are installed
    try:
        subprocess.check_call([str(venv_python), "-c", "import pymem"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("Installing dependencies (pymem)...")
        subprocess.check_call([str(venv_python), "-m", "pip", "install", "pymem"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 3. Relaunch within the virtual environment
    try:
        os.execv(str(venv_python), [str(venv_python), str(Path(__file__).resolve())] + sys.argv[1:])
    except AttributeError:
        # Fallback for platforms without execv
        sys.exit(subprocess.call([str(venv_python), str(Path(__file__).resolve())] + sys.argv[1:]))

if __name__ == "__main__":
    ensure_bootstrap()

# Non-standard imports (must come after bootstrap)
import pymem
import pymem.process

# Windows API constants
SW_HIDE = 0
HWND_TOP = 0
SWP_NOSIZE = 0x0001
SWP_NOZORDER = 0x0004
SWP_SHOWWINDOW = 0x0040
MONITOR_DEFAULTTONEAREST = 2

class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_ulong), ("rcMonitor", RECT), ("rcWork", RECT), ("dwFlags", ctypes.c_ulong)]

DEFAULT_CONFIG = {
    "GamePath": "C:\\Program Files\\HoYoPlay\\games\\Genshin Impact game\\GenshinImpact.exe",
    "PopupWindow": True,
    "Fullscreen": False,
    "UseCustomRes": True,
    "UsePowerSave": True,
    "FPSTarget": 120,
    "CustomResX": 1920,
    "CustomResY": 1042,
    "PopupPosX": 0,
    "PopupPosY": 0,
    "MonitorNum": 1,
    "AdditionalCommandLine": "",
    "Logging": True
}

script_dir = Path(__file__).parent.resolve()
log_file = None

def setup_logging(config):
    global log_file
    if config.get("Logging", True):
        log_file_path = script_dir / "fps_unlocker.log"
        log_file = open(log_file_path, "w", buffering=1)
        sys.stdout = log_file
        sys.stderr = log_file

def log(message):
    if log_file:
        timestamp = time.strftime('%H:%M:%S')
        print(f"[{timestamp}] {message}")

def load_config():
    config_path = script_dir / "fps_config.json"
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except:
            return DEFAULT_CONFIG
    else:
        try:
            with open(config_path, "w") as f:
                json.dump(DEFAULT_CONFIG, f, indent=2)
        except: pass
    return DEFAULT_CONFIG

def get_foreground_window():
    return ctypes.windll.user32.GetForegroundWindow()

def get_window_thread_process_id(hwnd):
    pid = ctypes.c_ulong()
    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value

# Windows API types
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

def snap_window_to_monitor_top_left(pid, config):
    """Finds the game window and moves it to the specified position on its monitor."""
    if config["Fullscreen"] or not config["PopupWindow"]:
        return

    snapped = [False]
    def enum_handler(hwnd, lParam):
        if ctypes.windll.user32.IsWindowVisible(hwnd):
            window_pid = ctypes.c_ulong()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
            if window_pid.value == pid:
                hMonitor = ctypes.windll.user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
                mi = MONITORINFO()
                mi.cbSize = ctypes.sizeof(MONITORINFO)
                if ctypes.windll.user32.GetMonitorInfoW(hMonitor, ctypes.byref(mi)):
                    x = mi.rcMonitor.left + config.get("PopupPosX", 0)
                    y = mi.rcMonitor.top + config.get("PopupPosY", 0)
                    ctypes.windll.user32.SetWindowPos(hwnd, HWND_TOP, x, y, 0, 0, SWP_NOSIZE | SWP_NOZORDER | SWP_SHOWWINDOW)
                    log(f"Snapped window to: ({x}, {y})")
                    snapped[0] = True
                return False
        return True

    proc_handler = WNDENUMPROC(enum_handler)
    for _ in range(60):
        ctypes.windll.user32.EnumWindows(proc_handler, 0)
        if snapped[0]: break
        time.sleep(0.5)

def find_process():
    for name in ["GenshinImpact.exe", "YuanShen.exe"]:
        try:
            output = subprocess.check_output(["tasklist", "/FI", f"IMAGENAME eq {name}"], stderr=subprocess.STDOUT, text=True)
            if name.lower() in output.lower():
                for line in output.splitlines():
                    if name.lower() in line.lower():
                        parts = line.split()
                        return int(parts[1]), name
        except: pass
    return None, None

def unlock_fps():
    config = load_config()
    setup_logging(config)
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), SW_HIDE)
    
    pm = None
    module_base = None
    log("--- STARTING BACKGROUND SERVICE ---")

    game_path = config["GamePath"]
    if not os.path.exists(game_path):
        log(f"Error: Game not found at {game_path}")
        return

    # Unity Command Line Arguments
    cmd = [
        game_path, 
        "-screen-fullscreen", "1" if config["Fullscreen"] else "0"
    ]

    if config["UseCustomRes"]:
        cmd.extend([
            "-screen-width", str(config["CustomResX"]), 
            "-screen-height", str(config["CustomResY"])
        ])

    if config["PopupWindow"]: cmd.append("-popupwindow")
    if config["MonitorNum"]: cmd.extend(["-monitor", str(config["MonitorNum"])])
    if config["AdditionalCommandLine"]: cmd.extend(config["AdditionalCommandLine"].split())

    log(f"Launching game: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, cwd=os.path.dirname(game_path))
    pid = proc.pid

    # 1. THE RACE (Immediate Attachment)
    log(f"Attaching to PID {pid}...")
    start_time = time.time()
    while module_base is None:
        try:
            pm = pymem.Pymem(pid)
            base_val = pm.process_base
            module_base = base_val.lpBaseOfDll if hasattr(base_val, 'lpBaseOfDll') else int(base_val)
            pm.read_bytes(module_base, 1)
            log(f"WON THE RACE in {int((time.time() - start_time) * 1000)}ms!")
            break
        except:
            pm = None # Reset to retry full attachment
            if time.time() - start_time > 60:
                log("Fatal: Race timeout.")
                return
            continue

    # 2. RESOLVE FPS ADDRESS (Do this before anything else)
    try:
        e_lfanew = struct.unpack("<I", pm.read_bytes(module_base + 0x3C, 4))[0]
        size_of_image = struct.unpack("<I", pm.read_bytes(module_base + e_lfanew + 0x50, 4))[0]
    except Exception as e:
        log(f"Fatal: Could not read PE headers: {e}")
        return
    
    log("Scanning for FPS pattern...")
    pattern = b"\xB9\x3C\x00\x00\x00\xE8"
    match_addr = None
    chunk_size = 1024 * 1024
    for i in range(0, size_of_image, chunk_size):
        try:
            data = pm.read_bytes(module_base + i, min(chunk_size, size_of_image - i))
            idx = data.find(pattern)
            if idx != -1:
                match_addr = module_base + i + idx
                break
        except: continue

    if not match_addr:
        log("Error: FPS Pattern not found.")
        return

    rip = match_addr + 5
    curr_rip = rip
    for _ in range(10):
        try:
            instr = pm.read_bytes(curr_rip, 1)[0]
            if instr in [0xE8, 0xE9]:
                d = struct.unpack("<i", pm.read_bytes(curr_rip + 1, 4))[0]
                curr_rip = curr_rip + d + 5
            else: break
        except: break
    
    fps_address = curr_rip + struct.unpack("<i", pm.read_bytes(curr_rip + 2, 4))[0] + 6
    log(f"Resolved FPS Address: {hex(fps_address)}")

    # 3. WINDOW SNAPPING (Now happening in background or sequentially)
    if config["PopupWindow"]:
        log("Waiting for window to snap...")
        snap_window_to_monitor_top_left(pid, config)

    # 4. SERVICE LOOP
    last_applied_target = -1
    log("FPS Unlock Active.")
    
    while True:
        try:
            # Detect game exit by checking if we can still read/write
            # This is more reliable than GetExitCodeProcess when anti-cheat is involved
            pm.write_int(fps_address, pm.read_int(fps_address))
            
            target = config["FPSTarget"]
            if config["UsePowerSave"] and get_window_thread_process_id(get_foreground_window()) != pid:
                target = 10
            
            if target != last_applied_target:
                pm.write_int(fps_address, target)
                log(f"Edit: Applied {target} FPS target.")
                last_applied_target = target
            else:
                pm.write_int(fps_address, target)
            
            time.sleep(0.062)
        except Exception:
            # If any memory operation fails, the game likely closed or access was lost
            break

    log("Game closed. Service stopping.")
    if log_file: log_file.close()
    sys.exit(0)

if __name__ == "__main__":
    try:
        unlock_fps()
    except Exception:
        if log_file:
            log(traceback.format_exc())
            log_file.close()
