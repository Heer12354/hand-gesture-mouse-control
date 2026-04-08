import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import pyautogui
import time
import os
import urllib.request
import numpy as np
import threading

# ===== OPTIMIZED SETTINGS =====
CAM_WIDTH = 640
CAM_HEIGHT = 480
CLICK_DIST = 0.25  # Reduced accidental clicks
DEAD_ZONE = 3  # Reduced lag
SCROLL_SPEED = 2
GESTURE_STABLE_FRAMES = 5  # Increased to prevent accidental clicks

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0
screen_w, screen_h = pyautogui.size()

# ===== HAND CONNECTIONS & COLORS =====
HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),
    (5,9),(9,10),(10,11),(11,12),(9,13),(13,14),(14,15),(15,16),
    (13,17),(17,18),(18,19),(19,20),(0,17)
]

GESTURE_COLORS = {
    "none": (140,140,150), "neutral": (180,180,190),
    "open_palm": (60,220,120), "fist": (80,80,255),
    "pinch": (40,210,255), "point": (255,190,80),
    "peace": (230,240,0), "thumbs_up": (0,170,255),
    "thumbs_down": (255,110,110), "ok_sign": (170,0,255),
}

ACTION_STYLES = {
    "LEFT CLICK!": (0,255,0), "RIGHT CLICK!": (0,0,255),
    "SCROLL UP!": (0,255,100), "SCROLL DOWN!": (0,100,255),
    "DRAGGING!": (0,165,255), "No Hand Detected": (0,0,255),
}

# ===== AUTO DOWNLOAD MODEL =====
model_path = "hand_landmarker.task"
if not os.path.exists(model_path):
    print("Downloading hand tracking model...")
    try:
        urllib.request.urlretrieve(
            "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
            model_path
        )
        print("Model downloaded successfully!")
    except Exception as e:
        print(f"Error downloading model: {e}")
        print("Please download manually from the URL above")
        exit()

# ===== MEDIAPIPE SETUP WITH ERROR HANDLING =====
latest_result = None
result_lock = threading.Lock()

def save_result(result, output_image, timestamp_ms):
    global latest_result
    with result_lock:
        latest_result = result

try:
    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.LIVE_STREAM,
        num_hands=2,
        min_hand_detection_confidence=0.6,
        min_hand_presence_confidence=0.6,
        min_tracking_confidence=0.6,
        result_callback=save_result
    )
    detector = vision.HandLandmarker.create_from_options(options)
except Exception as e:
    print(f"Error initializing detector: {e}")
    exit()

# ===== CAMERA SETUP WITH ERROR HANDLING =====
try:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise Exception("Cannot open camera")
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
except Exception as e:
    print(f"Camera error: {e}")
    exit()

# ===== OPTIMIZED SMOOTHING =====
ema_x, ema_y = screen_w // 2, screen_h // 2
EMA_ALPHA = 0.45
prev_x, prev_y = screen_w // 2, screen_h // 2

# ===== STATE VARIABLES =====
timestamp = 0
frame_count = 0
drag_active = False
scroll_cooldown = 0
fps_counter = 0
fps_time = time.time()
fps = 0
action_text = ""
action_timer = 0
ACTION_DISPLAY_DURATION = 0.6

# ===== GESTURE STABILIZER =====
class GestureStabilizer:
    def __init__(self):
        self.candidate = "none"
        self.stable = "none"
        self.frames = 0
        self.history = []
        self.max_history = 5
    
    def update(self, raw_gesture):
        self.history.append(raw_gesture)
        if len(self.history) > self.max_history:
            self.history.pop(0)
        
        if len(self.history) >= 3:
            from collections import Counter
            most_common = Counter(self.history).most_common(1)[0][0]
            if self.candidate == most_common:
                self.frames += 1
            else:
                self.candidate = most_common
                self.frames = 1
            
            if self.frames >= GESTURE_STABLE_FRAMES:
                self.stable = self.candidate
        
        return self.stable

stabilizer_hand1 = GestureStabilizer()
stabilizer_hand2 = GestureStabilizer()
left_pinch_active = False
right_pinch_active = False
click_debounce_timer = 0
CLICK_DEBOUNCE = 0.3

# ===== HELPER FUNCTIONS =====
def hand_size(lm):
    return max(np.hypot(lm[9].x - lm[0].x, lm[9].y - lm[0].y), 0.001)

def finger_ratio(lm, tip_id, pip_id):
    wrist = lm[0]
    dt = np.hypot(lm[tip_id].x - wrist.x, lm[tip_id].y - wrist.y)
    dp = max(np.hypot(lm[pip_id].x - wrist.x, lm[pip_id].y - wrist.y), 0.001)
    return dt / dp

def finger_open(lm, tip_id, pip_id):
    return finger_ratio(lm, tip_id, pip_id) > 1.05

