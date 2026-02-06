
# KeyNet
KeyNet is a simple and powerful Python library for detecting **keyboard events** (key press, key release) and binding them to **custom callbacks**.  

With KeyNet, you can easily build **keyboard-based automation**, **hotkey triggers**, or even interactive applications that react instantly when a key is pressed.


![Logo](https://i.postimg.cc/3wWFdPFc/KeyNet.png)


## Features

-  Detect **key press** and **key release** events
- Simple `.on(event, callback)` API
- Runs in a **background thread**, so your main app keeps working
- Works out-of-the-box on Windows
- Useful for **automation, scripting, and productivity apps**


## Installation

You can install keynet by:

```bash
pip install keynet

```
    
## Usage/Examples

### Example 1 – Detect a single key
```python
from keynet import KeyNet

kn = KeyNet()

def log_key(key):
    print(f"[KeyLog] {key}")

kn.on("key_press", log_key)
kn.start()

input("Logging keys... Press Enter to quit\n")

```


### Example 2 hotkey actions

```python 
from keynet import KeyNet

kn = KeyNet()

def key_action(key):
    if key == "a":
        print("You pressed A → Triggering Action 1")
    elif key == "b":
        print("You pressed B → Triggering Action 2")
    elif key == "q":
        print("Quit hotkeys (press Enter to exit)")
        kn.stop()

kn.on("key_press", key_action)
kn.start()

input("Try pressing A, B, or Q\n")

```
###  Example 3 volume control


```python

from keynet import KeyNet
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

kn = KeyNet()

def volume_control(key):
    if key == "up":
        current = volume.GetMasterVolumeLevelScalar()
        volume.SetMasterVolumeLevelScalar(min(1.0, current + 0.1), None)
        print(f"Volume UP → {int(volume.GetMasterVolumeLevelScalar() * 100)}%")
    elif key == "down":
        current = volume.GetMasterVolumeLevelScalar()
        volume.SetMasterVolumeLevelScalar(max(0.0, current - 0.1), None)
        print(f"Volume DOWN → {int(volume.GetMasterVolumeLevelScalar() * 100)}%")

kn.on("key_press", volume_control)
kn.start()

input("Press UP/DOWN arrow keys to control volume (Enter to quit)\n")
```
### Example 4 - mouse position

```python

from keynet import KeyNet
from pynput import mouse

kn = KeyNet()
mouse_controller = mouse.Controller()

def key_mouse_combo(key):
    if key == "c":
        pos = mouse_controller.position
        print(f"Captured mouse position: {pos}")
    elif key == "r":
        mouse_controller.position = (100, 100)
        print("Moved mouse to (100, 100)")

kn.on("key_press", key_mouse_combo)
kn.start()

input("Press C to capture mouse pos, R to move mouse (Enter to quit)\n")
```

## API Reference

### `KeyNet` Class  

#### `KeyNet()`  
Create a new event detector instance.  

---

### Keyboard Event Handlers  

#### `@detector.on_key(callback)`  
Registers a callback that triggers on **every key press**.  

```python
@detector.on_key
def log_key(event):
    print(f"Key pressed: {event}")
```

#### `@detector.on_hotkey(hotkeys: List[Set[str]])`  
Registers a callback that triggers when a **hotkey combination** is pressed.  

```python
@detector.on_hotkey([{"ctrl", "shift", "x"}])
def hotkey_action(event):
    print("CTRL + SHIFT + X detected!")
```

---

### Mouse Event Handlers  

`@detector.on_click(callback)`  
Registers a callback for **mouse clicks**.  

```python
@detector.on_click
def on_click(event):
    print(f"Mouse clicked: {event}")
```

`@detector.on_scroll(callback)`  
Registers a callback for **mouse scroll events**.  

```python
@detector.on_scroll
def on_scroll(event):
    print(f"Scrolled: {event}")
```

---

### System Event Handlers  

`@detector.on_volume_change(callback)`  
Registers a callback for **system volume changes**.  

```python
@detector.on_volume_change
def on_volume_change(volume_level):
    print(f"Volume changed: {volume_level}")
```

---

### Running the Detector  

`detector.start()`  
Starts listening for all registered events.  

```python
detector.start()
```

`detector.stop()`  
Stops event detection.  

```python
detector.stop()
```

## License

[MIT](https://choosealicense.com/licenses/mit/)


## Authors

- [@Rudransh joshi](https://rudransh.kafalfpc.com/)

