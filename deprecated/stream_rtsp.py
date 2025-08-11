#!/usr/bin/env python3
"""
RTSP Streaming for Glasses Stream
Broadcasts the captured stream via RTSP for network access
"""

import cv2
import numpy as np
import pyautogui
import subprocess
import threading
import time
import socket
from typing import Optional

class RTSPStreamer:
    """Streams captured frames via RTSP using FFmpeg"""
    
    def __init__(self, rtsp_url: str = "rtsp://localhost:8554/stream", 
                 fps: int = 30,
                 width: int = 340,
                 height: int = 230):
        self.rtsp_url = rtsp_url
        self.fps = fps
        self.width = width
        self.height = height
        self.process = None
        self.is_streaming = False
        
        # Stream position (same as unified)
        self.x = 40
        self.y = 330
        
    def start_ffmpeg_process(self):
        """Start FFmpeg process for RTSP streaming"""
        command = [
            'ffmpeg',
            '-y',  # Overwrite output
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-pix_fmt', 'bgr24',
            '-s', f'{self.width}x{self.height}',
            '-r', str(self.fps),
            '-i', '-',  # Input from stdin
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-tune', 'zerolatency',
            '-pix_fmt', 'yuv420p',
            '-rtsp_transport', 'tcp',  # Use TCP instead of UDP
            '-f', 'rtsp',
            self.rtsp_url
        ]
        
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stderr=subprocess.DEVNULL,  # Suppress FFmpeg output
            stdout=subprocess.DEVNULL
        )
        
    def capture_and_stream(self):
        """Capture screen and stream via RTSP"""
        while self.is_streaming:
            try:
                # Capture screen
                screenshot = pyautogui.screenshot()
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Extract stream region
                stream = frame[self.y:self.y+self.height, self.x:self.x+self.width]
                
                # Ensure correct size
                if stream.shape[:2] != (self.height, self.width):
                    stream = cv2.resize(stream, (self.width, self.height))
                
                # Write to FFmpeg stdin
                if self.process and self.process.stdin and self.process.poll() is None:
                    try:
                        self.process.stdin.write(stream.tobytes())
                        self.process.stdin.flush()
                    except BrokenPipeError:
                        print("FFmpeg process ended, restarting...")
                        self.start_ffmpeg_process()
                        time.sleep(1)
                else:
                    print("FFmpeg not running, restarting...")
                    self.start_ffmpeg_process()
                    time.sleep(1)
                    
                # Control frame rate
                time.sleep(1.0 / self.fps)
                    
            except Exception as e:
                print(f"Stream error: {e}")
                time.sleep(0.1)
                
    def start(self):
        """Start RTSP streaming"""
        print(f"Starting RTSP stream at: {self.rtsp_url}")
        self.is_streaming = True
        
        # Start FFmpeg
        self.start_ffmpeg_process()
        
        # Start capture thread
        self.stream_thread = threading.Thread(target=self.capture_and_stream)
        self.stream_thread.daemon = True
        self.stream_thread.start()
        
        print("RTSP stream started!")
        print(f"View with: ffplay {self.rtsp_url}")
        print(f"Or VLC: vlc {self.rtsp_url}")
        
    def stop(self):
        """Stop RTSP streaming"""
        self.is_streaming = False
        
        if self.stream_thread:
            self.stream_thread.join(timeout=2)
            
        if self.process:
            self.process.stdin.close()
            self.process.terminate()
            self.process.wait(timeout=5)
            
        print("RTSP stream stopped")

