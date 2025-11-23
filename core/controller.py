import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import threading

from utils.config import load_config, save_config

class MouseController:
    def __init__(self):
        self.running = False
        self.thread = None
        self.stop_callback = None
        
        # Load Configuration
        self.config = load_config()

        # State
        self.cap = None
        self.hands = None
        self.screen_width, self.screen_height = pyautogui.size()
        
    def set_stop_callback(self, callback):
        self.stop_callback = callback

    def start(self):
        if self.running:
            return
        
        self.config["enabled"] = True 
        self.running = True
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True 
        self.thread.start()
        print("Mouse Controller Started")

    def stop(self):
        self.running = False
        self.config["enabled"] = False
        if self.thread:
            self.thread.join()
        print("Mouse Controller Stopped")

    def update_config(self, key, value):
        self.config[key] = value
        save_config(self.config)
        print(f"Config updated: {key} = {value}")

    def _run_loop(self):
        print("Thread started")
        pyautogui.PAUSE = 0
        pyautogui.FAILSAFE = False 

        mp_hands = mp.solutions.hands
        self.hands = mp_hands.Hands(
            model_complexity=0, 
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        print("Opening Camera...")
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open camera.")
            self.running = False
            return
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        print("Camera Opened Successfully")

        plocX, plocY = 0, 0
        clocX, clocY = 0, 0
        is_left_clicking = False
        is_right_clicking = False
        drag_active = False
        anchor_x, anchor_y = 0, 0
        smoothening = 5

        while self.running:
            if not self.config["enabled"]:
                # If disabled via config but loop running, just wait
                # But we usually stop the loop. This is a safety check.
                time.sleep(0.1)
                continue

            success, img = self.cap.read()
            if not success:
                continue

            img = cv2.flip(img, 1)
            h, w, c = img.shape
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = self.hands.process(img_rgb)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    landmarks = hand_landmarks.landmark
                    
                    # Tips
                    thumb_tip = landmarks[4]
                    index_tip = landmarks[8]
                    middle_tip = landmarks[12]
                    ring_tip = landmarks[16]
                    pinky_tip = landmarks[20]
                    
                    # Coordinates
                    x1, y1 = int(index_tip.x * w), int(index_tip.y * h) 
                    x2, y2 = int(thumb_tip.x * w), int(thumb_tip.y * h)               
                    x3, y3 = int(middle_tip.x * w), int(middle_tip.y * h) 
                    
                    # Fingers Up Detection
                    fingers = []
                    fingers.append(1 if thumb_tip.x < landmarks[3].x else 0) 
                    fingers.append(1 if index_tip.y < landmarks[6].y else 0)
                    fingers.append(1 if middle_tip.y < landmarks[10].y else 0)
                    fingers.append(1 if ring_tip.y < landmarks[14].y else 0)
                    fingers.append(1 if pinky_tip.y < landmarks[18].y else 0)
                    
                    # --- FIST GESTURE (STOP) ---
                    # All fingers down (0)
                    if all(f == 0 for f in fingers):
                        print("Fist Detected - Stopping")
                        self.running = False
                        self.config["enabled"] = False
                        if self.stop_callback:
                            self.stop_callback()
                        break

                    # --- SCROLL LOGIC ---
                    is_scroll_gesture = fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0
                    
                    if is_scroll_gesture and self.config.get("scroll_enabled", True):
                        mx, my = (x1 + x3) // 2, (y1 + y3) // 2
                        y_mapped = np.interp(my, (self.config["frame_margin"], h - self.config["frame_margin"]), (0, self.screen_height))
                        dy = y_mapped - plocY
                        
                        if abs(dy) > self.config["scroll_threshold"]:
                            clicks = int(dy / 5) 
                            pyautogui.scroll(-clicks * 20) 
                            
                        plocX, plocY = np.interp(mx, (self.config["frame_margin"], w - self.config["frame_margin"]), (0, self.screen_width)), y_mapped

                    else:
                        # --- MOUSE LOGIC ---
                        dist_left = np.hypot(x2 - x1, y2 - y1)
                        dist_right = np.hypot(x2 - x3, y2 - y3)
                        
                        # Mapping
                        x_mapped = np.interp(x1, (self.config["frame_margin"], w - self.config["frame_margin"]), (-20, self.screen_width + 20))
                        y_mapped = np.interp(y1, (self.config["frame_margin"], h - self.config["frame_margin"]), (-20, self.screen_height + 20))
                        
                        # Adaptive Smoothing
                        move_dist = np.hypot(x_mapped - plocX, y_mapped - plocY)
                        
                        # Movement Deadzone (Anti-Jitter for stillness)
                        if move_dist < 3: # Ignore micro-movements
                            clocX, clocY = plocX, plocY
                            should_move = False
                        else:
                            if is_left_clicking:
                                smoothening = 10 # Extra stable when dragging
                            elif move_dist > 50: 
                                smoothening = self.config["smoothening_fast"]
                            elif move_dist > 20: 
                                smoothening = self.config["smoothening_medium"]
                            else: 
                                smoothening = self.config["smoothening_slow"]
                            
                            # Move
                            clocX = plocX + (x_mapped - plocX) / smoothening
                            clocY = plocY + (y_mapped - plocY) / smoothening
                            
                            # Clamp
                            clocX = np.clip(clocX, 0, self.screen_width - 1)
                            clocY = np.clip(clocY, 0, self.screen_height - 1)

                            should_move = False
                            
                            if is_left_clicking:
                                dist_from_anchor = np.hypot(clocX - anchor_x, clocY - anchor_y)
                                if dist_from_anchor > self.config["drag_threshold"]:
                                    drag_active = True
                                
                                if drag_active:
                                    should_move = True
                            else:
                                drag_active = False 
                                if dist_left > self.config["stabilize_threshold"]:
                                    should_move = True

                        if should_move:
                            try:
                                pyautogui.moveTo(clocX, clocY, duration=0)
                            except pyautogui.FailSafeException:
                                pass
                            plocX, plocY = clocX, clocY

                        # Left Click
                        if dist_left < self.config["click_threshold"]:
                            if not is_left_clicking:
                                pyautogui.mouseDown()
                                is_left_clicking = True
                                anchor_x, anchor_y = plocX, plocY 
                        else:
                            if is_left_clicking:
                                pyautogui.mouseUp()
                                is_left_clicking = False

                        # Right Click
                        if dist_right < self.config["click_threshold"] and self.config.get("right_click_enabled", True):
                            if not is_right_clicking:
                                pyautogui.rightClick()
                                is_right_clicking = True
                                time.sleep(0.2) 
                                is_right_clicking = False 

        # Cleanup
        if self.cap:
            self.cap.release()
