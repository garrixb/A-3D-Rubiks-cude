"""
Camera-based gesture control for the Rubik's Cube using MediaPipe.
Shows camera feed in a separate OpenCV window and recognises
hand-motion gestures (swipes / twists) that mimic turning a cube.
"""

import math
import threading
import queue
import time
import os
import uuid

import cv2
import numpy as np
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import drawing_utils
from mediapipe.tasks.python.vision import HandLandmarksConnections

# ---------------------------------------------------------------------------
# Gesture commands
# ---------------------------------------------------------------------------
CMD_SCRAMBLE  = 'scramble'
CMD_SOLVE     = 'solve'
CMD_NONE      = None

# ---------------------------------------------------------------------------
# Motion parameters
# ---------------------------------------------------------------------------
# Static pose detection
POSE_HOLD_FRAMES = 3      # frames to confirm pose before triggering
POSE_COOLDOWN    = 1.0    # seconds between static pose triggers

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'hand_landmarker.task')


def _ensure_model():
    """Return the model path or None."""
    p = MODEL_PATH
    if os.path.exists(p):
        return p
    # fallback: working dir
    alt = 'hand_landmarker.task'
    if os.path.exists(alt):
        return alt
    return None


def dist2(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def is_fist(landmarks):
    """True if all four non-thumb fingers are curled."""
    for tip, pip in [(8, 6), (12, 10), (16, 14), (20, 18)]:
        if landmarks[tip].y < landmarks[pip].y:
            return False
    return True


def is_open_palm(landmarks):
    """True if all five fingers are clearly extended."""
    if dist2(landmarks[4], landmarks[0]) <= dist2(landmarks[3], landmarks[0]):
        return False
    for tip, pip in [(8, 6), (12, 10), (16, 14), (20, 18)]:
        if landmarks[tip].y >= landmarks[pip].y:
            return False
    return True


def is_gun_pose(landmarks):
    """True if hand is in gun pose: thumb+index extended, others curled."""
    thumb_extended = dist2(landmarks[4], landmarks[0]) > dist2(landmarks[3], landmarks[0])
    index_extended = landmarks[8].y < landmarks[6].y
    middle_curled = landmarks[12].y >= landmarks[10].y
    ring_curled = landmarks[16].y >= landmarks[14].y
    pinky_curled = landmarks[20].y >= landmarks[18].y
    return thumb_extended and index_extended and middle_curled and ring_curled and pinky_curled


def get_gun_direction(landmarks):
    """Get direction vector the gun is pointing.
    Returns ('U'|'D'|'L'|'R'|'F'|'B') or None."""
    wrist = landmarks[0]
    index_tip = landmarks[8]
    
    dx = index_tip.x - wrist.x
    dy = index_tip.y - wrist.y
    
    abs_dx = abs(dx)
    abs_dy = abs(dy)
    
    if max(abs_dx, abs_dy) < 0.05:
        return None
    
    if abs_dx > abs_dy:
        return 'R' if dx > 0 else 'L'
    else:
        return 'U' if dy < 0 else 'D'


# ---------------------------------------------------------------------------
class GestureController:
    """
    Webcam capture + gesture recognition in a background thread.
    Shows camera feed in an OpenCV window.
    """

    def __init__(self, model_path=None, command_queue=None):
        self.running = False
        self.thread = None
        self.queue = command_queue or queue.Queue(maxsize=8)
        self._model = None
        self._model_path = model_path or _ensure_model()
        # Window name
        self._win_name = f'手势控制 - {uuid.uuid4().hex[:4]}'
        # Gun pose state
        self._last_gun_time = 0
        self._last_gun_dir = None
        # Static pose state
        self._pose_start = None      # frame count when current pose started
        self._current_pose = None    # 'fist', 'open'
        self._last_pose_time = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def start(self):
        if self.running:
            return True
        if not self._model_path:
            print('[手势] 模型文件未找到，请将 hand_landmarker.task 放在项目根目录')
            return False
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        return True

    def stop(self):
        self.running = False
        try:
            cv2.destroyWindow(self._win_name)
        except Exception:
            pass
        if self.thread:
            self.thread.join(timeout=2.0)
            self.thread = None

    @property
    def is_active(self):
        return self.running and self.thread and self.thread.is_alive()

    def get_command(self):
        try:
            return self.queue.get_nowait()
        except queue.Empty:
            return None

    def _put_cmd(self, cmd):
        try:
            self.queue.put_nowait(cmd)
        except queue.Full:
            pass

    # ------------------------------------------------------------------
    # Model
    # ------------------------------------------------------------------
    def _load_model(self):
        if self._model is not None:
            return self._model
        try:
            options = vision.HandLandmarkerOptions(
                base_options=python.BaseOptions(model_asset_path=self._model_path),
                running_mode=vision.RunningMode.LIVE_STREAM,
                num_hands=1,
                min_hand_detection_confidence=0.6,
                min_tracking_confidence=0.5,
                result_callback=self._on_result,
            )
            self._model = vision.HandLandmarker.create_from_options(options)
            return self._model
        except Exception as e:
            print(f'[手势] 加载模型失败: {e}')
            return None

    # ------------------------------------------------------------------
    # MediaPipe callback (called from capture thread)
    # ------------------------------------------------------------------
    def _on_result(self, result, output_image, timestamp_ms):
        """Called by MediaPipe for each frame.  Stores landmarks for later
        use in the main capture loop (since we can't draw here safely)."""
        self._latest_result = result

    # ------------------------------------------------------------------
    # Capture & recognition loop
    # ------------------------------------------------------------------
    def _run(self):
        model = self._load_model()
        if model is None:
            self.running = False
            return

        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            print('[手势] 无法打开摄像头')
            self.running = False
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)

        cv2.namedWindow(self._win_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self._win_name, 640, 480)
        print(f'[手势] 摄像头已启动 — 窗口: "{self._win_name}"')

        self._latest_result = None
        self._pose_start = None
        self._current_pose = None

        timestamp = 0
        try:
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.03)
                    continue
                timestamp += 1
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                ts_us = int(time.perf_counter() * 1_000_000)
                model.detect_async(mp_image, ts_us)

                # Small sleep to let the async callback fire
                time.sleep(0.005)

                # Get latest landmarks from the callback
                lm_result = self._latest_result
                gesture_text = '未检测到手'
                color = (0, 0, 255)

                if lm_result and lm_result.hand_landmarks:
                    lm = lm_result.hand_landmarks[0]

                    # --- 1. Draw landmarks on the frame ---
                    drawing_utils.draw_landmarks(
                        frame, lm,
                        connections=HandLandmarksConnections.HAND_CONNECTIONS,
                        landmark_drawing_spec=drawing_utils.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
                        connection_drawing_spec=drawing_utils.DrawingSpec(color=(255, 0, 0), thickness=2),
                    )

                    # --- 2. Gun pose detection ---
                    if is_gun_pose(lm):
                        cmd = self._detect_gun_direction(lm)
                        if cmd:
                            gesture_text = cmd
                            color = (0, 255, 0)
                        else:
                            gesture_text = '手枪就绪'
                            color = (0, 255, 0)
                    else:
                        # --- 3. Static pose detection ---
                        cmd = self._detect_static_pose(lm)
                        if cmd:
                            gesture_text = cmd
                            color = (0, 255, 255)
                        else:
                            gesture_text = self._current_pose or '等待手势'
                            color = (0, 255, 0) if self._current_pose else (180, 180, 0)

                else:
                    # Reset state when hand is lost
                    self._pose_start = None
                    self._current_pose = None
                    self._last_gun_dir = None

                # Draw gesture label on the frame
                cv2.putText(frame, gesture_text, (20, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2,
                            cv2.LINE_AA)

                # Show the frame
                cv2.imshow(self._win_name, frame)
                key = cv2.pollKey() & 0xFF
                if key == 27:  # ESC
                    print('[手势] 用户关闭摄像头窗口')
                    self.running = False
                    break
                elif key == ord('q'):
                    self.running = False
                    break

        finally:
            cap.release()
            try:
                cv2.destroyWindow(self._win_name)
            except Exception:
                pass
            print('[手势] 摄像头已关闭')

    # ------------------------------------------------------------------
    # Gun direction detection
    # ------------------------------------------------------------------
    def _detect_gun_direction(self, lm):
        """Detect direction the gun is pointing and trigger rotation.
        Returns a command string or None."""
        GUN_COOLDOWN = 0.5
        
        dir = get_gun_direction(lm)
        if dir is None:
            return None

        now = time.time()
        if now - self._last_gun_time < GUN_COOLDOWN:
            return None

        self._last_gun_time = now
        self._last_gun_dir = dir
        
        self._put_cmd(dir)
        return f'指向 → {dir}'

    # ------------------------------------------------------------------
    # Static pose detection (fist → scramble, open palm → solve)
    # ------------------------------------------------------------------
    def _detect_static_pose(self, lm):
        """Detect static poses — triggers on hold."""
        fist = is_fist(lm)
        open_palm = is_open_palm(lm)

        pose = None
        if fist:
            pose = 'fist'
        elif open_palm:
            pose = 'open'

        if pose != self._current_pose:
            self._current_pose = pose
            self._pose_start = 0 if pose else 0
        elif pose:
            self._pose_start += 1
            if self._pose_start >= POSE_HOLD_FRAMES:
                now = time.time()
                if now - self._last_pose_time < POSE_COOLDOWN:
                    return None
                self._last_pose_time = now
                self._pose_start = 0
                
                if pose == 'fist':
                    self._put_cmd(CMD_SCRAMBLE)
                    return '握拳 → 打乱'
                elif pose == 'open':
                    self._put_cmd(CMD_SOLVE)
                    return '张手 → 复原'

        return None

    def __del__(self):
        self.stop()
