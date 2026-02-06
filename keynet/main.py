# main.py
import threading
import time
import platform
from typing import Callable, Set, List, Tuple, Dict, Any, Optional
import psutil
from pynput import keyboard, mouse
from pynput.keyboard import Key, KeyCode
import subprocess

if platform.system() == "Windows":
    import pythoncom
    from ctypes import POINTER, cast
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume


class KeyNet:
    """Cross-platform system event monitor (keyboard, mouse, battery, network, volume)."""

    def __init__(self):
        self.listeners: Dict[str, List[Tuple[Callable, Dict[str, Any]]]] = {
            "key_press": [],
            "key_release": [],
            "key_combo": [],
            "mouse_click": [],
            "mouse_move": [],
            "mouse_scroll": [],
            "volume_threshold": [],
            "volume_mute": [],
            "battery": [],
            "network": []
        }
        self.current_keys: Set[str] = set()
        self.running: bool = False
        self._key_lock = threading.Lock()
        self._keyboard_listener: Optional[keyboard.Listener] = None
        self._mouse_listener: Optional[mouse.Listener] = None
        self.os = platform.system().lower()

    # -------------------- Input Handling --------------------

    def _key_to_string(self, key: Key | KeyCode) -> str:
        if isinstance(key, KeyCode) and key.char:
            return key.char.lower()
        elif isinstance(key, Key):
            return key.name.lower() if key.name else str(key)
        return str(key).strip("'")

    def on(self, event_type: str, callback: Callable, **kwargs) -> None:
        if event_type not in self.listeners:
            raise ValueError(f"Unknown event type: {event_type}")
        self.listeners[event_type].append((callback, kwargs))

    def _check_combo(self, combo: List[str]) -> bool:
        with self._key_lock:
            return set(combo).issubset(self.current_keys)

    # -------------------- Keyboard & Mouse --------------------

    def _start_keyboard_listener(self) -> None:
        def on_press(key):
            key_str = self._key_to_string(key)
            with self._key_lock:
                self.current_keys.add(key_str)
            for cb, _ in self.listeners["key_press"]:
                cb(key_str)
            for cb, params in self.listeners["key_combo"]:
                combo = params.get("combo", [])
                if combo and self._check_combo(combo):
                    cb(combo)

        def on_release(key):
            key_str = self._key_to_string(key)
            with self._key_lock:
                self.current_keys.discard(key_str)
            for cb, _ in self.listeners["key_release"]:
                cb(key_str)

        self._keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self._keyboard_listener.start()

    def _start_mouse_listener(self) -> None:
        def on_click(x, y, button, pressed):
            for cb, _ in self.listeners["mouse_click"]:
                cb(x, y, button, pressed)

        def on_move(x, y):
            for cb, _ in self.listeners["mouse_move"]:
                cb(x, y)

        def on_scroll(x, y, dx, dy):
            for cb, _ in self.listeners["mouse_scroll"]:
                cb(x, y, dx, dy)

        self._mouse_listener = mouse.Listener(on_click=on_click, on_move=on_move, on_scroll=on_scroll)
        self._mouse_listener.start()

    # -------------------- System Monitors --------------------

    def _start_system_monitors(self) -> None:
        def monitor():
            if self.os == "windows":
                pythoncom.CoInitialize()
            try:
                last_battery = None
                last_net = None
                last_vol_state = None
                last_mute_state = None
                while self.running:
                    # Battery
                    if self.listeners["battery"]:
                        try:
                            batt = psutil.sensors_battery()
                            if batt and (last_battery != (batt.percent, batt.power_plugged)):
                                last_battery = (batt.percent, batt.power_plugged)
                                for cb, _ in self.listeners["battery"]:
                                    cb(batt.percent, batt.power_plugged)
                        except Exception as e:
                            print("Battery error:", e)

                    # Network
                    if self.listeners["network"]:
                        try:
                            net = psutil.net_if_stats()
                            connected = any(iface.isup for iface in net.values())
                            if last_net != connected:
                                last_net = connected
                                for cb, _ in self.listeners["network"]:
                                    cb(connected)
                        except Exception as e:
                            print("Network error:", e)

                    # Volume
                    if self.listeners["volume_threshold"] or self.listeners["volume_mute"]:
                        try:
                            vol, muted = self._get_system_volume()
                            if vol is not None:
                                for cb, params in self.listeners["volume_threshold"]:
                                    threshold = params.get("threshold", 50)
                                    if last_vol_state != (vol >= threshold):
                                        last_vol_state = (vol >= threshold)
                                        cb(vol)
                            if muted is not None and muted != last_mute_state:
                                last_mute_state = muted
                                for cb, _ in self.listeners["volume_mute"]:
                                    cb(muted)
                        except Exception as e:
                            print("Volume error:", e)
                    time.sleep(1)
            finally:
                if self.os == "windows":
                    pythoncom.CoUninitialize()

        threading.Thread(target=monitor, daemon=True).start()

    # -------------------- Cross-Platform Volume --------------------

    def _get_system_volume(self) -> Tuple[Optional[int], Optional[bool]]:
        """Get system volume and mute state depending on OS."""
        try:
            if self.os == "windows":
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                vol = int(volume.GetMasterVolumeLevelScalar() * 100)
                return vol, bool(volume.GetMute())

            elif self.os == "darwin":  # macOS
                output = subprocess.run(
                    ["osascript", "-e", "output volume of (get volume settings)"],
                    capture_output=True, text=True
                )
                vol = int(output.stdout.strip()) if output.stdout.strip() else None
                muted_output = subprocess.run(
                    ["osascript", "-e", "output muted of (get volume settings)"],
                    capture_output=True, text=True
                )
                muted = muted_output.stdout.strip().lower() == "true"
                return vol, muted

            elif self.os == "linux":
                try:
                    output = subprocess.run(
                        ["amixer", "get", "Master"],
                        capture_output=True, text=True
                    )
                    vol_line = [line for line in output.stdout.split("\n") if "%" in line]
                    if vol_line:
                        vol_str = vol_line[0].split("[")[1].split("%")[0]
                        muted = "off" in vol_line[0].lower()
                        return int(vol_str), muted
                except FileNotFoundError:
                    return None, None

            return None, None
        except Exception as e:
            print("Volume detection error:", e)
            return None, None

    # -------------------- Start / Stop --------------------

    def start(self) -> None:
        self.running = True
        self._start_keyboard_listener()
        self._start_mouse_listener()
        self._start_system_monitors()

    def stop(self) -> None:
        self.running = False
        if self._keyboard_listener:
            self._keyboard_listener.stop()
        if self._mouse_listener:
            self._mouse_listener.stop()
