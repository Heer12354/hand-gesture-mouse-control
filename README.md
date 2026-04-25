# 🖐️ Hand Gesture Mouse Control

> Control your Mac cursor using nothing but your hands — powered by Python and MediaPipe.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10%2B-orange)
![Platform](https://img.shields.io/badge/Platform-macOS-lightgrey?logo=apple)
![License](https://img.shields.io/badge/License-MIT-green)


<img width="736" height="480" alt="ezgif-760f955474ad30c7" src="https://github.com/user-attachments/assets/f16d7802-e3d6-4018-8afe-1ed10f03ad6b" />


---

## ✨ Features

| Gesture | Action |
|---|---|
| ☝️ Index finger (1 hand) | Move cursor |
| ✊ Fist | Click & drag |
| 🤏 Pinch index + thumb (2nd hand) | Left click |
| 🤏 Pinch middle + thumb (2nd hand) | Right click |
| ✌️ Two fingers up (2nd hand) | Scroll up |
| ✌️ Two fingers down (2nd hand) | Scroll down |

- Real-time hand tracking at 30 FPS
- EMA-smoothed cursor — no jitter
- Gesture stabiliser — no accidental clicks
- Two-hand mode for full mouse control
- On-screen HUD with live gesture labels and FPS counter
- Auto-downloads the MediaPipe model on first run

---

## 🖥️ Demo

```
One hand  →  move the cursor
Two hands →  second hand triggers clicks & scroll
Press Q   →  quit
```

---

## 🚀 Getting Started

### Prerequisites
- macOS (Apple Silicon or Intel)
- Python 3.10 or later
- A webcam

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/Heer12354/hand-gesture-mouse-control.git
cd hand-gesture-mouse-control

# 2. (Recommended) Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Run

```bash
python gesture_mouse.py
```

The MediaPipe hand-landmarker model (~8 MB) will be downloaded automatically on the first run.

---

## 🛠️ Configuration

All tuneable settings live in the `Config` class at the top of `gesture_mouse.py`:

| Setting | Default | Description |
|---|---|---|
| `CLICK_DIST` | `0.25` | Pinch distance threshold for a click |
| `DEAD_ZONE` | `3` px | Minimum movement before cursor updates |
| `EMA_ALPHA` | `0.45` | Cursor smoothing factor (0 = frozen, 1 = raw) |
| `GESTURE_STABLE_FRAMES` | `5` | Frames required to confirm a gesture |
| `SCROLL_SPEED` | `2` | Lines scrolled per tick |
| `CLICK_DEBOUNCE` | `0.30` s | Minimum time between two clicks |

---

## 📁 Project Structure

```
hand-gesture-mouse-control/
├── gesture_mouse.py   # Main script
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

---

## 🔧 Troubleshooting

**Camera not opening**  
Make sure no other app is using the webcam, then re-run the script.

**Cursor jitter**  
Increase `DEAD_ZONE` or decrease `EMA_ALPHA` in `Config`.

**Accidental clicks**  
Increase `CLICK_DIST` (smaller pinch threshold) or `GESTURE_STABLE_FRAMES`.

**Low FPS**  
Lower `CAM_WIDTH` / `CAM_HEIGHT` in `Config`, or close other CPU-heavy apps.

---

## 🤝 Contributing

Pull requests are welcome! If you find a bug or have an idea, open an issue first so we can discuss it.

---

## 👤 Author

**Heet Bhayani** — [@Heer12354](https://github.com/Heer12354)

---

## 📄 License

This project is released under the [MIT License](LICENSE).
