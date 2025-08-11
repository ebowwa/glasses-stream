# iPhone Glasses Stream Extraction System

## Problem
Need to extract the livestream from iPhone-mirrored glasses app (LensMoo) to use the camera feed for AI processing, recording, and other applications.

## Current Solution
Python script that captures iPhone screen mirror and extracts just the camera livestream portion.

## Requirements
- iPhone with glasses app (LensMoo) connected to smart glasses
- Mac with screen mirroring capability
- Python with OpenCV

## Working Code
```python
#!/usr/bin/env python3
import cv2
import numpy as np
import pyautogui
import time

# Coordinates for livestream box
STREAM_X = 40      
STREAM_Y = 330     
STREAM_WIDTH = 340   
STREAM_HEIGHT = 230

cv2.namedWindow('Glasses Livestream', cv2.WINDOW_NORMAL)

while True:
    # Capture screen
    screenshot = pyautogui.screenshot()
    frame = np.array(screenshot)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    
    # Extract stream region
    stream = frame[STREAM_Y:STREAM_Y+STREAM_HEIGHT, STREAM_X:STREAM_X+STREAM_WIDTH]
    
    # Display
    cv2.imshow('Glasses Livestream', stream)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
```

## Key Features Needed
1. **Real-time position adjustment** - Arrow keys to move capture area
2. **Visual guides** - Border/grid to ensure correct positioning  
3. **Configuration persistence** - Save position for next run
4. **Stream output options** - WebSocket, RTMP, file recording
5. **API access** - HTTP endpoints for snapshots and stream

## System Architecture Goals

### Components
1. **Capture Service** - Background process capturing frames
2. **Stream Server** - Distribute frames via WebSocket/HTTP
3. **Processing Pipeline** - Apply AI models, filters, transforms
4. **Storage System** - Record streams, save events

### Use Cases
- AI vision assistant (GPT-4V integration)
- Security monitoring with motion detection
- Live streaming to platforms
- Training data collection

### API Design
```
GET  /stream/live      - WebSocket connection
GET  /stream/snapshot  - Current frame
POST /stream/record    - Start/stop recording  
POST /stream/process   - Apply AI model
GET  /stream/status    - System health
```

## Questions
1. Best approach for reliable iPhone screen capture beyond pyautogui?
2. Optimal frame distribution method for multiple consumers?
3. How to handle stream interruptions/reconnection gracefully?
4. Recommended architecture for real-time AI processing pipeline?

## Installation
```bash
pip install opencv-python pillow pyautogui numpy

# Run basic stream
python stream_now.py
```

The current implementation works but needs to evolve into a proper system for production use.