class SimpleRTSPServer:
    """Simple RTSP server using mediamtx (formerly rtsp-simple-server)"""
    
    @staticmethod
    def start_server():
        """Start mediamtx RTSP server"""
        try:
            # Check if mediamtx is installed
            subprocess.run(['mediamtx', '--version'], capture_output=True)
            
            # Start server
            process = subprocess.Popen(
                ['mediamtx'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            print("RTSP server started on rtsp://localhost:8554")
            return process
            
        except FileNotFoundError:
            print("mediamtx not found. Install with:")
            print("  brew install mediamtx")
            print("Or download from: https://github.com/bluenviron/mediamtx")
            return None

class RTMPStreamer:
    """Alternative: Stream via RTMP (YouTube, Twitch, etc)"""
    
    def __init__(self, rtmp_url: str, stream_key: str = ""):
        self.rtmp_url = rtmp_url + stream_key if stream_key else rtmp_url
        self.width = 340
        self.height = 230
        self.x = 40
        self.y = 330
        
    def stream_to_rtmp(self):
        """Stream directly to RTMP service"""
        command = [
            'ffmpeg',
            '-f', 'avfoundation',
            '-framerate', '30',
            '-i', '1',  # Main display on macOS
            '-vf', f'crop={self.width}:{self.height}:{self.x}:{self.y}',
            '-c:v', 'libx264',
            '-preset', 'veryfast',
            '-maxrate', '3000k',
            '-bufsize', '6000k',
            '-pix_fmt', 'yuv420p',
            '-g', '60',  # Keyframe interval
            '-c:a', 'aac',
            '-b:a', '128k',
            '-ar', '44100',
            '-f', 'flv',
            self.rtmp_url
        ]
        
        print(f"Streaming to: {self.rtmp_url}")
        subprocess.run(command)

def main():
    """Example usage"""
    import sys
    
    print("=== Glasses Stream RTSP/RTMP Broadcaster ===")
    print("\nOptions:")
    print("1. RTSP Local Stream (for VLC, OBS, etc)")
    print("2. RTMP to YouTube/Twitch")
    print("3. Simple HTTP Stream (MJPEG)")
    
    choice = input("\nSelect (1-3): ")
    
    if choice == '1':
        # RTSP streaming
        server = SimpleRTSPServer.start_server()
        
        if server:
            time.sleep(2)  # Let server start
            
            streamer = RTSPStreamer(
                rtsp_url="rtsp://localhost:8554/glasses",
                fps=30
            )
            
            try:
                streamer.start()
                print("\n✅ Stream running!")
                print("\nConnect with:")
                print(f"  VLC: rtsp://localhost:8554/glasses")
                print(f"  OBS: Add Media Source → rtsp://localhost:8554/glasses")
                print(f"  FFplay: ffplay rtsp://localhost:8554/glasses")
                print("\nPress Ctrl+C to stop")
                
                while True:
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                streamer.stop()
                if server:
                    server.terminate()
                    
    elif choice == '2':
        # RTMP streaming
        print("\nRTMP Streaming Setup:")
        print("YouTube: rtmp://a.rtmp.youtube.com/live2/")
        print("Twitch: rtmp://live.twitch.tv/app/")
        
        rtmp_url = input("\nEnter RTMP URL: ")
        stream_key = input("Enter Stream Key: ")
        
        streamer = RTMPStreamer(rtmp_url, stream_key)
        
        try:
            streamer.stream_to_rtmp()
        except KeyboardInterrupt:
            print("\nStream stopped")
            
    elif choice == '3':
        # Simple HTTP MJPEG stream
        print("\nHTTP MJPEG Stream")
        print("Starting on http://localhost:8080/stream")
        
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import io
        
        class StreamHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/stream':
                    self.send_response(200)
                    self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
                    self.end_headers()
                    
                    x, y, w, h = 40, 330, 340, 230
                    
                    try:
                        while True:
                            screenshot = pyautogui.screenshot()
                            frame = np.array(screenshot)
                            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                            stream = frame[y:y+h, x:x+w]
                            
                            _, buffer = cv2.imencode('.jpg', stream)
                            
                            self.send_header('Content-Type', 'image/jpeg')
                            self.send_header('Content-Length', str(len(buffer)))
                            self.end_headers()
                            self.wfile.write(buffer)
                            self.wfile.write(b'--frame\r\n')
                            
                            time.sleep(0.033)  # ~30fps
                            
                    except Exception as e:
                        print(f"Stream error: {e}")
        
        server = HTTPServer(('localhost', 8080), StreamHandler)
        print("HTTP stream started at: http://localhost:8080/stream")
        server.serve_forever()

if __name__ == "__main__":
    main()