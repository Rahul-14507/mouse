import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time

def main():
    # Optimize PyAutoGUI
    pyautogui.PAUSE = 0
    pyautogui.FAILSAFE = False 

    # Initialize MediaPipe Hands
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        model_complexity=0, 
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    mp_draw = mp.solutions.drawing_utils

    # Screen dimensions
    screen_width, screen_height = pyautogui.size()

    # Camera setup
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Frame margin 
    frame_margin = 70
    
    # Smoothing variables
    smoothening = 5
    plocX, plocY = 0, 0
    clocX, clocY = 0, 0

    # Click state
    is_left_clicking = False
    is_right_clicking = False
    
    # Anchor for dragging
    drag_active = False
    anchor_x, anchor_y = 0, 0
    
    # Thresholds
    click_threshold = 30       
    stabilize_threshold = 50   
    drag_threshold = 40        
    scroll_threshold = 15      

    # FPS Calculation
    pTime = 0
    cTime = 0

    print("Starting Hand Gesture Mouse Control (Final Optimized)...")
    print("Press 'q' to quit.")

    while True:
        success, img = cap.read()
        if not success:
            continue

        img = cv2.flip(img, 1)
        h, w, c = img.shape
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Landmarks
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
                
                # --- Finger State Detection ---
                fingers = []
                # Thumb (Check x for side movement or IP y)
                fingers.append(1 if thumb_tip.x < landmarks[3].x else 0) 
                fingers.append(1 if index_tip.y < landmarks[6].y else 0)
                fingers.append(1 if middle_tip.y < landmarks[10].y else 0)
                fingers.append(1 if ring_tip.y < landmarks[14].y else 0)
                fingers.append(1 if pinky_tip.y < landmarks[18].y else 0)
                
                # --- Logic State Machine ---
                mode_text = "None"
                
                # Scroll Gesture: Index & Middle UP, Others DOWN
                is_scroll_gesture = fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0
                
                if is_scroll_gesture:
                    # --- SCROLL MODE ---
                    mode_text = "Scroll"
                    mx, my = (x1 + x3) // 2, (y1 + y3) // 2
                    
                    # Map current Y to screen
                    y_mapped = np.interp(my, (frame_margin, h - frame_margin), (0, screen_height))
                    
                    # Calculate delta
                    dy = y_mapped - plocY
                    
                    if abs(dy) > scroll_threshold:
                        clicks = int(dy / 5) 
                        pyautogui.scroll(-clicks * 20) 
                        
                    # Update ploc (using mapped Y for consistency)
                    plocX, plocY = np.interp(mx, (frame_margin, w - frame_margin), (0, screen_width)), y_mapped

                else:
                    # --- MOUSE CONTROL MODE ---
                    dist_left = np.hypot(x2 - x1, y2 - y1)    # Index - Thumb
                    dist_right = np.hypot(x2 - x3, y2 - y3)   # Middle - Thumb
                    
                    # Calculate Target Position with Edge Clamping
                    # Map to slightly larger area (-20 to width+20) to ensure edges are reachable
                    x_mapped = np.interp(x1, (frame_margin, w - frame_margin), (-20, screen_width + 20))
                    y_mapped = np.interp(y1, (frame_margin, h - frame_margin), (-20, screen_height + 20))
                    
                    # Adaptive Smoothing
                    move_dist = np.hypot(x_mapped - plocX, y_mapped - plocY)
                    if is_left_clicking:
                        smoothening = 8 
                    elif move_dist > 50: 
                        smoothening = 2
                    elif move_dist > 20: 
                        smoothening = 4
                    else: 
                        smoothening = 7
                    
                    # Apply Smoothing
                    clocX = plocX + (x_mapped - plocX) / smoothening
                    clocY = plocY + (y_mapped - plocY) / smoothening
                    
                    # Clamp to screen dimensions
                    clocX = np.clip(clocX, 0, screen_width - 1)
                    clocY = np.clip(clocY, 0, screen_height - 1)

                    should_move = False
                    
                    if is_left_clicking:
                        dist_from_anchor = np.hypot(clocX - anchor_x, clocY - anchor_y)
                        if dist_from_anchor > drag_threshold:
                            drag_active = True
                        
                        if drag_active:
                            should_move = True
                            mode_text = "Drag"
                        else:
                            should_move = False
                            mode_text = "Click Locked"
                    else:
                        drag_active = False 
                        if dist_left > stabilize_threshold:
                            should_move = True
                            mode_text = "Move"
                        else:
                            should_move = False
                            mode_text = "Stabilize"

                    if should_move:
                        try:
                            pyautogui.moveTo(clocX, clocY, duration=0)
                        except pyautogui.FailSafeException:
                            pass
                        plocX, plocY = clocX, clocY

                    # --- Left Click ---
                    if dist_left < click_threshold:
                        cv2.circle(img, ((x1 + x2) // 2, (y1 + y2) // 2), 10, (0, 255, 0), cv2.FILLED)
                        if not is_left_clicking:
                            pyautogui.mouseDown()
                            is_left_clicking = True
                            anchor_x, anchor_y = plocX, plocY 
                    else:
                        if is_left_clicking:
                            pyautogui.mouseUp()
                            is_left_clicking = False

                    # --- Right Click ---
                    if dist_right < click_threshold:
                        if not is_right_clicking:
                            pyautogui.rightClick()
                            is_right_clicking = True
                            time.sleep(0.2) 
                            is_right_clicking = False 

                # Debug Text
                cv2.putText(img, f"{mode_text}", (20, 100), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 255), 2)

        # FPS Calculation
        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime
        cv2.putText(img, f'FPS: {int(fps)}', (20, 50), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 3)

        cv2.imshow("Hand Gesture Mouse", img)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
