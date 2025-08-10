#!/usr/bin/env python3
"""
Unified Glasses Stream System
Combines best features from all versions into production-ready system
"""

import cv2
import numpy as np
import pyautogui
import asyncio
import json
import time
import threading
import queue
from dataclasses import dataclass
from typing import Optional, Tuple, Callable
from enum import Enum
import os

class MovementMode(Enum):
    FINE = 1      # 1px precision
    NORMAL = 5    # 5px steps  
    FAST = 10     # 10px jumps
    TURBO = 20    # 20px leaps

class OverlayMode(Enum):
    NONE = 0
    MINIMAL = 1   # Just border
    STANDARD = 2  # Border + info
    FULL = 3      # All guides
    DEBUG = 4     # Everything

@dataclass
class StreamConfig:
    """Configuration for stream capture"""
    x: int = 40
    y: int = 330
    width: int = 340
    height: int = 230
    overlay_mode: OverlayMode = OverlayMode.STANDARD
    movement_mode: MovementMode = MovementMode.NORMAL
    auto_save: bool = True
    config_file: str = "stream_config.json"

class StreamCapture:
    """Core capture engine - handles screen capture and region extraction"""
    
    def __init__(self, config: StreamConfig):
        self.config = config
        self.screen_width, self.screen_height = pyautogui.size()
        self.frame_queue = queue.Queue(maxsize=30)
        self.is_running = False
        self._capture_thread = None
        
    def start(self):
        """Start capture thread"""
        self.is_running = True
        self._capture_thread = threading.Thread(target=self._capture_loop)
        self._capture_thread.daemon = True
        self._capture_thread.start()
        
    def stop(self):
        """Stop capture thread"""
        self.is_running = False
        if self._capture_thread:
            self._capture_thread.join()
            
    def _capture_loop(self):
        """Continuous capture loop"""
        while self.is_running:
            try:
                screenshot = pyautogui.screenshot()
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Extract region
                stream = self._extract_region(frame)
                
                # Add to queue (drop old frames if full)
                if self.frame_queue.full():
                    self.frame_queue.get()
                self.frame_queue.put(stream)
                
            except Exception as e:
                print(f"Capture error: {e}")
                time.sleep(0.1)
                
    def _extract_region(self, frame):
        """Extract stream region with bounds checking"""
        # Handle edge cases and padding
        y1 = max(0, self.config.y)
        y2 = min(frame.shape[0], self.config.y + self.config.height)
        x1 = max(0, self.config.x)
        x2 = min(frame.shape[1], self.config.x + self.config.width)
        
        stream = frame[y1:y2, x1:x2]
        
        # Pad if necessary
        if stream.shape[0] < self.config.height or stream.shape[1] < self.config.width:
            padded = np.zeros((self.config.height, self.config.width, 3), dtype=np.uint8)
            padded[:stream.shape[0], :stream.shape[1]] = stream
            stream = padded
            
        return stream
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get latest frame"""
        try:
            return self.frame_queue.get_nowait()
        except queue.Empty:
            return None

class OverlayRenderer:
    """Handles all visual overlays and UI elements"""
    
    def __init__(self, config: StreamConfig):
        self.config = config
        self.colors = {
            'border_normal': (0, 255, 0),
            'border_edge': (0, 0, 255),
            'grid': (128, 128, 128),
            'crosshair': (0, 255, 255),
            'corner': (255, 255, 0),
            'text': (0, 255, 0)
        }
        
    def render(self, frame: np.ndarray) -> np.ndarray:
        """Apply overlays based on mode"""
        if self.config.overlay_mode == OverlayMode.NONE:
            return frame
            
        frame = frame.copy()
        
        if self.config.overlay_mode.value >= OverlayMode.MINIMAL.value:
            frame = self._draw_border(frame)
            
        if self.config.overlay_mode.value >= OverlayMode.STANDARD.value:
            frame = self._draw_info(frame)
            
        if self.config.overlay_mode.value >= OverlayMode.FULL.value:
            frame = self._draw_guides(frame)
            
        if self.config.overlay_mode == OverlayMode.DEBUG:
            frame = self._draw_debug(frame)
            
        return frame
    
    def _draw_border(self, frame):
        """Draw border with edge detection"""
        h, w = frame.shape[:2]
        screen_w, screen_h = pyautogui.size()
        
        # Check if at edge
        at_edge = (self.config.y <= 0 or self.config.x <= 0 or
                  self.config.y + self.config.height >= screen_h or
                  self.config.x + self.config.width >= screen_w)
        
        color = self.colors['border_edge'] if at_edge else self.colors['border_normal']
        cv2.rectangle(frame, (0, 0), (w-1, h-1), color, 2)
        
        # Corner markers
        corner_size = 20
        corner_thick = 3
        for x, y in [(0, 0), (w-1, 0), (0, h-1), (w-1, h-1)]:
            dx = 1 if x == 0 else -1
            dy = 1 if y == 0 else -1
            cv2.line(frame, (x, y), (x + dx*corner_size, y), self.colors['corner'], corner_thick)
            cv2.line(frame, (x, y), (x, y + dy*corner_size), self.colors['corner'], corner_thick)
            
        return frame
    
    def _draw_info(self, frame):
        """Draw position and control info"""
        # Semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(overlay, (5, 5), (250, 65), (0, 0, 0), -1)
        frame = cv2.addWeighted(frame, 0.8, overlay, 0.2, 0)
        
        # Info text
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, f"Pos: ({self.config.x}, {self.config.y})", 
                   (10, 25), font, 0.5, self.colors['text'], 1)
        cv2.putText(frame, f"Size: {self.config.width}x{self.config.height}", 
                   (10, 45), font, 0.5, self.colors['text'], 1)
        cv2.putText(frame, f"Mode: {self.config.movement_mode.name}", 
                   (10, 60), font, 0.4, self.colors['text'], 1)
        
        return frame
    
    def _draw_guides(self, frame):
        """Draw grid and crosshair"""
        h, w = frame.shape[:2]
        
        # Grid (rule of thirds)
        for i in range(1, 3):
            x = int(w * i / 3)
            y = int(h * i / 3)
            cv2.line(frame, (x, 0), (x, h), self.colors['grid'], 1)
            cv2.line(frame, (0, y), (w, y), self.colors['grid'], 1)
        
        # Crosshair
        cx, cy = w // 2, h // 2
        cv2.line(frame, (cx - 15, cy), (cx + 15, cy), self.colors['crosshair'], 1)
        cv2.line(frame, (cx, cy - 15), (cx, cy + 15), self.colors['crosshair'], 1)
        cv2.circle(frame, (cx, cy), 3, self.colors['crosshair'], -1)
        
        return frame
    
    def _draw_debug(self, frame):
        """Draw debug information"""
        h, w = frame.shape[:2]
        
        # FPS counter placeholder
        cv2.putText(frame, "DEBUG MODE", (w-100, 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
        
        return frame

class MovementController:
    """Handles all movement and positioning logic"""
    
    def __init__(self, config: StreamConfig):
        self.config = config
        self.movement_speeds = {
            MovementMode.FINE: 1,
            MovementMode.NORMAL: 5,
            MovementMode.FAST: 10,
            MovementMode.TURBO: 20
        }
        
    def move(self, dx: int = 0, dy: int = 0, relative: bool = True):
        """Move the capture area"""
        if relative:
            self.config.x += dx * self.movement_speeds[self.config.movement_mode]
            self.config.y += dy * self.movement_speeds[self.config.movement_mode]
        else:
            self.config.x = dx
            self.config.y = dy
            
    def resize(self, dw: int = 0, dh: int = 0):
        """Resize the capture area"""
        self.config.width = max(50, self.config.width + dw)
        self.config.height = max(50, self.config.height + dh)
        
    def reset(self):
        """Reset to defaults"""
        self.config.x = 40
        self.config.y = 330
        self.config.width = 340
        self.config.height = 230
        
    def auto_detect(self, frame: np.ndarray) -> bool:
        """Attempt to auto-detect stream area"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if 300 < w < 400 and 200 < h < 300:
                self.config.x = x
                self.config.y = y
                self.config.width = w
                self.config.height = h
                return True
        return False

