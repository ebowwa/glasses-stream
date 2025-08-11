#!/usr/bin/env python3
"""Direct RTMP streaming from glasses capture"""

import cv2
import subprocess
import pyautogui
import numpy as np
import time

# Stream position - capture the actual glasses stream area
x, y, w, h = 40, 330, 340, 230  # Original capture area

# Output size for RTMP (will be resized)
output_w, output_h = 640, 480  # Standard size for better display

print("Starting direct RTMP stream...")
print("This will stream the glasses capture area directly to RTMP")

# Start FFmpeg process
command = [
    'ffmpeg',
    '-y',
    '-f', 'rawvideo',
    '-vcodec', 'rawvideo', 
    '-pix_fmt', 'bgr24',
    '-s', f'{w}x{h}',
    '-r', '30',
    '-i', '-',
    '-vf', f'scale={output_w}:{output_h}',  # Resize to output size
    '-c:v', 'libx264',
    '-preset', 'ultrafast',
    '-pix_fmt', 'yuv420p',
    '-f', 'flv',
    'rtmp://localhost/live/stream'
]

process = subprocess.Popen(command, stdin=subprocess.PIPE)

print("✅ Streaming to rtmp://localhost/live/stream")
print("Press Ctrl+C to stop")

try:
    while True:
        # Capture screen
        screenshot = pyautogui.screenshot()
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Extract region
        stream = frame[y:y+h, x:x+w]
        
        # Send to FFmpeg
        process.stdin.write(stream.tobytes())
        process.stdin.flush()
        
        time.sleep(1/30)  # 30 fps
        
except KeyboardInterrupt:
    print("\nStopping stream...")
    process.stdin.close()
    process.terminate()
    print("Done")