#!/usr/bin/env python3
"""
Precise iPhone Glasses Stream Extractor
Allows capturing from any screen position including edges
"""

import cv2
import numpy as np
import pyautogui
import time
import json
import os

class PreciseStreamExtractor:
    def __init__(self):
        # Get screen dimensions
        self.screen_width, self.screen_height = pyautogui.size()
        print(f"Screen size: {self.screen_width}x{self.screen_height}")
        
        # Initial position - adjusted for your screenshot
        # The stream appears to be higher up than we thought
        self.x = 40
        self.y = 250  # Moved up from 330
        self.width = 340
        self.height = 260  # Increased to capture full area
        
        # Allow going beyond screen edges for edge content
        self.allow_negative = True
        
        # Visual settings
        self.show_border = True
        self.show_measurements = True
        self.border_thickness = 2
        
        self.load_config()
    
    def load_config(self):
        """Load saved configuration"""
        if os.path.exists('precise_stream_config.json'):
            try:
                with open('precise_stream_config.json', 'r') as f:
                    config = json.load(f)
                    self.x = config.get('x', self.x)
                    self.y = config.get('y', self.y)
                    self.width = config.get('width', self.width)
                    self.height = config.get('height', self.height)
                    print(f"Loaded: x={self.x}, y={self.y}, w={self.width}, h={self.height}")
            except:
                pass
    
    def save_config(self):
        """Save configuration"""
        config = {'x': self.x, 'y': self.y, 'width': self.width, 'height': self.height}
        with open('precise_stream_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Saved: x={self.x}, y={self.y}, w={self.width}, h={self.height}")
    
    def capture_screen(self):
        """Capture the full screen with padding for edge captures"""
        screenshot = pyautogui.screenshot()
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Add padding for captures that go beyond screen edges
        if self.allow_negative:
            # Add black padding around the screen capture
            pad = 500
            padded = np.zeros((frame.shape[0] + pad*2, frame.shape[1] + pad*2, 3), dtype=np.uint8)
            padded[pad:pad+frame.shape[0], pad:pad+frame.shape[1]] = frame
            return padded, pad
        
        return frame, 0
    
    def extract_stream(self, frame, pad):
        """Extract stream region with padding offset"""
        # Adjust coordinates for padding
        x = self.x + pad
        y = self.y + pad
        
        # Ensure we don't go out of bounds
        y1 = max(0, y)
        y2 = min(frame.shape[0], y + self.height)
        x1 = max(0, x)
        x2 = min(frame.shape[1], x + self.width)
        
        # Extract region
        stream = frame[y1:y2, x1:x2]
        
        # If extracted region is smaller than requested, pad it
        if stream.shape[0] < self.height or stream.shape[1] < self.width:
            padded_stream = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            padded_stream[:stream.shape[0], :stream.shape[1]] = stream
            stream = padded_stream
        
        return stream
    
    def draw_overlay(self, stream):
        """Draw overlay with guides"""
        h, w = stream.shape[:2]
        
        if self.show_border:
            # Outer border with color coding
            # Green = good capture, Red = hitting screen edge
            is_at_edge = (self.y <= 0 or self.x <= 0 or 
                         self.y + self.height >= self.screen_height or
                         self.x + self.width >= self.screen_width)
            color = (0, 0, 255) if is_at_edge else (0, 255, 0)
            
            cv2.rectangle(stream, (0, 0), (w-1, h-1), color, self.border_thickness)
            
            # Draw corner brackets
            bracket_size = 30
            bracket_thick = 3
            # Top-left
            cv2.line(stream, (0, 0), (bracket_size, 0), (255, 255, 0), bracket_thick)
            cv2.line(stream, (0, 0), (0, bracket_size), (255, 255, 0), bracket_thick)
            # Top-right
            cv2.line(stream, (w-1, 0), (w-bracket_size, 0), (255, 255, 0), bracket_thick)
            cv2.line(stream, (w-1, 0), (w-1, bracket_size), (255, 255, 0), bracket_thick)
            # Bottom-left
            cv2.line(stream, (0, h-1), (bracket_size, h-1), (255, 255, 0), bracket_thick)
            cv2.line(stream, (0, h-1), (0, h-bracket_size), (255, 255, 0), bracket_thick)
            # Bottom-right
            cv2.line(stream, (w-1, h-1), (w-bracket_size, h-1), (255, 255, 0), bracket_thick)
            cv2.line(stream, (w-1, h-1), (w-1, h-bracket_size), (255, 255, 0), bracket_thick)
        
        if self.show_measurements:
            # Background for text
            overlay = stream.copy()
            cv2.rectangle(overlay, (5, 5), (250, 90), (0, 0, 0), -1)
            stream = cv2.addWeighted(stream, 0.8, overlay, 0.2, 0)
            
            # Position info
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(stream, f"Pos: ({self.x}, {self.y})", (10, 25), font, 0.5, (0, 255, 0), 1)
            cv2.putText(stream, f"Size: {self.width}x{self.height}", (10, 45), font, 0.5, (0, 255, 0), 1)
            cv2.putText(stream, f"Screen: {self.screen_width}x{self.screen_height}", (10, 65), font, 0.5, (0, 255, 0), 1)
            
            # Edge warnings
            if self.y <= 0:
                cv2.putText(stream, "AT TOP EDGE", (10, 85), font, 0.5, (0, 0, 255), 1)
            if self.x <= 0:
                cv2.putText(stream, "AT LEFT EDGE", (10, 85), font, 0.5, (0, 0, 255), 1)
        
        return stream
    
    def run(self):
        """Main loop"""
        print("\n=== Precise Stream Capture ===")
        print("\nControls:")
        print("  Arrow Keys    : Move by 1 pixel")
        print("  WASD         : Move by 5 pixels")
        print("  Shift+Arrow  : Move by 10 pixels")
        print("  +/- or =/]   : Resize")
        print("  0 (zero)     : Try auto-detect stream area")
        print("  R            : Reset position")
        print("  S            : Save configuration")
        print("  M            : Toggle measurements")
        print("  B            : Toggle border")
        print("  Space        : Save snapshot")
        print("  Q            : Quit")
        print(f"\nCurrent: x={self.x}, y={self.y}, {self.width}x{self.height}")
        print("Tip: The stream can now capture from screen edges (y can be 0 or negative)\n")
        
        cv2.namedWindow('Glasses Stream', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Glasses Stream', self.width * 2, self.height * 2)
        
        # For fine adjustment
        fine_step = 1
        normal_step = 5
        large_step = 10
        
        while True:
            # Capture with padding
            frame, pad = self.capture_screen()
            
            # Extract stream
            stream = self.extract_stream(frame, pad)
            
            # Add overlay
            stream = self.draw_overlay(stream)
            
            # Display
            cv2.imshow('Glasses Stream', stream)
            
            # Handle input
            key = cv2.waitKey(1) & 0xFF
            
            # Fine movement (arrow keys - 1 pixel)
            if key == 81:  # Left
                self.x -= fine_step
            elif key == 83:  # Right
                self.x += fine_step
            elif key == 82:  # Up
                self.y -= fine_step
            elif key == 84:  # Down
                self.y += fine_step
            
            # Normal movement (WASD - 5 pixels)
            elif key == ord('a'):
                self.x -= normal_step
            elif key == ord('d'):
                self.x += normal_step
            elif key == ord('w'):
                self.y -= normal_step
            elif key == ord('s'):
                self.y += normal_step
            
            # Large movement (Shift+Arrow would be detected differently)
            elif key == ord('A'):  # Shift+A
                self.x -= large_step
            elif key == ord('D'):  # Shift+D
                self.x += large_step
            elif key == ord('W'):  # Shift+W
                self.y -= large_step
            elif key == ord('S'):  # Shift+S
                self.y += large_step
            
            # Size adjustment
            elif key == ord('+') or key == ord('='):
                self.width += 5
                self.height += 5
            elif key == ord('-'):
                self.width = max(50, self.width - 5)
                self.height = max(50, self.height - 5)
            elif key == ord(']'):
                self.width += 5
            elif key == ord('['):
                self.width = max(50, self.width - 5)
            
            # Other controls
            elif key == ord('0'):  # Auto-detect
                print("Attempting auto-detection...")
                # Try to find the stream area by looking for the rounded rectangle
                gray = cv2.cvtColor(frame[pad:pad+self.screen_height, pad:pad+self.screen_width], cv2.COLOR_BGR2GRAY)
                edges = cv2.Canny(gray, 50, 150)
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # Find rectangular contours around the expected size
                for contour in contours:
                    x, y, w, h = cv2.boundingRect(contour)
                    if 300 < w < 400 and 200 < h < 300:
                        self.x = x
                        self.y = y
                        self.width = w
                        self.height = h
                        print(f"Found potential stream at: {x}, {y}, {w}x{h}")
                        break
                
            elif key == ord('r'):  # Reset
                self.x, self.y = 40, 250
                self.width, self.height = 340, 260
                print("Reset to defaults")
            
            elif key == ord('m'):  # Toggle measurements
                self.show_measurements = not self.show_measurements
            
            elif key == ord('b'):  # Toggle border
                self.show_border = not self.show_border
            
            elif key == ord(' '):  # Save snapshot
                clean_stream = self.extract_stream(frame, pad)
                filename = f"stream_{time.strftime('%Y%m%d_%H%M%S')}.png"
                cv2.imwrite(filename, clean_stream)
                print(f"Saved: {filename}")
            
            elif key == ord('s'):  # Save config
                self.save_config()
            
            elif key == ord('q') or key == 27:  # Quit
                break
            
            # Print position on any movement
            if key in [81, 82, 83, 84, ord('w'), ord('a'), ord('s'), ord('d'), 
                      ord('W'), ord('A'), ord('S'), ord('D')]:
                print(f"Position: x={self.x}, y={self.y}")
        
        cv2.destroyAllWindows()

if __name__ == "__main__":
    extractor = PreciseStreamExtractor()
    extractor.run()