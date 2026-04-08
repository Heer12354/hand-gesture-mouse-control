# 🖐️ Hand Gesture Mouse Control

Control your Mac cursor using only hand gestures — no mouse needed. Built with Python, MediaPipe, and OpenCV.

> **Built from scratch** — started with zero computer vision knowledge and iterated across 13 versions with help from Claude (Anthropic AI).

---

## 📸 Demo

| Gesture | Action |
|---|---|
| ☝️ Point (1 hand) | Move cursor |
| ✊ Fist (1 hand) | Click & drag |
| 🤏 Index + Thumb pinch (2nd hand) | Left click |
| 🤏 Middle + Thumb pinch (2nd hand) | Right click |
| ✌️ Two fingers up (2nd hand) | Scroll up |
| ✌️ Two fingers down (2nd hand) | Scroll down |

---

## 🧰 Tech Stack

| Tool | Version |
|---|---|
| Python | 3.13 |
| MediaPipe | 0.10.33 |
| OpenCV | Latest |
| PyAutoGUI | Latest |
| NumPy | Latest |

---

## ⚙️ Setup & Installation

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/hand-gesture-mouse-control.git
cd hand-gesture-mouse-control
```

### 2. Create a virtual environment

> Required on macOS due to the externally managed Python environment.

```bash
python3 -m venv handgesture
source handgesture/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** Only `mediapipe==0.10.33` works with Python 3.13. Versions below 0.10.30 are not available for Python 3.13.

### 4. Run the program

```bash
python hand_control.py
```

> The MediaPipe hand landmark model (`hand_landmarker.task`, ~10MB) will be **auto-downloaded** on first run.

---

## 🎮 Controls

### Single Hand Mode (Cursor Control)

| Gesture | Action |
|---|---|
| Move index finger | Moves the cursor |
| Fist | Holds mouse button (drag) |

### Two Hand Mode (Action Hand)

Show your second hand in frame to trigger actions:

| Gesture (2nd hand) | Action |
|---|---|
| Index + Thumb pinch | Left click |
| Middle + Thumb pinch | Right click |
| Index + Middle fingers up, ring + pinky down | Scroll up |
| Index + Middle fingers down, pinky up | Scroll down |

**Press `q` to quit.**

---

## 🔧 Configuration

You can tweak these constants at the top of `hand_control.py`:

```python
CLICK_DIST = 0.25        # Pinch distance threshold for clicks
DEAD_ZONE = 3            # Minimum pixel movement to update cursor
SCROLL_SPEED = 2         # Scroll steps per gesture
GESTURE_STABLE_FRAMES = 5  # Frames needed to confirm a gesture
EMA_ALPHA = 0.45         # Smoothing factor (higher = faster, less smooth)
CLICK_DEBOUNCE = 0.3     # Seconds between clicks (prevents accidental double-clicks)
```

---

## 🐛 Known Issues & Fixes

| Problem | Fix |
|---|---|
| `AttributeError: module 'mediapipe' has no attribute 'solutions'` | Use `mediapipe==0.10.33` — the new Tasks API replaced the old `mp.solutions` API |
| High lag / low FPS | Set `pyautogui.PAUSE = 0`, use 640×480 resolution, process every frame |
| Cursor not reaching screen edges | Use margin mapping to remap the hand's active zone to the full screen |
| Accidental clicks | Added `GestureStabilizer` class + click debounce timer |
| macOS pip install error (externally managed) | Use a virtual environment (`python3 -m venv`) |

---

## 📁 Project Structure

```
hand-gesture-mouse-control/
├── hand_control.py      # Main script
├── requirements.txt     # Python dependencies
├── .gitignore
└── README.md
```

> `hand_landmarker.task` is auto-downloaded on first run and excluded from git via `.gitignore`.

---

## 🚀 How It Works

1. **Webcam** captures frames at 640×480 via OpenCV
2. **MediaPipe** Hand Landmarker detects 21 landmarks per hand in real time (async LIVE_STREAM mode)
3. **Gesture classifier** reads finger positions and computes ratios to identify gestures
4. **GestureStabilizer** requires a gesture to appear consistently across multiple frames before acting
5. **EMA smoothing** reduces jitter in cursor movement
6. **PyAutoGUI** executes the mouse action (move, click, scroll, drag)

---

## 📖 Development Story

This project was built iteratively across **13 versions** over several days. It started after seeing an Instagram Reel showing cursor control via webcam, and the goal was to replicate it on macOS from scratch.

Key milestones:
- **v1** — First attempt using old `mp.solutions.hands` API (broke immediately on newer mediapipe)
- **v2** — Rewrote using new MediaPipe Tasks API
- **v3-v5** — Fixed lag, improved accuracy, added margin mapping
- **v6-v8** — Added two-hand support, scroll gestures, drag
- **v9-v11** — Added gesture stabilizer, click debounce, visual HUD
- **v12-v13** — Final optimization: reduced lag, better FPS, cleaner code

---

## 🙏 Credits

- Built by **Heet** with assistance from [Claude](https://claude.ai) (Anthropic AI)
- Hand landmark model by [Google MediaPipe](https://mediapipe-studio.webapps.google.com/home)

---

## 📄 License

MIT License — free to use, modify, and share.
