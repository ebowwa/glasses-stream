#!/usr/bin/env python3
"""
Direct iPhone Screen Mirror Livestream Extractor
Immediately opens a window showing just the glasses livestream
"""

import cv2
import numpy as np
import pyautogui
import time

# Coordinates - these will be updated in real-time
STREAM_X = 40      
STREAM_Y = 330     
STREAM_WIDTH = 340   
STREAM_HEIGHT = 230

print("Starting glasses livestream extraction...")
print("Make sure your iPhone is mirrored to your Mac screen")
print("\nControls:")
print("  Arrow Keys - Move capture area (hold Shift for bigger steps)")
print("  +/- - Resize capture area")
print("  'q' - Quit")
print("  's' - Save snapshot")
print("  'c' - Click and drag calibration mode")
print("  'r' - Reset to defaults")
print("\nCurrent position: X={}, Y={}, W={}, H={}".format(STREAM_X, STREAM_Y, STREAM_WIDTH, STREAM_HEIGHT))
print("Opening stream window...\n")

# Create window
cv2.namedWindow('Glasses Livestream', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Glasses Livestream', STREAM_WIDTH * 2, STREAM_HEIGHT * 2)

step = 5  # Default movement step

while True:
    # Capture screen
    screenshot = pyautogui.screenshot()
    frame = np.array(screenshot)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    
    # Extract stream region
    stream = frame[STREAM_Y:STREAM_Y+STREAM_HEIGHT, STREAM_X:STREAM_X+STREAM_WIDTH]
    
    # Add border to show capture area clearly
    cv2.rectangle(stream, (0, 0), (STREAM_WIDTH-1, STREAM_HEIGHT-1), (0, 255, 0), 2)
    
    # Show position info on stream
    cv2.putText(stream, f"({STREAM_X},{STREAM_Y}) {STREAM_WIDTH}x{STREAM_HEIGHT}", 
                (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # Display
    cv2.imshow('Glasses Livestream', stream)
    
    # Handle keys
    key = cv2.waitKey(1) & 0xFF
    
    # Movement controls
    if key == 81:  # Left arrow
        STREAM_X -= step
        print(f"X={STREAM_X}")
    elif key == 83:  # Right arrow
        STREAM_X += step
        print(f"X={STREAM_X}")
    elif key == 82:  # Up arrow
        STREAM_Y -= step
        print(f"Y={STREAM_Y}")
    elif key == 84:  # Down arrow
        STREAM_Y += step
        print(f"Y={STREAM_Y}")
    
    # Size controls
    elif key == ord('+') or key == ord('='):
        STREAM_WIDTH += 10
        STREAM_HEIGHT += 10
        print(f"Size: {STREAM_WIDTH}x{STREAM_HEIGHT}")
    elif key == ord('-'):
        STREAM_WIDTH = max(50, STREAM_WIDTH - 10)
        STREAM_HEIGHT = max(50, STREAM_HEIGHT - 10)
        print(f"Size: {STREAM_WIDTH}x{STREAM_HEIGHT}")
    
    # Other controls
    elif key == ord('q'):
        print("Closing stream...")
        break
    elif key == ord('s'):
        filename = f"stream_{time.strftime('%Y%m%d_%H%M%S')}.png"
        cv2.imwrite(filename, stream)
        print(f"Saved: {filename}")
    elif key == ord('c'):
        print("\nCalibration mode - Select the livestream area")
        roi = cv2.selectROI("Select Stream Area", frame, False)
        cv2.destroyWindow("Select Stream Area")
        if roi[2] > 0 and roi[3] > 0:
            STREAM_X, STREAM_Y, STREAM_WIDTH, STREAM_HEIGHT = roi
            print(f"New coordinates: X={STREAM_X}, Y={STREAM_Y}, W={STREAM_WIDTH}, H={STREAM_HEIGHT}")
    elif key == ord('r'):
        STREAM_X, STREAM_Y = 40, 330
        STREAM_WIDTH, STREAM_HEIGHT = 340, 230
        print("Reset to defaults")

cv2.destroyAllWindows()