def thumb_extended(lm):
    return np.hypot(lm[4].x - lm[5].x, lm[4].y - lm[5].y) / hand_size(lm) > 0.34

def classify_gesture(lm):
    index_open = finger_open(lm, 8, 6)
    middle_open = finger_open(lm, 12, 10)
    ring_open = finger_open(lm, 16, 14)
    pinky_open = finger_open(lm, 20, 18)
    open_count = sum([index_open, middle_open, ring_open, pinky_open])
    thumb_open = thumb_extended(lm)
    size = hand_size(lm)
    pinch_ti = np.hypot(lm[4].x - lm[8].x, lm[4].y - lm[8].y) / size
    wrist = lm[0]
    thumb_tip_y = lm[4].y
    
    if pinch_ti < 0.22 and middle_open and ring_open and pinky_open: return "ok_sign"
    if pinch_ti < 0.28 and open_count >= 2: return "pinch"
    if thumb_tip_y < wrist.y - size * 0.28 and open_count <= 1: return "thumbs_up"
    if thumb_tip_y > wrist.y + size * 0.22 and open_count <= 1: return "thumbs_down"
    if index_open and middle_open and ring_open and pinky_open and thumb_open: return "open_palm"
    if index_open and middle_open and not ring_open and not pinky_open: return "peace"
    if index_open and not middle_open and not ring_open and not pinky_open: return "point"
    if open_count <= 1 and not thumb_open: return "fist"
    return "neutral"

def is_scroll_up(lm):
    index_up = lm[8].y < lm[6].y
    middle_up = lm[12].y < lm[10].y
    ring_down = lm[16].y > lm[14].y
    pinky_down = lm[20].y > lm[18].y
    return index_up and middle_up and ring_down and pinky_down

def is_scroll_down(lm):
    index_down = lm[8].y > lm[6].y
    middle_down = lm[12].y > lm[10].y
    ring_down = lm[16].y > lm[14].y
    pinky_up = lm[20].y < lm[18].y
    return index_down and middle_down and ring_down and pinky_up

def draw_hand(frame, lm, gesture, w, h):
    color = GESTURE_COLORS.get(gesture, (180,180,190))
    for a, b in HAND_CONNECTIONS:
        x1,y1 = int(lm[a].x*w), int(lm[a].y*h)
        x2,y2 = int(lm[b].x*w), int(lm[b].y*h)
        cv2.line(frame, (x1,y1), (x2,y2), (0,0,0), 5)
        cv2.line(frame, (x1,y1), (x2,y2), color, 2)
    for i, point in enumerate(lm):
        x,y = int(point.x*w), int(point.y*h)
        dot_color = (160,245,255) if i in [4,8] else (255,255,255)
        cv2.circle(frame, (x,y), 5, (0,0,0), -1)
        cv2.circle(frame, (x,y), 3, dot_color, -1)

def draw_action_text(frame, text, w, h):
    if not text: return
    color = ACTION_STYLES.get(text, (255,255,255))
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale, thickness = 1.2, 3
    text_size = cv2.getTextSize(text, font, scale, thickness)[0]
    text_x = (w - text_size[0]) // 2
    text_y = h - 40
    cv2.putText(frame, text, (text_x+2, text_y+2), font, scale, (0,0,0), thickness+2)
    cv2.putText(frame, text, (text_x, text_y), font, scale, color, thickness)

