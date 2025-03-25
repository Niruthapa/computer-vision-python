import cv2
import mediapipe as mp
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import tkinter as tk
from tkinter import ttk

# Try importing screen_brightness_control, handle errors
try:
    import screen_brightness_control as sbc
    brightness_control_available = True
except ImportError:
    brightness_control_available = False
    print("Warning: screen_brightness_control module not found. Brightness control will be disabled.")

# Initialize MediaPipe Hands module
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_drawing = mp.solutions.drawing_utils

# Get the default audio endpoint (speaker) for volume control
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

# Function to update volume
def update_volume(distance):
    min_distance, max_distance = 0.05, 0.3
    min_volume, max_volume = 0.0, 1.0
    new_volume = (distance - min_distance) / (max_distance - min_distance) * (max_volume - min_volume) + min_volume
    new_volume = max(min_volume, min(max_volume, new_volume))
    volume.SetMasterVolumeLevelScalar(new_volume, None)
    return new_volume * 100  # Convert to percentage

# Function to update brightness
def update_brightness(distance):
    if not brightness_control_available:
        return 0  # Return 0 brightness if the module is unavailable
    
    min_distance, max_distance = 0.05, 0.3
    min_brightness, max_brightness = 10, 100
    new_brightness = (distance - min_distance) / (max_distance - min_distance) * (max_brightness - min_brightness) + min_brightness
    new_brightness = int(max(min_brightness, min(max_brightness, new_brightness)))
    sbc.set_brightness(new_brightness)
    return new_brightness

# GUI setup
root = tk.Tk()
root.title("Hand Gesture Control")
root.geometry("300x150")

tk.Label(root, text="Right Hand: Brightness | Left Hand: Volume").pack()
volume_progress = ttk.Progressbar(root, orient='horizontal', length=200, mode='determinate')
volume_progress.pack()
brightness_progress = ttk.Progressbar(root, orient='horizontal', length=200, mode='determinate')
brightness_progress.pack()

# Webcam setup
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        continue
    
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)
    
    brightness = 0  # Initialize brightness variable

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            thumb_x = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].x
            thumb_y = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].y
            index_x = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x
            index_y = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y
            
            distance = math.dist([thumb_x, thumb_y], [index_x, index_y])
            
            # Check hand side
            if hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x < 0.5:# Right hand  
                brightness = update_brightness(distance)
                brightness_progress['value'] = brightness
            else:   # Left hand
                volume_level = update_volume(distance)
                volume_progress['value'] = volume_level
                
                # Display volume on screen
                cv2.putText(frame, f'Volume: {volume_level:.2f}%', (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)

            # Display brightness on screen (only if brightness control is available)
            if brightness_control_available:
                cv2.putText(frame, f'Brightness: {brightness:.2f}%', (10, 60), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
    
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    cv2.imshow('Camera Feed', frame)
    
    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
root.mainloop()
