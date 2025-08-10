#!/usr/bin/env python3
"""
Enhanced iPhone Glasses Stream Extractor with Configuration
Visual guides and real-time adjustment controls
"""

import cv2
import numpy as np
import pyautogui
import time
import json
import os

class EnhancedStreamExtractor:
    def __init__(self):
        # Default coordinates (will be updated from saved config if exists)
        self.x = 40
        self.y = 330
        self.width = 340
        self.height = 230
        
        # Adjustment settings
        self.step_size = 5  # pixels to move per arrow key press
        self.show_guides = True
        self.show_crosshair = True
        self.show_info = True
        self.show_border = True
        self.border_color = (0, 255, 0)  # Green border
        
        # Load saved configuration
        self.load_config()
        
    def load_config(self):
        """Load saved configuration if exists"""
        if os.path.exists('stream_config.json'):
            try:
                with open('stream_config.json', 'r') as f:
                    config = json.load(f)
                    self.x = config.get('x', self.x)
                    self.y = config.get('y', self.y)
                    self.width = config.get('width', self.width)
                    self.height = config.get('height', self.height)
                    print(f"Loaded config: x={self.x}, y={self.y}, w={self.width}, h={self.height}")
            except:
                print("Could not load config, using defaults")
    
    def save_config(self):
        """Save current configuration"""
        config = {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height
        }
        with open('stream_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        print("Configuration saved!")
    
    def capture_screen(self):
        """Capture the full screen"""
        screenshot = pyautogui.screenshot()
        frame = np.array(screenshot)
        return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    
    def draw_guides(self, frame):
        """Draw visual guides on the frame"""
        h, w = frame.shape[:2]
        
        if self.show_border:
            # Draw thick border around extracted area
            cv2.rectangle(frame, (0, 0), (w-1, h-1), self.border_color, 3)
            
            # Draw corner markers
            corner_len = 20
            corner_thick = 4
            # Top-left
            cv2.line(frame, (0, 0), (corner_len, 0), (255, 255, 0), corner_thick)
            cv2.line(frame, (0, 0), (0, corner_len), (255, 255, 0), corner_thick)
            # Top-right
            cv2.line(frame, (w-1, 0), (w-corner_len, 0), (255, 255, 0), corner_thick)
            cv2.line(frame, (w-1, 0), (w-1, corner_len), (255, 255, 0), corner_thick)
            # Bottom-left
            cv2.line(frame, (0, h-1), (corner_len, h-1), (255, 255, 0), corner_thick)
            cv2.line(frame, (0, h-1), (0, h-corner_len), (255, 255, 0), corner_thick)
            # Bottom-right
            cv2.line(frame, (w-1, h-1), (w-corner_len, h-1), (255, 255, 0), corner_thick)
            cv2.line(frame, (w-1, h-1), (w-1, h-corner_len), (255, 255, 0), corner_thick)
        
        if self.show_crosshair:
            # Draw center crosshair
            cx, cy = w // 2, h // 2
            cv2.line(frame, (cx - 15, cy), (cx + 15, cy), (0, 255, 255), 1)
            cv2.line(frame, (cx, cy - 15), (cx, cy + 15), (0, 255, 255), 1)
            cv2.circle(frame, (cx, cy), 3, (0, 255, 255), -1)
        
        if self.show_guides:
            # Draw grid lines (rule of thirds)
            for i in range(1, 3):
                # Vertical lines
                x_pos = int(w * i / 3)
                cv2.line(frame, (x_pos, 0), (x_pos, h), (128, 128, 128), 1)
                # Horizontal lines
                y_pos = int(h * i / 3)
                cv2.line(frame, (0, y_pos), (w, y_pos), (128, 128, 128), 1)
        
        return frame
    
    def draw_info(self, frame):
        """Draw information overlay"""
        if not self.show_info:
            return frame
            
        h, w = frame.shape[:2]
        
        # Create semi-transparent overlay for text background
        overlay = frame.copy()
        cv2.rectangle(overlay, (5, 5), (350, 140), (0, 0, 0), -1)
        frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
        
        # Draw text info
        font = cv2.FONT_HERSHEY_SIMPLEX
        color = (0, 255, 0)
        
        info_lines = [
            f"Position: ({self.x}, {self.y})",
            f"Size: {self.width} x {self.height}",
            f"Step: {self.step_size}px",
            "",
            "Controls:",
            "Arrows: Move | +/-: Resize | Tab: Toggle guides",
            "B: Border | G: Grid | I: Info | S: Save | Q: Quit"
        ]
        
        y_offset = 20
        for line in info_lines:
            cv2.putText(frame, line, (10, y_offset), font, 0.4, color, 1)
            y_offset += 18
        
        return frame
    
    def draw_full_screen_overlay(self, screen):
        """Draw overlay on full screen showing capture area"""
        overlay = screen.copy()
        
        # Darken everything except capture area
        mask = np.zeros(screen.shape[:2], dtype=np.uint8)
        cv2.rectangle(mask, (self.x, self.y), 
                     (self.x + self.width, self.y + self.height), 255, -1)
        
        # Apply darkening
        darkened = cv2.addWeighted(screen, 0.3, np.zeros_like(screen), 0.7, 0)
        result = np.where(mask[..., None], screen, darkened)
        
        # Draw capture area border
        cv2.rectangle(result, (self.x, self.y), 
                     (self.x + self.width, self.y + self.height), 
                     (0, 255, 0), 2)
        
        # Draw info at top
        cv2.putText(result, f"Capture Area: ({self.x}, {self.y}) {self.width}x{self.height}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        return result.astype(np.uint8)
    
    def run(self):
        """Main loop"""
        print("\n=== Enhanced Glasses Stream Extractor ===")
        print("\nKeyboard Controls:")
        print("  Arrow Keys : Move capture area")
        print("  Shift+Arrow: Move faster (20px)")
        print("  +/- Keys   : Increase/decrease size")
        print("  [ ]        : Adjust width only")
        print("  { }        : Adjust height only")
        print("  Tab        : Toggle all guides")
        print("  B          : Toggle border")
        print("  G          : Toggle grid")
        print("  C          : Toggle crosshair")
        print("  I          : Toggle info display")
        print("  F          : Show full screen overlay")
        print("  R          : Reset to defaults")
        print("  S          : Save configuration")
        print("  Space      : Save snapshot")
        print("  Q/Esc      : Quit")
        print("\nStarting stream...\n")
        
        # Create windows
        cv2.namedWindow('Glasses Livestream', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Glasses Livestream', self.width * 2, self.height * 2)
        
        full_screen_mode = False
        
        while True:
            # Capture screen
            screen = self.capture_screen()
            
            if full_screen_mode:
                # Show full screen with overlay
                display = self.draw_full_screen_overlay(screen)
                cv2.namedWindow('Full Screen View', cv2.WINDOW_NORMAL)
                cv2.imshow('Full Screen View', display)
            else:
                # Extract stream region
                stream = screen[self.y:self.y+self.height, self.x:self.x+self.width]
                
                # Add visual guides
                stream = self.draw_guides(stream)
                stream = self.draw_info(stream)
                
                # Display
                cv2.imshow('Glasses Livestream', stream)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            
            # Movement controls
            if key == 81:  # Left arrow
                self.x = max(0, self.x - self.step_size)
            elif key == 83:  # Right arrow
                self.x += self.step_size
            elif key == 82:  # Up arrow
                self.y = max(0, self.y - self.step_size)
            elif key == 84:  # Down arrow
                self.y += self.step_size
            
            # Size controls
            elif key == ord('+') or key == ord('='):
                self.width += 10
                self.height += 10
            elif key == ord('-'):
                self.width = max(50, self.width - 10)
                self.height = max(50, self.height - 10)
            elif key == ord('['):
                self.width = max(50, self.width - 10)
            elif key == ord(']'):
                self.width += 10
            elif key == ord('{'):
                self.height = max(50, self.height - 10)
            elif key == ord('}'):
                self.height += 10
            
            # Toggle controls
            elif key == ord('\t'):  # Tab
                self.show_guides = not self.show_guides
                self.show_border = not self.show_border
                self.show_crosshair = not self.show_crosshair
            elif key == ord('b'):
                self.show_border = not self.show_border
            elif key == ord('g'):
                self.show_guides = not self.show_guides
            elif key == ord('c'):
                self.show_crosshair = not self.show_crosshair
            elif key == ord('i'):
                self.show_info = not self.show_info
            elif key == ord('f'):
                full_screen_mode = not full_screen_mode
                if not full_screen_mode:
                    cv2.destroyWindow('Full Screen View')
            
            # Other controls
            elif key == ord('r'):  # Reset
                self.x, self.y = 40, 330
                self.width, self.height = 340, 230
                print("Reset to defaults")
            elif key == ord('s'):  # Save config
                self.save_config()
            elif key == ord(' '):  # Space - snapshot
                if not full_screen_mode:
                    stream = screen[self.y:self.y+self.height, self.x:self.x+self.width]
                    filename = f"stream_{time.strftime('%Y%m%d_%H%M%S')}.png"
                    cv2.imwrite(filename, stream)
                    print(f"Saved snapshot: {filename}")
            elif key == ord('q') or key == 27:  # Q or Esc
                break
        
        cv2.destroyAllWindows()
        print("\nStream closed")

if __name__ == "__main__":
    extractor = EnhancedStreamExtractor()
    extractor.run()