def draw_hud(frame, w, h, gesture1, gesture2, fps, num_hands):
    overlay = frame.copy()
    cv2.rectangle(overlay, (0,0), (w,70), (10,12,20), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
    cv2.putText(frame, f"FPS: {fps:.0f}", (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (150,200,255), 1)
    color1 = GESTURE_COLORS.get(gesture1, (180,180,190))
    cv2.putText(frame, f"CURSOR: {gesture1}", (10,42), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color1, 2)
    if num_hands == 2:
        color2 = GESTURE_COLORS.get(gesture2, (180,180,190))
        cv2.putText(frame, f"ACTION: {gesture2}", (10,62), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color2, 2)
    else:
        cv2.putText(frame, "ACTION: show 2nd hand", (10,62), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100,100,100), 1)

# ===== MAIN LOOP =====
print("=" * 50)
print("HAND GESTURE MOUSE CONTROL")
print("=" * 50)
print("Controls:")
print("  1 Hand  → Move index finger to control cursor")
print("  2 Hands → Use action hand for clicks/scroll")
print("  Press 'q' to quit")
print("=" * 50)

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame, retrying...")
            time.sleep(0.1)
            continue
        
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        frame_count += 1
        
        fps_counter += 1
        if time.time() - fps_time >= 1.0:
            fps = fps_counter
            fps_counter = 0
            fps_time = time.time()
        
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            timestamp += 1
            detector.detect_async(mp_image, timestamp)
        except Exception as e:
            print(f"Detection error: {e}")
            continue
        
        gesture1 = "none"
        gesture2 = "none"
        current_action = ""
        num_hands = 0
        
        with result_lock:
            current_result = latest_result
        
        if current_result and current_result.hand_landmarks:
            num_hands = len(current_result.hand_landmarks)
            cursor_hand = current_result.hand_landmarks[0]
            gesture1 = stabilizer_hand1.update(classify_gesture(cursor_hand))
            draw_hand(frame, cursor_hand, gesture1, w, h)
            
            margin = 0.08
            mapped_x = (cursor_hand[8].x - margin) / (1 - 2 * margin) * screen_w
            mapped_y = (cursor_hand[8].y - margin) / (1 - 2 * margin) * screen_h
            mapped_x = max(0, min(screen_w, mapped_x))
            mapped_y = max(0, min(screen_h, mapped_y))
            
            ema_x = ema_x + EMA_ALPHA * (mapped_x - ema_x)
            ema_y = ema_y + EMA_ALPHA * (mapped_y - ema_y)
            
            if gesture1 == "fist":
                if not drag_active:
                    pyautogui.mouseDown()
                    drag_active = True
                pyautogui.moveTo(ema_x, ema_y)
                current_action = "DRAGGING!"
            else:
                if drag_active:
                    pyautogui.mouseUp()
                    drag_active = False
                
                dist_moved = np.hypot(ema_x - prev_x, ema_y - prev_y)
                if dist_moved > DEAD_ZONE:
                    pyautogui.moveTo(ema_x, ema_y)
                    prev_x, prev_y = ema_x, ema_y
            
            if num_hands == 2:
                action_hand = current_result.hand_landmarks[1]
                gesture2 = stabilizer_hand2.update(classify_gesture(action_hand))
                draw_hand(frame, action_hand, gesture2, w, h)
                size2 = hand_size(action_hand)
                
                if is_scroll_up(action_hand):
                    if time.time() - scroll_cooldown > 0.12:
                        pyautogui.scroll(SCROLL_SPEED)
                        scroll_cooldown = time.time()
                    current_action = "SCROLL UP!"
                    left_pinch_active = False
                    right_pinch_active = False
                elif is_scroll_down(action_hand):
                    if time.time() - scroll_cooldown > 0.12:
                        pyautogui.scroll(-SCROLL_SPEED)
                        scroll_cooldown = time.time()
                    current_action = "SCROLL DOWN!"
                    left_pinch_active = False
                    right_pinch_active = False
                else:
                    pinch_dist = np.hypot(action_hand[8].x-action_hand[4].x, action_hand[8].y-action_hand[4].y) / size2
                    right_dist = np.hypot(action_hand[12].x-action_hand[4].x, action_hand[12].y-action_hand[4].y) / size2
                    
                    current_time = time.time()
                    
                    if pinch_dist < CLICK_DIST and pinch_dist < right_dist:
                        if not left_pinch_active and (current_time - click_debounce_timer) > CLICK_DEBOUNCE:
                            pyautogui.click()
                            left_pinch_active = True
                            click_debounce_timer = current_time
                            action_text = "LEFT CLICK!"
                            action_timer = current_time
                        right_pinch_active = False
                    
                    elif right_dist < CLICK_DIST and right_dist < pinch_dist:
                        if not right_pinch_active and (current_time - click_debounce_timer) > CLICK_DEBOUNCE:
                            pyautogui.rightClick()
                            right_pinch_active = True
                            click_debounce_timer = current_time
                            action_text = "RIGHT CLICK!"
                            action_timer = current_time
                        left_pinch_active = False
                    
                    else:
                        left_pinch_active = False
                        right_pinch_active = False
            else:
                stabilizer_hand2.update("none")
                left_pinch_active = False
                right_pinch_active = False
        else:
            stabilizer_hand1.update("none")
            stabilizer_hand2.update("none")
            if drag_active:
                pyautogui.mouseUp()
                drag_active = False
            left_pinch_active = False
            right_pinch_active = False
            current_action = "No Hand Detected"
        
        if current_action:
            action_text = current_action
            action_timer = time.time()
        
        draw_hud(frame, w, h, gesture1, gesture2, fps, num_hands)
        
        if action_text and (time.time() - action_timer) < ACTION_DISPLAY_DURATION:
            draw_action_text(frame, action_text, w, h)
        else:
            action_text = ""
        
        cv2.imshow("Hand Gesture Mouse Control", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("\nProgram interrupted by user")
except Exception as e:
    print(f"\nError occurred: {e}")
    import traceback
    traceback.print_exc()
finally:
    print("Cleaning up...")
    if drag_active:
        try:
            pyautogui.mouseUp()
        except:
            pass
    cap.release()
    cv2.destroyAllWindows()
    print("Program closed successfully")
