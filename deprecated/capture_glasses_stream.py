#!/usr/bin/env python3
"""
iPhone Screen Mirror Livestream Extractor
Captures iPhone screen via QuickTime or system screen recording
and extracts just the glasses livestream view
"""

import cv2
import numpy as np
import subprocess
import time
from PIL import Image
import pyautogui
import os

class GlassesStreamExtractor:
    def __init__(self):
        # Coordinates for the livestream box (adjust based on your screen)
        # These are approximate based on the screenshot
        self.stream_region = {
            'top': 330,     # Adjust based on actual position
            'left': 40,     # Adjust based on actual position  
            'width': 340,   # Width of stream box
            'height': 230   # Height of stream box
        }
        
    def capture_screen(self):
        """Capture the screen using pyautogui"""
        screenshot = pyautogui.screenshot()
        frame = np.array(screenshot)
        # Convert RGB to BGR for OpenCV
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        return frame
    
    def extract_stream_region(self, frame):
        """Extract just the livestream region from the full frame"""
        y1 = self.stream_region['top']
        y2 = y1 + self.stream_region['height']
        x1 = self.stream_region['left']
        x2 = x1 + self.stream_region['width']
        
        stream_frame = frame[y1:y2, x1:x2]
        return stream_frame
    
    def start_stream_window(self):
        """Display only the livestream in a separate window"""
        print("Starting glasses livestream extraction...")
        print("Press 'q' to quit, 's' to save snapshot")
        print("\nMake sure iPhone is mirrored to your Mac screen")
        print("Adjust coordinates in script if stream box is not aligned\n")
        
        cv2.namedWindow('Glasses Livestream', cv2.WINDOW_NORMAL)
        
        while True:
            # Capture full screen
            frame = self.capture_screen()
            
            # Extract stream region
            stream_frame = self.extract_stream_region(frame)
            
            # Display the stream
            cv2.imshow('Glasses Livestream', stream_frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                # Save snapshot
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"glasses_stream_{timestamp}.png"
                cv2.imwrite(filename, stream_frame)
                print(f"Saved snapshot: {filename}")
        
        cv2.destroyAllWindows()
    
    def calibrate_position(self):
        """Interactive calibration to find the correct stream position"""
        print("Calibration Mode - Click and drag to select the livestream area")
        print("Press SPACE when done, ESC to cancel")
        
        # Take a screenshot
        screenshot = pyautogui.screenshot()
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Let user select ROI
        roi = cv2.selectROI("Select Livestream Area", frame, False)
        cv2.destroyWindow("Select Livestream Area")
        
        if roi[2] > 0 and roi[3] > 0:
            self.stream_region = {
                'left': roi[0],
                'top': roi[1],
                'width': roi[2],
                'height': roi[3]
            }
            print(f"\nNew coordinates set:")
            print(f"  Top: {self.stream_region['top']}")
            print(f"  Left: {self.stream_region['left']}")
            print(f"  Width: {self.stream_region['width']}")
            print(f"  Height: {self.stream_region['height']}")
            
            # Save calibration
            self.save_calibration()
            return True
        return False
    
    def save_calibration(self):
        """Save calibration settings"""
        import json
        with open('stream_calibration.json', 'w') as f:
            json.dump(self.stream_region, f, indent=2)
        print("Calibration saved to stream_calibration.json")
    
    def load_calibration(self):
        """Load saved calibration if exists"""
        import json
        try:
            with open('stream_calibration.json', 'r') as f:
                self.stream_region = json.load(f)
                print("Loaded saved calibration")
                return True
        except FileNotFoundError:
            return False

def main():
    extractor = GlassesStreamExtractor()
    
    print("=== Glasses Livestream Extractor ===")
    print("1. Start stream extraction")
    print("2. Calibrate stream position")
    print("3. Exit")
    
    choice = input("\nSelect option (1-3): ")
    
    if choice == '1':
        # Try to load saved calibration
        extractor.load_calibration()
        extractor.start_stream_window()
    elif choice == '2':
        if extractor.calibrate_position():
            print("\nCalibration complete! Starting stream...")
            time.sleep(1)
            extractor.start_stream_window()
    elif choice == '3':
        print("Exiting...")
    else:
        print("Invalid option")

if __name__ == "__main__":
    main()