class ConfigManager:
    """Handles configuration persistence"""
    
    @staticmethod
    def save(config: StreamConfig):
        """Save configuration to JSON"""
        data = {
            'x': config.x,
            'y': config.y,
            'width': config.width,
            'height': config.height,
            'overlay_mode': config.overlay_mode.value,
            'movement_mode': config.movement_mode.value
        }
        with open(config.config_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    @staticmethod
    def load(config: StreamConfig) -> bool:
        """Load configuration from JSON"""
        if not os.path.exists(config.config_file):
            return False
            
        try:
            with open(config.config_file, 'r') as f:
                data = json.load(f)
                config.x = data.get('x', config.x)
                config.y = data.get('y', config.y)
                config.width = data.get('width', config.width)
                config.height = data.get('height', config.height)
                config.overlay_mode = OverlayMode(data.get('overlay_mode', 2))
                config.movement_mode = MovementMode(data.get('movement_mode', 5))
            return True
        except:
            return False

class UnifiedStreamSystem:
    """Main system orchestrator"""
    
    def __init__(self):
        self.config = StreamConfig()
        self.capture = StreamCapture(self.config)
        self.overlay = OverlayRenderer(self.config)
        self.movement = MovementController(self.config)
        self.config_manager = ConfigManager()
        
        # Load saved config
        if self.config_manager.load(self.config):
            print("Loaded saved configuration")
            
    def run_interactive(self):
        """Run interactive viewer mode"""
        print("\n=== Unified Glasses Stream System ===")
        print("\nMovement Controls:")
        print("  Arrows     : Move (speed based on mode)")
        print("  Tab        : Cycle movement speed")
        print("  +/-        : Resize")
        print("\nOverlay Controls:")
        print("  1-5        : Set overlay mode (1=none, 5=debug)")
        print("  B          : Quick toggle border")
        print("\nOther Controls:")
        print("  C          : Calibrate (click & drag)")
        print("  A          : Auto-detect")
        print("  R          : Reset position")
        print("  S          : Save config")
        print("  Space      : Snapshot")
        print("  Q          : Quit")
        
        # Start capture
        self.capture.start()
        
        # Create window
        cv2.namedWindow('Glasses Stream', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Glasses Stream', self.config.width * 2, self.config.height * 2)
        
        try:
            while True:
                # Get latest frame
                frame = self.capture.get_frame()
                if frame is None:
                    time.sleep(0.01)
                    continue
                
                # Apply overlays
                display = self.overlay.render(frame)
                
                # Show frame
                cv2.imshow('Glasses Stream', display)
                
                # Handle input
                if not self._handle_input():
                    break
                    
        finally:
            self.capture.stop()
            cv2.destroyAllWindows()
            
            if self.config.auto_save:
                self.config_manager.save(self.config)
                print("Configuration saved")
                
    def _handle_input(self) -> bool:
        """Handle keyboard input"""
        key = cv2.waitKey(1) & 0xFF
        
        if key == 0xFF:  # No key
            return True
            
        # Movement
        if key == 81:  # Left
            self.movement.move(dx=-1)
        elif key == 83:  # Right
            self.movement.move(dx=1)
        elif key == 82:  # Up
            self.movement.move(dy=-1)
        elif key == 84:  # Down
            self.movement.move(dy=1)
            
        # Movement speed
        elif key == ord('\t'):
            modes = list(MovementMode)
            idx = (modes.index(self.config.movement_mode) + 1) % len(modes)
            self.config.movement_mode = modes[idx]
            print(f"Movement mode: {self.config.movement_mode.name}")
            
        # Resize
        elif key in [ord('+'), ord('=')]:
            self.movement.resize(dw=10, dh=10)
        elif key == ord('-'):
            self.movement.resize(dw=-10, dh=-10)
            
        # Overlay modes
        elif ord('1') <= key <= ord('5'):
            self.config.overlay_mode = OverlayMode(key - ord('1'))
            print(f"Overlay mode: {self.config.overlay_mode.name}")
            
        # Quick toggles
        elif key == ord('b'):
            if self.config.overlay_mode == OverlayMode.NONE:
                self.config.overlay_mode = OverlayMode.MINIMAL
            else:
                self.config.overlay_mode = OverlayMode.NONE
                
        # Calibration
        elif key == ord('c'):
            self._calibrate()
            
        # Auto-detect
        elif key == ord('a'):
            screenshot = pyautogui.screenshot()
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            if self.movement.auto_detect(frame):
                print(f"Auto-detected at ({self.config.x}, {self.config.y})")
            else:
                print("Auto-detect failed")
                
        # Reset
        elif key == ord('r'):
            self.movement.reset()
            print("Reset to defaults")
            
        # Save
        elif key == ord('s'):
            self.config_manager.save(self.config)
            print("Configuration saved")
            
        # Snapshot
        elif key == ord(' '):
            frame = self.capture.get_frame()
            if frame is not None:
                filename = f"snapshot_{time.strftime('%Y%m%d_%H%M%S')}.png"
                cv2.imwrite(filename, frame)
                print(f"Saved: {filename}")
                
        # Quit
        elif key == ord('q') or key == 27:
            return False
            
        return True
    
    def _calibrate(self):
        """Interactive calibration"""
        print("Calibration mode - Select the livestream area")
        screenshot = pyautogui.screenshot()
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        roi = cv2.selectROI("Select Stream Area", frame, False)
        cv2.destroyWindow("Select Stream Area")
        
        if roi[2] > 0 and roi[3] > 0:
            self.config.x, self.config.y = roi[0], roi[1]
            self.config.width, self.config.height = roi[2], roi[3]
            print(f"Calibrated: ({self.config.x}, {self.config.y}) {self.config.width}x{self.config.height}")

def main():
    """Entry point"""
    system = UnifiedStreamSystem()
    system.run_interactive()

if __name__ == "__main__":
    main()